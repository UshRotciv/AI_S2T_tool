#!/usr/bin/env python3
"""
智能服務管理工具 - 根治連接埠衝突和服務連通性問題
功能：
1. 自動連接埠清理和管理
2. 智能連接埠選擇
3. 服務健康監控和自動重啟
4. AI/RAG 連通性診斷和修復
5. 一鍵啟動和管理
"""

import subprocess
import requests
import json
import time
import socket
import psutil
import sys
import os
import signal
import threading
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import logging

# 設定日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('service_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SmartServiceManager:
    def __init__(self, preferred_port: int = 8001):
        self.preferred_port = preferred_port
        self.backup_ports = [8002, 8003, 8004, 8005, 8006, 8007, 8008]
        self.current_port = None
        self.service_process = None
        self.monitoring_active = False
        self.ai_service_path = os.path.join(os.path.dirname(__file__), 'ai-service')
        self.main_py_path = os.path.join(self.ai_service_path, 'main.py')
        
    def kill_processes_on_port(self, port: int) -> bool:
        """強制終止佔用指定連接埠的所有程序"""
        logger.info(f"🔍 檢查連接埠 {port} 的佔用情況...")
        killed_processes = []
        
        try:
            for conn in psutil.net_connections():
                if conn.laddr.port == port and conn.pid:
                    try:
                        process = psutil.Process(conn.pid)
                        process_info = {
                            'pid': conn.pid,
                            'name': process.name(),
                            'cmdline': ' '.join(process.cmdline())
                        }
                        
                        logger.info(f"🎯 發現佔用程序: {process_info['name']} (PID: {process_info['pid']})")
                        
                        # 嘗試優雅終止
                        process.terminate()
                        try:
                            process.wait(timeout=3)
                            logger.info(f"✅ 優雅終止程序 {process_info['pid']}")
                        except psutil.TimeoutExpired:
                            # 強制終止
                            process.kill()
                            logger.info(f"💥 強制終止程序 {process_info['pid']}")
                        
                        killed_processes.append(process_info)
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                        logger.warning(f"⚠️ 無法終止程序 {conn.pid}: {e}")
                        
        except Exception as e:
            logger.error(f"❌ 檢查連接埠時發生錯誤: {e}")
            return False
        
        if killed_processes:
            logger.info(f"🧹 已清理 {len(killed_processes)} 個佔用連接埠 {port} 的程序")
            time.sleep(2)  # 等待程序完全終止
            return True
        else:
            logger.info(f"✨ 連接埠 {port} 沒有被佔用")
            return True
    
    def find_available_port(self) -> Optional[int]:
        """智能尋找可用連接埠"""
        all_ports = [self.preferred_port] + self.backup_ports
        
        for port in all_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('localhost', port))
                    logger.info(f"✅ 找到可用連接埠: {port}")
                    return port
            except OSError:
                logger.info(f"❌ 連接埠 {port} 被佔用")
                continue
        
        logger.error("❌ 沒有找到可用的連接埠")
        return None
    
    def update_port_in_main_py(self, new_port: int) -> bool:
        """更新 main.py 中的連接埠設定"""
        try:
            if not os.path.exists(self.main_py_path):
                logger.error(f"❌ 找不到 main.py: {self.main_py_path}")
                return False
            
            with open(self.main_py_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 尋找並替換 uvicorn.run 中的 port 參數
            import re
            pattern = r'uvicorn\.run\(app,\s*host="[^"]*",\s*port=\d+\)'
            replacement = f'uvicorn.run(app, host="0.0.0.0", port={new_port})'
            
            if re.search(pattern, content):
                new_content = re.sub(pattern, replacement, content)
                with open(self.main_py_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.info(f"✅ 已更新 main.py 中的連接埠為 {new_port}")
                return True
            else:
                logger.warning("⚠️ 在 main.py 中找不到 uvicorn.run 設定")
                return False
                
        except Exception as e:
            logger.error(f"❌ 更新 main.py 時發生錯誤: {e}")
            return False
    
    def check_dependencies(self) -> Dict[str, bool]:
        """檢查服務依賴"""
        dependencies = {
            'ollama': False,
            'chromadb': False,
            'python_packages': False
        }
        
        # 檢查 Ollama
        try:
            result = subprocess.run(['ollama', 'list'], capture_output=True, text=True, timeout=10)
            dependencies['ollama'] = result.returncode == 0
            if dependencies['ollama']:
                logger.info("✅ Ollama 服務正常")
            else:
                logger.warning("⚠️ Ollama 服務異常")
        except Exception as e:
            logger.warning(f"⚠️ Ollama 檢查失敗: {e}")
        
        # 檢查 Python 套件
        try:
            import chromadb
            import fastapi
            import uvicorn
            dependencies['python_packages'] = True
            logger.info("✅ Python 套件完整")
        except ImportError as e:
            logger.error(f"❌ 缺少 Python 套件: {e}")
        
        # 檢查 ChromaDB
        try:
            db_path = os.path.join(self.ai_service_path, 'chroma_db')
            if os.path.exists(db_path):
                dependencies['chromadb'] = True
                logger.info("✅ ChromaDB 資料庫存在")
            else:
                logger.warning("⚠️ ChromaDB 資料庫不存在")
        except Exception as e:
            logger.error(f"❌ ChromaDB 檢查失敗: {e}")
        
        return dependencies
    
    def start_service(self, port: int) -> bool:
        """啟動 FastAPI 服務"""
        try:
            # 更新連接埠設定
            if not self.update_port_in_main_py(port):
                return False
            
            # 啟動服務
            logger.info(f"🚀 啟動 FastAPI 服務在連接埠 {port}...")
            
            cmd = [sys.executable, 'main.py']
            self.service_process = subprocess.Popen(
                cmd,
                cwd=self.ai_service_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 等待服務啟動
            time.sleep(5)
            
            # 檢查服務是否正常啟動
            if self.service_process.poll() is None:
                self.current_port = port
                logger.info(f"✅ FastAPI 服務已啟動 (PID: {self.service_process.pid})")
                return True
            else:
                stdout, stderr = self.service_process.communicate()
                logger.error(f"❌ FastAPI 服務啟動失敗")
                logger.error(f"STDOUT: {stdout}")
                logger.error(f"STDERR: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ 啟動服務時發生錯誤: {e}")
            return False
    
    def test_service_health(self, port: int) -> Dict[str, Any]:
        """測試服務健康狀態"""
        base_url = f"http://localhost:{port}"
        health_status = {
            'port': port,
            'service_running': False,
            'endpoints': {},
            'ai_rag_connected': False
        }
        
        # 測試基本端點
        endpoints = [
            ('/api/status', 'GET'),
            ('/docs', 'GET')
        ]
        
        for endpoint, method in endpoints:
            try:
                url = f"{base_url}{endpoint}"
                response = requests.get(url, timeout=5)
                health_status['endpoints'][endpoint] = {
                    'status_code': response.status_code,
                    'success': response.status_code == 200
                }
                if response.status_code == 200:
                    health_status['service_running'] = True
            except Exception as e:
                health_status['endpoints'][endpoint] = {
                    'error': str(e),
                    'success': False
                }
        
        # 測試 AI/RAG 連通性
        if health_status['service_running']:
            try:
                test_data = {
                    "question": "測試 AI 和 RAG 連通性",
                    "session_id": "health_check"
                }
                response = requests.post(f"{base_url}/api/ask", json=test_data, timeout=15)
                if response.status_code == 200:
                    result = response.json()
                    if 'answer' in result and result['answer']:
                        health_status['ai_rag_connected'] = True
                        logger.info("✅ AI/RAG 連通性正常")
                    else:
                        logger.warning("⚠️ AI/RAG 回應異常")
                else:
                    logger.warning(f"⚠️ AI/RAG 測試失敗，狀態碼: {response.status_code}")
            except Exception as e:
                logger.error(f"❌ AI/RAG 連通性測試失敗: {e}")
        
        return health_status
    
    def stop_service(self):
        """停止服務"""
        if self.service_process:
            try:
                self.service_process.terminate()
                self.service_process.wait(timeout=5)
                logger.info("✅ 服務已停止")
            except subprocess.TimeoutExpired:
                self.service_process.kill()
                logger.info("💥 強制終止服務")
            except Exception as e:
                logger.error(f"❌ 停止服務時發生錯誤: {e}")
            finally:
                self.service_process = None
                self.current_port = None
    
    def monitor_service(self):
        """監控服務狀態"""
        while self.monitoring_active and self.current_port:
            try:
                health = self.test_service_health(self.current_port)
                if not health['service_running']:
                    logger.warning("⚠️ 服務異常，嘗試重啟...")
                    self.restart_service()
                elif not health['ai_rag_connected']:
                    logger.warning("⚠️ AI/RAG 連通性異常")
                
                time.sleep(30)  # 每30秒檢查一次
                
            except Exception as e:
                logger.error(f"❌ 監控過程中發生錯誤: {e}")
                time.sleep(10)
    
    def restart_service(self) -> bool:
        """重啟服務"""
        logger.info("🔄 重啟服務...")
        self.stop_service()
        time.sleep(2)
        return self.start_smart_service()
    
    def start_smart_service(self) -> bool:
        """智能啟動服務"""
        logger.info("🧠 開始智能服務啟動流程...")
        
        # 1. 檢查依賴
        logger.info("📋 檢查服務依賴...")
        dependencies = self.check_dependencies()
        if not all(dependencies.values()):
            logger.error("❌ 服務依賴不完整，請檢查:")
            for dep, status in dependencies.items():
                if not status:
                    logger.error(f"  - {dep}: 異常")
            return False
        
        # 2. 清理舊的連接埠佔用
        logger.info("🧹 清理連接埠佔用...")
        self.kill_processes_on_port(self.preferred_port)
        for port in self.backup_ports:
            self.kill_processes_on_port(port)
        
        # 3. 尋找可用連接埠
        available_port = self.find_available_port()
        if not available_port:
            logger.error("❌ 沒有可用的連接埠")
            return False
        
        # 4. 啟動服務
        if self.start_service(available_port):
            # 5. 測試服務健康狀態
            time.sleep(3)
            health = self.test_service_health(available_port)
            
            if health['service_running']:
                logger.info(f"🎉 服務啟動成功！連接埠: {available_port}")
                
                if health['ai_rag_connected']:
                    logger.info("🤖 AI/RAG 連通性正常")
                else:
                    logger.warning("⚠️ AI/RAG 連通性異常，但服務已啟動")
                
                # 6. 開始監控
                self.monitoring_active = True
                monitor_thread = threading.Thread(target=self.monitor_service, daemon=True)
                monitor_thread.start()
                
                return True
            else:
                logger.error("❌ 服務啟動失敗")
                return False
        else:
            return False
    
    def generate_startup_script(self):
        """生成一鍵啟動腳本"""
        script_content = f'''@echo off
chcp 65001 > nul
echo ================================================
echo  智能 AI 服務啟動器
echo ================================================
echo.

cd /d "{os.path.dirname(__file__)}"
python smart_service_manager.py --start

pause
'''
        
        script_path = os.path.join(os.path.dirname(__file__), 'start_ai_service.bat')
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        logger.info(f"📝 已生成一鍵啟動腳本: {script_path}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='智能服務管理工具')
    parser.add_argument('--start', action='store_true', help='啟動服務')
    parser.add_argument('--stop', action='store_true', help='停止服務')
    parser.add_argument('--restart', action='store_true', help='重啟服務')
    parser.add_argument('--status', action='store_true', help='檢查狀態')
    parser.add_argument('--port', type=int, default=8001, help='偏好連接埠')
    
    args = parser.parse_args()
    
    manager = SmartServiceManager(preferred_port=args.port)
    
    if args.start:
        success = manager.start_smart_service()
        if success:
            print(f"\n🎉 服務已成功啟動在連接埠 {manager.current_port}")
            print(f"📖 API 文檔: http://localhost:{manager.current_port}/docs")
            print(f"🔍 服務狀態: http://localhost:{manager.current_port}/api/status")
            print("\n按 Ctrl+C 停止服務...")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 正在停止服務...")
                manager.monitoring_active = False
                manager.stop_service()
                print("✅ 服務已停止")
        else:
            print("❌ 服務啟動失敗")
            sys.exit(1)
    
    elif args.stop:
        manager.stop_service()
        print("✅ 服務已停止")
    
    elif args.restart:
        if manager.restart_service():
            print("✅ 服務重啟成功")
        else:
            print("❌ 服務重啟失敗")
    
    elif args.status:
        if manager.current_port:
            health = manager.test_service_health(manager.current_port)
            print(f"服務狀態: {'運行中' if health['service_running'] else '未運行'}")
            print(f"AI/RAG 連通性: {'正常' if health['ai_rag_connected'] else '異常'}")
        else:
            print("服務未運行")
    
    else:
        # 生成啟動腳本
        manager.generate_startup_script()
        print("使用方法:")
        print("  python smart_service_manager.py --start    # 啟動服務")
        print("  python smart_service_manager.py --stop     # 停止服務")
        print("  python smart_service_manager.py --restart  # 重啟服務")
        print("  python smart_service_manager.py --status   # 檢查狀態")
        print("\n或者直接執行 start_ai_service.bat 一鍵啟動")

if __name__ == "__main__":
    main()

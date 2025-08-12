#!/usr/bin/env python3
"""
FastAPI 服務自動化診斷工具
功能：
1. 連接埠使用狀況檢查
2. 服務健康狀態測試
3. 錯誤診斷和報告
4. 自動修復建議
"""

import subprocess
import requests
import json
import time
import socket
import psutil
import sys
from typing import Dict, List, Tuple, Optional
from datetime import datetime

class FastAPIServiceDiagnostic:
    def __init__(self, target_port: int = 8001, backup_ports: List[int] = None):
        self.target_port = target_port
        self.backup_ports = backup_ports or [8002, 8003, 8004, 8005]
        self.base_url = f"http://localhost:{target_port}"
        self.test_results = {}
        
    def check_port_usage(self, port: int) -> Dict:
        """檢查指定連接埠的使用狀況"""
        result = {
            "port": port,
            "is_available": False,
            "process_info": None,
            "error": None
        }
        
        try:
            # 嘗試綁定連接埠
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                result["is_available"] = True
        except OSError as e:
            result["error"] = str(e)
            
            # 查找佔用連接埠的程序
            try:
                for conn in psutil.net_connections():
                    if conn.laddr.port == port:
                        try:
                            process = psutil.Process(conn.pid)
                            result["process_info"] = {
                                "pid": conn.pid,
                                "name": process.name(),
                                "cmdline": " ".join(process.cmdline()),
                                "status": process.status()
                            }
                            break
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
            except Exception as e:
                result["error"] += f" | Process lookup error: {str(e)}"
                
        return result
    
    def find_available_port(self) -> Optional[int]:
        """尋找可用的連接埠"""
        all_ports = [self.target_port] + self.backup_ports
        
        for port in all_ports:
            port_info = self.check_port_usage(port)
            if port_info["is_available"]:
                return port
        return None
    
    def test_service_health(self, port: int = None) -> Dict:
        """測試 FastAPI 服務健康狀態"""
        test_port = port or self.target_port
        base_url = f"http://localhost:{test_port}"
        
        result = {
            "port": test_port,
            "service_running": False,
            "endpoints_tested": {},
            "response_times": {},
            "errors": []
        }
        
        # 測試端點列表
        endpoints = [
            ("/api/status", "GET"),
            ("/api/ask", "POST"),
            ("/docs", "GET"),  # FastAPI 自動文檔
        ]
        
        for endpoint, method in endpoints:
            url = f"{base_url}{endpoint}"
            start_time = time.time()
            
            try:
                if method == "GET":
                    response = requests.get(url, timeout=5)
                elif method == "POST":
                    test_data = {"question": "測試問題", "session_id": "test"}
                    response = requests.post(url, json=test_data, timeout=10)
                
                response_time = time.time() - start_time
                result["response_times"][endpoint] = response_time
                
                result["endpoints_tested"][endpoint] = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response_time,
                    "content_length": len(response.content)
                }
                
                if response.status_code == 200:
                    result["service_running"] = True
                    
            except requests.exceptions.RequestException as e:
                result["endpoints_tested"][endpoint] = {
                    "error": str(e),
                    "success": False
                }
                result["errors"].append(f"{endpoint}: {str(e)}")
        
        return result
    
    def diagnose_startup_issues(self) -> Dict:
        """診斷服務啟動問題"""
        diagnosis = {
            "timestamp": datetime.now().isoformat(),
            "port_analysis": {},
            "service_health": {},
            "recommendations": [],
            "severity": "INFO"
        }
        
        # 1. 檢查目標連接埠
        port_info = self.check_port_usage(self.target_port)
        diagnosis["port_analysis"] = port_info
        
        if not port_info["is_available"]:
            diagnosis["severity"] = "ERROR"
            if port_info["process_info"]:
                proc_info = port_info["process_info"]
                diagnosis["recommendations"].append(
                    f"連接埠 {self.target_port} 被程序佔用: {proc_info['name']} (PID: {proc_info['pid']})"
                )
                diagnosis["recommendations"].append(
                    f"建議執行: taskkill /PID {proc_info['pid']} /F"
                )
            else:
                diagnosis["recommendations"].append(
                    f"連接埠 {self.target_port} 被未知程序佔用，建議重啟系統或使用其他連接埠"
                )
        
        # 2. 尋找可用連接埠
        available_port = self.find_available_port()
        if available_port and available_port != self.target_port:
            diagnosis["recommendations"].append(
                f"建議使用可用連接埠: {available_port}"
            )
        
        # 3. 測試服務健康狀態
        if port_info["is_available"]:
            diagnosis["service_health"] = self.test_service_health(self.target_port)
        elif available_port:
            diagnosis["service_health"] = self.test_service_health(available_port)
        
        # 4. 生成修復建議
        if diagnosis["severity"] == "ERROR":
            diagnosis["recommendations"].append(
                "自動修復步驟："
            )
            diagnosis["recommendations"].append(
                "1. 停止佔用連接埠的程序"
            )
            diagnosis["recommendations"].append(
                "2. 或修改 FastAPI 配置使用其他連接埠"
            )
            diagnosis["recommendations"].append(
                "3. 重新啟動 FastAPI 服務"
            )
        
        return diagnosis
    
    def generate_port_fix_script(self, new_port: int) -> str:
        """生成連接埠修復腳本"""
        script_content = f"""#!/usr/bin/env python3
# 自動生成的連接埠修復腳本
# 生成時間: {datetime.now().isoformat()}

import os
import re

def update_port_in_file(file_path, old_port, new_port):
    \"\"\"更新檔案中的連接埠設定\"\"\"
    if not os.path.exists(file_path):
        print(f"檔案不存在: {{file_path}}")
        return False
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替換連接埠設定
        patterns = [
            rf'port={old_port}',
            rf':{old_port}',
            rf'localhost:{old_port}',
            rf'127\.0\.0\.1:{old_port}'
        ]
        
        updated = False
        for pattern in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, pattern.replace(str(old_port), str(new_port)), content)
                updated = True
        
        if updated:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已更新 {{file_path}}")
            return True
        else:
            print(f"{{file_path}} 中未找到連接埠 {{old_port}} 的設定")
            return False
            
    except Exception as e:
        print(f"更新 {{file_path}} 時發生錯誤: {{e}}")
        return False

# 需要更新的檔案列表
files_to_update = [
    'ai-service/main.py',
    'test_api_chain.py',
    'start_services_step_by_step.bat',
    'start-all.bat'
]

print(f"正在將連接埠從 {self.target_port} 更新為 {new_port}...")

for file_path in files_to_update:
    update_port_in_file(file_path, {self.target_port}, {new_port})

print("連接埠更新完成！")
"""
        return script_content
    
    def run_comprehensive_test(self) -> Dict:
        """執行完整的診斷測試"""
        print("🔍 開始 FastAPI 服務完整診斷...")
        print("=" * 60)
        
        # 執行診斷
        diagnosis = self.diagnose_startup_issues()
        
        # 輸出結果
        print(f"\n📊 診斷報告 ({diagnosis['timestamp']})")
        print("-" * 40)
        
        # 連接埠狀態
        port_info = diagnosis["port_analysis"]
        print(f"\n🔌 連接埠 {port_info['port']} 狀態:")
        if port_info["is_available"]:
            print("  ✅ 可用")
        else:
            print("  ❌ 被佔用")
            if port_info["process_info"]:
                proc = port_info["process_info"]
                print(f"  📋 佔用程序: {proc['name']} (PID: {proc['pid']})")
                print(f"  📋 命令行: {proc['cmdline']}")
        
        # 服務健康狀態
        if "service_health" in diagnosis and diagnosis["service_health"]:
            health = diagnosis["service_health"]
            print(f"\n🏥 服務健康檢查 (連接埠 {health['port']}):")
            print(f"  服務運行: {'✅' if health['service_running'] else '❌'}")
            
            for endpoint, result in health["endpoints_tested"].items():
                if "error" in result:
                    print(f"  {endpoint}: ❌ {result['error']}")
                else:
                    status = "✅" if result["success"] else "❌"
                    print(f"  {endpoint}: {status} (狀態碼: {result['status_code']}, 響應時間: {result.get('response_time', 0):.2f}s)")
        
        # 建議
        print(f"\n💡 建議 (嚴重程度: {diagnosis['severity']}):")
        for i, recommendation in enumerate(diagnosis["recommendations"], 1):
            print(f"  {i}. {recommendation}")
        
        # 尋找可用連接埠
        available_port = self.find_available_port()
        if available_port and available_port != self.target_port:
            print(f"\n🔄 可用連接埠: {available_port}")
            
            # 生成修復腳本
            fix_script = self.generate_port_fix_script(available_port)
            script_path = "port_fix_script.py"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(fix_script)
            print(f"  📝 已生成修復腳本: {script_path}")
        
        print("\n" + "=" * 60)
        print("診斷完成！")
        
        return diagnosis

def main():
    """主函數"""
    diagnostic = FastAPIServiceDiagnostic(target_port=8001)
    result = diagnostic.run_comprehensive_test()
    
    # 保存診斷結果
    with open('diagnostic_report.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n📄 詳細報告已保存至: diagnostic_report.json")
    
    return result

if __name__ == "__main__":
    main()

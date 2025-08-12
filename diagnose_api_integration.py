#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API 串接診斷工具
診斷 SQLite 版本的 App Server 與 AI Service 之間的 API 串接問題
"""

import requests
import json
import time
import sys
from datetime import datetime

def log_message(message):
    """記錄帶時間戳的訊息"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def test_ai_service_direct():
    """直接測試 AI Service"""
    log_message("=== 直接測試 AI Service ===")
    
    try:
        # 測試健康檢查
        health_response = requests.get("http://localhost:8001/health", timeout=5)
        log_message(f"AI Service 健康檢查狀態: {health_response.status_code}")
        if health_response.status_code == 200:
            log_message(f"健康檢查回應: {health_response.text}")
        
        # 測試 /ask 端點
        test_question = {"question": "什麼是資安？"}
        ask_response = requests.post("http://localhost:8001/ask", 
                                   json=test_question, 
                                   timeout=10)
        
        log_message(f"AI Service /ask 狀態碼: {ask_response.status_code}")
        log_message(f"AI Service /ask 回應標頭: {dict(ask_response.headers)}")
        
        if ask_response.status_code == 200:
            response_data = ask_response.json()
            log_message(f"AI Service 回應結構: {list(response_data.keys())}")
            log_message(f"AI Service 完整回應: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            # 檢查回應格式
            if 'answer' in response_data:
                log_message(f"✅ AI Service 回應包含 'answer' 字段")
                log_message(f"答案內容: {response_data['answer']}")
            else:
                log_message(f"❌ AI Service 回應缺少 'answer' 字段")
                
        else:
            log_message(f"❌ AI Service /ask 請求失敗: {ask_response.text}")
            
    except Exception as e:
        log_message(f"❌ 直接測試 AI Service 失敗: {str(e)}")

def test_app_server_proxy():
    """測試 App Server 代理功能"""
    log_message("=== 測試 App Server 代理功能 ===")
    
    try:
        # 測試 App Server 健康狀態
        app_health = requests.get("http://localhost:3001/", timeout=5)
        log_message(f"App Server 狀態: {app_health.status_code}")
        
        # 測試代理 /api/ask
        test_question = {"question": "什麼是資安？"}
        proxy_response = requests.post("http://localhost:3001/api/ask", 
                                     json=test_question, 
                                     timeout=10)
        
        log_message(f"App Server 代理狀態碼: {proxy_response.status_code}")
        log_message(f"App Server 代理回應標頭: {dict(proxy_response.headers)}")
        
        if proxy_response.status_code == 200:
            response_data = proxy_response.json()
            log_message(f"App Server 代理回應結構: {list(response_data.keys())}")
            log_message(f"App Server 代理完整回應: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            
            # 檢查前端期望的格式
            if 'answer' in response_data:
                log_message(f"✅ App Server 代理回應包含 'answer' 字段（前端期望格式）")
                log_message(f"前端將顯示: {response_data['answer']}")
            else:
                log_message(f"❌ App Server 代理回應缺少 'answer' 字段（前端期望格式）")
                
        else:
            log_message(f"❌ App Server 代理請求失敗: {proxy_response.text}")
            
    except Exception as e:
        log_message(f"❌ 測試 App Server 代理失敗: {str(e)}")

def compare_responses():
    """比較直接調用 AI Service 和通過 App Server 代理的回應"""
    log_message("=== 比較回應格式 ===")
    
    test_question = {"question": "測試問題"}
    
    try:
        # 直接調用 AI Service
        direct_response = requests.post("http://localhost:8001/ask", 
                                      json=test_question, 
                                      timeout=10)
        
        # 通過 App Server 代理
        proxy_response = requests.post("http://localhost:3001/api/ask", 
                                     json=test_question, 
                                     timeout=10)
        
        if direct_response.status_code == 200 and proxy_response.status_code == 200:
            direct_data = direct_response.json()
            proxy_data = proxy_response.json()
            
            log_message("直接調用 AI Service 回應:")
            log_message(json.dumps(direct_data, ensure_ascii=False, indent=2))
            
            log_message("通過 App Server 代理回應:")
            log_message(json.dumps(proxy_data, ensure_ascii=False, indent=2))
            
            # 比較結構
            if direct_data == proxy_data:
                log_message("✅ 直接調用和代理回應完全一致")
            else:
                log_message("❌ 直接調用和代理回應不一致")
                log_message(f"差異: 直接調用鍵 {set(direct_data.keys())} vs 代理鍵 {set(proxy_data.keys())}")
                
        else:
            log_message(f"❌ 無法比較回應 - 直接調用狀態: {direct_response.status_code}, 代理狀態: {proxy_response.status_code}")
            
    except Exception as e:
        log_message(f"❌ 比較回應失敗: {str(e)}")

def check_frontend_compatibility():
    """檢查前端兼容性"""
    log_message("=== 檢查前端兼容性 ===")
    
    try:
        # 模擬前端請求
        test_question = {"question": "什麼是資安？"}
        response = requests.post("http://localhost:3001/api/ask", 
                               json=test_question, 
                               timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # 檢查前端期望的字段
            if 'answer' in data:
                log_message(f"✅ 前端可以正常獲取答案: response.data.answer = '{data['answer']}'")
                
                # 檢查是否為錯誤訊息
                if "系統處理您的問題時遇到了技術問題" in data['answer']:
                    log_message(f"⚠️ AI Service 返回錯誤訊息，需要進一步診斷 AI Service 內部問題")
                elif "Sorry, something went wrong" in data['answer']:
                    log_message(f"⚠️ 前端顯示通用錯誤訊息，可能是 API 調用失敗")
                else:
                    log_message(f"✅ AI Service 返回正常答案")
                    
            else:
                log_message(f"❌ 前端無法獲取答案，response.data 結構: {list(data.keys())}")
                
        else:
            log_message(f"❌ API 調用失敗，前端將顯示 'Sorry, something went wrong.'")
            
    except Exception as e:
        log_message(f"❌ 前端兼容性檢查失敗: {str(e)}")

def main():
    """主函數"""
    log_message("開始 API 串接診斷")
    log_message("=" * 60)
    
    # 檢查服務是否運行
    services = [
        ("AI Service", "http://localhost:8001/health"),
        ("App Server", "http://localhost:3001/")
    ]
    
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=3)
            log_message(f"✅ {service_name} 運行中 (狀態碼: {response.status_code})")
        except:
            log_message(f"❌ {service_name} 未運行或無法訪問")
            return
    
    log_message("")
    
    # 執行診斷測試
    test_ai_service_direct()
    log_message("")
    
    test_app_server_proxy()
    log_message("")
    
    compare_responses()
    log_message("")
    
    check_frontend_compatibility()
    log_message("")
    
    log_message("=" * 60)
    log_message("API 串接診斷完成")

if __name__ == "__main__":
    main()

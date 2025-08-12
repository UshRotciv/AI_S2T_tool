#!/usr/bin/env python3
"""
測試真實情境問題 - 會議白板拍照處理
"""
import requests
import json

def test_real_scenario():
    print("=== 測試真實情境問題 ===")
    
    # 用戶提供的真實問題
    question = "會議結束後，為了方便記錄，我用自己的手機拍下白板上的會議內容，並上傳到自己的Teams聊天室。這樣做是否合規？"
    
    try:
        print(f"問題: {question}")
        print("發送請求...")
        
        response = requests.post(
            'http://localhost:5000/api/ask',
            json={
                'question': question,
                'session_id': 'real_test'
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get('answer', '無回答')
            sources = data.get('sources', [])
            
            print(f"\n✅ API 回應成功")
            print(f"回答長度: {len(answer)} 字")
            print(f"來源數量: {len(sources)} 筆")
            
            if sources:
                print("\n📚 來源資料:")
                for i, source in enumerate(sources[:3], 1):
                    title = source.get('title', '無標題')
                    category = source.get('category', '無類別')
                    print(f"  {i}. [{category}] {title}")
            
            print(f"\n💬 回答內容:")
            print(answer[:200] + "..." if len(answer) > 200 else answer)
            
            # 檢查是否真的找到相關內容
            if "白板" in answer or "拍照" in answer or "Teams" in answer:
                print("\n✅ 回答包含相關關鍵詞")
            else:
                print("\n❌ 回答似乎不相關")
                
        else:
            print(f"❌ API 錯誤: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

if __name__ == "__main__":
    test_real_scenario()

#!/usr/bin/env python3
import sqlite3
import os

# 設定資料庫路徑
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DB_PATH = os.path.join(SCRIPT_DIR, 'ai-service', 'logs.db')

def check_qa_logs():
    """檢查問答日誌記錄"""
    try:
        if not os.path.exists(LOG_DB_PATH):
            print(f"❌ 資料庫檔案不存在: {LOG_DB_PATH}")
            return
        
        conn = sqlite3.connect(LOG_DB_PATH)
        cursor = conn.cursor()
        
        # 檢查資料表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='qa_log';")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print("❌ qa_log 資料表不存在")
            conn.close()
            return
        
        # 查詢最近的記錄
        cursor.execute("SELECT COUNT(*) FROM qa_log;")
        total_count = cursor.fetchone()[0]
        print(f"📊 總記錄數: {total_count}")
        
        if total_count > 0:
            cursor.execute("""
                SELECT id, session_id, question, answer, timestamp 
                FROM qa_log 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            records = cursor.fetchall()
            
            print("\n📝 最近的問答記錄:")
            print("-" * 80)
            for record in records:
                id, session_id, question, answer, timestamp = record
                print(f"ID: {id}")
                print(f"Session: {session_id}")
                print(f"時間: {timestamp}")
                print(f"問題: {question[:100]}..." if len(question) > 100 else f"問題: {question}")
                print(f"回答: {answer[:100]}..." if len(answer) > 100 else f"回答: {answer}")
                print("-" * 80)
        else:
            print("📝 目前沒有任何問答記錄")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 檢查日誌時發生錯誤: {e}")

if __name__ == "__main__":
    check_qa_logs()

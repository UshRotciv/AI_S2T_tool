import os
import shutil
import stat

def handle_remove_readonly(func, path, exc_info):
    """
    Error handler for shutil.rmtree.
    If the error is due to an access error (read only file) it attempts to 
    change the file permissions and then retries the move.
    """
    exc_type, exc_value, _ = exc_info
    if exc_type is PermissionError:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    else:
        raise

def clean_database(db_path="chroma_db"):
    """清除並重置向量資料庫"""
    if os.path.exists(db_path):
        print(f"移除舊的數據庫: {db_path}")
        try:
            shutil.rmtree(db_path, onerror=handle_remove_readonly)
            print("成功移除舊數據庫")
            return True
        except Exception as e:
            print(f"移除數據庫時出錯: {str(e)}")
            return False
    else:
        print(f"數據庫目錄不存在: {db_path}")
        return True

if __name__ == "__main__":
    clean_database()

import ollama
import sys

def test_embedding(model_name):
    try:
        print(f"測試 {model_name} 模型的嵌入功能...")
        response = ollama.embeddings(
            model=model_name,
            prompt="印表機發現無人拿走的機密文件"
        )
        
        if "embedding" in response:
            print(f"嵌入向量維度: {len(response['embedding'])}")
            print(f"嵌入向量前5個值: {response['embedding'][:5]}")
            print(f"嵌入向量後5個值: {response['embedding'][-5:]}")
            return True
        else:
            print(f"錯誤: 嵌入響應中沒有 embedding 字段")
            print(f"完整響應: {response}")
            return False
    except Exception as e:
        print(f"錯誤: {str(e)}")
        return False

if __name__ == "__main__":
    model = "mxbai-embed-large" if len(sys.argv) < 2 else sys.argv[1]
    success = test_embedding(model)
    print(f"測試結果: {'成功' if success else '失敗'}")

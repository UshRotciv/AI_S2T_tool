# AI Service Dockerfile
# 基於 Python 3.11 slim 版本
FROM python:3.11-slim

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 設定工作目錄
WORKDIR /app

# 複製 requirements 並安裝 Python 依賴
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程式碼
COPY . .

# 建立 ChromaDB 資料目錄
RUN mkdir -p chroma_db

# 設定環境變數
ENV PYTHONPATH=/app
ENV AI_PORT=8000
ENV CHROMA_DIR=/app/chroma_db

# 暴露端口
EXPOSE 8000

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/status', timeout=5)" || exit 1

# 啟動應用
CMD ["python", "main.py"]

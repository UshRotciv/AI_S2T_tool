# App Server Dockerfile
# 基於 Node.js 20 Alpine 版本，輕量且安全
FROM node:20-alpine

# 安裝 better-sqlite3 所需的編譯工具
RUN apk add --no-cache python3 make g++ sqlite

# 設定工作目錄
WORKDIR /app

# 複製 package 檔案並安裝依賴
COPY package.json package-lock.json* ./
RUN npm ci --only=production

# 複製應用程式碼
COPY . .

# 建立 SQLite 資料庫目錄
RUN mkdir -p sqlite

# 設定環境變數
ENV NODE_ENV=production
ENV APP_PORT=3001

# 暴露端口
EXPOSE 3001

# 健康檢查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3001/health || exit 1

# 啟動應用
CMD ["npm", "start"]

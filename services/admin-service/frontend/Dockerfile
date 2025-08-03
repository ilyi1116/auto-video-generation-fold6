# 使用 Node.js 官方映像
FROM node:18-alpine AS builder

# 設定工作目錄
WORKDIR /app

# 複製 package 文件
COPY package*.json ./

# 安裝依賴
RUN npm ci --only=production

# 複製原始碼
COPY . .

# 建構應用
RUN npm run build

# 生產階段 - 使用 Nginx
FROM nginx:alpine

# 複製建構結果到 Nginx
COPY --from=builder /app/build /usr/share/nginx/html

# 複製 Nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 暴露端口
EXPOSE 80

# 啟動 Nginx
CMD ["nginx", "-g", "daemon off;"]
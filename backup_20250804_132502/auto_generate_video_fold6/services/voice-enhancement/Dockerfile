FROM python:3.11-slim

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# 複製需求文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 創建非特權用戶
RUN groupadd -r appuser && useradd -r -g appuser appuser

# 複製應用程式碼並設置權限
COPY ./app ./app
RUN chown -R appuser:appuser /app

# 切換到非特權用戶
USER appuser

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# 運行應用
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
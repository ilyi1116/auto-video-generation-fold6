FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    imagemagick \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create non-privileged user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy application code
COPY app/ ./app/

# Create directories for storage
RUN mkdir -p /app/storage/{temp,images,audio,video,documents} && \
    chown -R appuser:appuser /app && \
    chmod -R 755 /app/storage

# Switch to non-privileged user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
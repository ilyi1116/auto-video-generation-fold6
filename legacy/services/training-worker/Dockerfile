# Multi-stage Dockerfile for Training Worker Service
# Optimized for ML model training with GPU support (optional)

# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies for audio processing and ML
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    g++ \
    libsndfile1 \
    libsoundfile1 \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Stage 2: Dependencies builder
FROM base as dependencies

# Set work directory
WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements and install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Production runtime
FROM python:3.11-slim as production

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    libsoundfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from dependencies stage
COPY --from=dependencies /opt/venv /opt/venv

# Copy application code
COPY main.py .

# Create directories for model storage
RUN mkdir -p /models /tmp/training \
    && chown -R appuser:appuser /app /models /tmp/training

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"

# Expose port (for monitoring/health checks if needed)
EXPOSE 8080

# Start Celery worker
CMD ["celery", "-A", "main.celery_app", "worker", \
     "--loglevel=info", \
     "--concurrency=2", \
     "--max-tasks-per-child=1000"]

# Labels for metadata
LABEL maintainer="ilyi1116@users.noreply.github.com" \
      version="1.0.0" \
      description="Training worker service for voice model training and fine-tuning" \
      org.opencontainers.image.title="Training Worker Service" \
      org.opencontainers.image.description="Celery worker service for ML model training and evaluation" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="ilyi1116@users.noreply.github.com" \
      org.opencontainers.image.source="https://github.com/ilyi1116/auto-video-generation-fold6" \
      org.opencontainers.image.licenses="MIT"
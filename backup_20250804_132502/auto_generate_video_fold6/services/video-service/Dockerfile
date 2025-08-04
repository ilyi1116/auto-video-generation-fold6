# Multi-stage Dockerfile for Video Generation Service
# Optimized for production deployment with security and performance considerations

# Stage 1: Base Python image with system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies with optimizations
RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libpq-dev \
        gcc \
        g++ \
        libc6-dev \
        curl \
        ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Stage 2: Dependencies installation
FROM base as dependencies

# Copy requirements files
COPY requirements.txt requirements-dev.txt ./

# Install Python dependencies with optimizations
RUN set -ex \
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --compile -r requirements.txt \
    && pip cache purge \
    && find /usr/local/lib/python3.11 -name '*.pyc' -delete \
    && find /usr/local/lib/python3.11 -name '*.pyo' -delete

# Stage 3: Development environment
FROM dependencies as development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port for development
EXPOSE 8003

# Development command
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003", "--reload"]

# Stage 4: Production build
FROM dependencies as builder

# Copy source code
COPY . .

# Create directories for media storage
RUN mkdir -p storage/images storage/videos storage/previews storage/thumbnails

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Stage 5: Production runtime
FROM python:3.11-slim as production

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# Install minimal runtime dependencies
RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libpq5 \
        curl \
        ca-certificates \
        tini \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && useradd --create-home --shell /bin/bash --user-group appuser

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies from dependencies stage
COPY --from=dependencies /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies /usr/local/bin /usr/local/bin

# Copy application code from builder stage
COPY --from=builder --chown=appuser:appuser /app .

# Create storage directories with proper permissions
RUN mkdir -p storage/images storage/videos storage/previews storage/thumbnails \
    && chown -R appuser:appuser storage

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8003/health || exit 1

# Expose port
EXPOSE 8003

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]

# Production command with optimized settings for video processing
CMD ["python", "-m", "uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8003", \
     "--workers", "4", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--max-requests", "500", \
     "--max-requests-jitter", "50", \
     "--timeout-keep-alive", "5", \
     "--access-log", \
     "--log-level", "info"]

# Stage 6: Testing environment
FROM development as testing

# Install additional testing tools
RUN pip install --no-cache-dir pytest-cov pytest-asyncio httpx

# Copy test files
COPY tests/ tests/

# Switch to non-root user
USER appuser

# Test command
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=.", "--cov-report=html"]

# Labels for metadata
LABEL maintainer="ilyi1116@users.noreply.github.com" \
      version="1.0.0" \
      description="AI-powered video generation service" \
      org.opencontainers.image.title="Video Generation Service" \
      org.opencontainers.image.description="FastAPI service for automated video generation using AI" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="ilyi1116@users.noreply.github.com" \
      org.opencontainers.image.source="https://github.com/ilyi1116/auto-video-generation-fold6" \
      org.opencontainers.image.licenses="MIT"
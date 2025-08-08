# Multi-stage Dockerfile for Trend Analysis Service
# Optimized for production deployment with security and performance considerations

# Stage 1: Base Python image with system dependencies
FROM python:3.11-slim as base

# Set environment variables for better performance
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONHASHSEED=random \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# Install system dependencies in one layer for better caching
RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
        libssl-dev \
        libpq-dev \
        curl \
        ca-certificates \
    && apt-get purge -y --auto-remove gcc libc6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set working directory
WORKDIR /app

# Stage 2: Dependencies installation with optimizations
FROM base as dependencies

# Install pip dependencies in single layer with optimizations
COPY requirements.txt ./
RUN set -ex \
    && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir --compile -r requirements.txt     && find /usr/local/lib/python3.11 -name '*.pyc' -delete     && find /usr/local/lib/python3.11 -name '*.pyo' -delete

# Stage 3: Development environment
FROM dependencies as development

# Install development dependencies
COPY requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy source code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port for development
EXPOSE 8007

# Development command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8007", "--reload"]

# Stage 4: Production build
FROM dependencies as builder

# Copy source code
COPY . .

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Stage 5: Optimized production runtime
FROM python:3.11-slim as production

# Set production environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONHASHSEED=random \
    ENVIRONMENT=production \
    PYTHONPATH=/app \
    PATH=/app/.local/bin:$PATH

# Install minimal runtime dependencies
RUN set -ex \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        libssl3 \
        libpq5 \
        curl \
        ca-certificates \
        tini \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
    && useradd --create-home --shell /bin/bash --user-group appuser

# Set working directory
WORKDIR /app

# Copy Python dependencies (optimized for layer caching)
COPY --from=dependencies --chown=appuser:appuser /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=dependencies --chown=appuser:appuser /usr/local/bin /usr/local/bin

# Copy application code from builder stage
COPY --from=builder --chown=appuser:appuser /app .

# Optimize Python bytecode compilation
RUN python -m compileall -b /app && find /app -name '*.py' -delete

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8007/health || exit 1

# Expose port
EXPOSE 8007

# Use tini as init system for proper signal handling
ENTRYPOINT ["tini", "--"]

# Production command with optimized settings
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8007", \
     "--workers", "2", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--max-requests", "1000", \
     "--max-requests-jitter", "100", \
     "--preload", \
     "--access-log", \
     "--log-level", "info"]

# Stage 6: Testing environment
FROM development as testing

# Install additional testing tools
RUN pip install --no-cache-dir pytest-cov pytest-asyncio httpx

# Switch to non-root user
USER appuser

# Test command
CMD ["python", "-m", "pytest", "tests/", "-v", "--cov=.", "--cov-report=html"]

# Labels for metadata
LABEL maintainer="ilyi1116@users.noreply.github.com" \
      version="1.0.0" \
      description="AI-powered trend analysis service" \
      org.opencontainers.image.title="Trend Analysis Service" \
      org.opencontainers.image.description="FastAPI service for social media trend analysis" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="ilyi1116@users.noreply.github.com" \
      org.opencontainers.image.source="https://github.com/ilyi1116/auto-video-generation-fold6" \
      org.opencontainers.image.licenses="MIT"
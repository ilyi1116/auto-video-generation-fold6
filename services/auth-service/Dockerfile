# Multi-stage Dockerfile for Authentication Service
# Optimized for production with security and JWT handling

# Stage 1: Base image with system dependencies
FROM python:3.13-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    libpq-dev \
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
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Stage 3: Development environment
FROM dependencies as development

# Install development dependencies
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY ./app ./app

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app" \
    ENVIRONMENT=development

# Expose port
EXPOSE 8001

# Development command with auto-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload", "--proxy-headers"]

# Stage 4: Production runtime
FROM python:3.13-slim as production

# Set environment variables for production
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production

# Install runtime system dependencies only
RUN apt-get update && apt-get install -y \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd --no-log-init -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy virtual environment from dependencies stage
COPY --from=dependencies /opt/venv /opt/venv

# Copy application code
COPY ./app ./app

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Expose port
EXPOSE 8001

# Production command with optimized settings
CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8001", \
     "--workers", "2", \
     "--proxy-headers", \
     "--access-log", \
     "--log-level", "info"]

# Stage 5: Testing environment
FROM development as testing

# Install additional testing tools
RUN pip install --no-cache-dir pytest-cov pytest-asyncio httpx

# Test command (no tests directory exists yet)
CMD ["python", "-m", "pytest", "--version"]

# Labels for metadata
LABEL maintainer="ilyi1116@users.noreply.github.com" \
      version="1.0.0" \
      description="Authentication service with JWT and user management" \
      org.opencontainers.image.title="Authentication Service" \
      org.opencontainers.image.description="FastAPI-based authentication service with JWT tokens" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="ilyi1116@users.noreply.github.com" \
      org.opencontainers.image.source="https://github.com/ilyi1116/auto-video-generation-fold6" \
      org.opencontainers.image.licenses="MIT"
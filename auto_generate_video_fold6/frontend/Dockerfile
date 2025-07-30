# Multi-stage Dockerfile for Frontend SvelteKit Application
# Optimized for production deployment with security and performance considerations

# Stage 1: Base Node.js image
FROM node:18-alpine as base

# Set environment variables
ENV NODE_ENV=development \
    NPM_CONFIG_CACHE=/tmp/.npm \
    PNPM_HOME="/pnpm" \
    PATH="$PNPM_HOME:$PATH"

# Install pnpm globally
RUN corepack enable && corepack prepare pnpm@latest --activate

# Create non-root user for security
RUN addgroup -g 1001 -S nodejs && \
    adduser -S sveltekit -u 1001

# Set working directory
WORKDIR /app

# Stage 2: Dependencies installation
FROM base as dependencies

# Copy package files
COPY package.json pnpm-lock.yaml* ./

# Install all dependencies (including dev dependencies for build)
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm install --frozen-lockfile

# Stage 3: Development environment
FROM dependencies as development

# Copy source code
COPY . .

# Change ownership to non-root user
RUN chown -R sveltekit:nodejs /app

# Switch to non-root user
USER sveltekit

# Expose port for development
EXPOSE 5173

# Development command with hot reload
CMD ["pnpm", "dev", "--host", "0.0.0.0"]

# Stage 4: Build stage
FROM dependencies as builder

# Copy source code
COPY . .

# Set environment to production for build
ENV NODE_ENV=production

# Build the application
RUN pnpm run build

# Remove dev dependencies and install only production deps
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm prune --prod --config.ignore-scripts=true

# Stage 5: Production runtime
FROM node:18-alpine as production

# Set environment variables for production
ENV NODE_ENV=production \
    PORT=3000

# Install only runtime dependencies
RUN apk add --no-cache \
    curl \
    dumb-init

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S sveltekit -u 1001

# Set working directory
WORKDIR /app

# Copy production dependencies from builder stage
COPY --from=builder --chown=sveltekit:nodejs /app/node_modules ./node_modules

# Copy built application from builder stage
COPY --from=builder --chown=sveltekit:nodejs /app/build ./build
COPY --from=builder --chown=sveltekit:nodejs /app/package.json ./package.json

# Create cache directory with proper permissions
RUN mkdir -p /tmp/.cache && chown -R sveltekit:nodejs /tmp/.cache

# Switch to non-root user
USER sveltekit

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Expose port
EXPOSE 3000

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Production command
CMD ["node", "build/index.js"]

# Stage 6: Testing environment
FROM dependencies as testing

# Install additional testing dependencies
RUN --mount=type=cache,id=pnpm,target=/pnpm/store \
    pnpm add -D @playwright/test

# Copy source code and test files
COPY . .

# Install Playwright browsers
RUN pnpm playwright install --with-deps

# Change ownership to non-root user
RUN chown -R sveltekit:nodejs /app

# Switch to non-root user
USER sveltekit

# Test command
CMD ["pnpm", "test"]

# Stage 7: Static build (for serving with nginx)
FROM nginx:alpine as static

# Copy built files from builder stage
COPY --from=builder /app/build /usr/share/nginx/html

# Copy custom nginx configuration
COPY --from=builder /app/nginx.conf /etc/nginx/conf.d/default.conf 2>/dev/null || \
    echo 'server { listen 80; location / { try_files $uri $uri/ /index.html; } }' > /etc/nginx/conf.d/default.conf

# Health check for nginx
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost || exit 1

# Expose port
EXPOSE 80

# Labels for metadata
LABEL maintainer="ilyi1116@users.noreply.github.com" \
      version="1.0.0" \
      description="SvelteKit frontend application for AI video generation platform" \
      org.opencontainers.image.title="AI Video Generator Frontend" \
      org.opencontainers.image.description="Modern web interface built with SvelteKit for automated video generation" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.authors="ilyi1116@users.noreply.github.com" \
      org.opencontainers.image.source="https://github.com/ilyi1116/auto-video-generation-fold6" \
      org.opencontainers.image.licenses="MIT"
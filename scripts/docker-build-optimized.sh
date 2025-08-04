#!/bin/bash

# Docker Build Optimization Script
# This script implements advanced Docker build optimizations for better performance and smaller images

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
REGISTRY_PREFIX="${CI_REGISTRY_IMAGE:-auto-video-generation}"
COMMIT_SHA="${CI_COMMIT_SHA:-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')}"
BUILD_CACHE_DIR="${BUILD_CACHE_DIR:-/tmp/docker-cache}"
PARALLEL_BUILDS="${PARALLEL_BUILDS:-4}"
ENABLE_BUILDKIT="${ENABLE_BUILDKIT:-1}"

# Services to build
SERVICES=("frontend" "trend-service" "video-service" "social-service" "scheduler-service" "api-gateway")

# Enable Docker BuildKit for advanced features
export DOCKER_BUILDKIT=${ENABLE_BUILDKIT}
export COMPOSE_DOCKER_CLI_BUILD=${ENABLE_BUILDKIT}

echo -e "${BLUE}🚀 Starting optimized Docker build process${NC}"
echo -e "${BLUE}📋 Configuration:${NC}"
echo -e "  Registry: ${REGISTRY_PREFIX}"
echo -e "  Commit SHA: ${COMMIT_SHA}"
echo -e "  Cache Dir: ${BUILD_CACHE_DIR}"
echo -e "  Parallel Builds: ${PARALLEL_BUILDS}"
echo -e "  BuildKit: ${ENABLE_BUILDKIT}"

# Create cache directory
mkdir -p "${BUILD_CACHE_DIR}"

# Function to build a single service with optimizations
build_service() {
    local service=$1
    local context_path=""
    local dockerfile_path=""
    
    case $service in
        "frontend")
            context_path="./frontend"
            dockerfile_path="./frontend/Dockerfile"
            ;;
        *"-service")
            context_path="./services/${service}"
            dockerfile_path="./services/${service}/Dockerfile"
            ;;
        *)
            echo -e "${RED}❌ Unknown service: ${service}${NC}"
            return 1
            ;;
    esac
    
    local image_name="${REGISTRY_PREFIX}/${service}:${COMMIT_SHA}"
    local cache_image="${REGISTRY_PREFIX}/${service}:cache"
    local cache_file="${BUILD_CACHE_DIR}/${service}-cache.tar"
    
    echo -e "${YELLOW}🔨 Building ${service}...${NC}"
    
    # Build arguments for optimization
    local build_args=(
        "--file" "${dockerfile_path}"
        "--target" "production"
        "--tag" "${image_name}"
        "--tag" "${cache_image}"
        "--build-arg" "BUILDKIT_INLINE_CACHE=1"
        "--build-arg" "PYTHON_VERSION=3.11"
        "--build-arg" "NODE_VERSION=18"
    )
    
    # Add cache from options if cache exists
    if [[ -f "${cache_file}" ]]; then
        echo -e "${BLUE}📦 Loading cache for ${service}${NC}"
        docker load -i "${cache_file}" 2>/dev/null || true
        build_args+=("--cache-from" "${cache_image}")
    fi
    
    # Add registry cache if available
    if docker pull "${cache_image}" 2>/dev/null; then
        build_args+=("--cache-from" "${cache_image}")
    fi
    
    # Perform the build
    if docker build "${build_args[@]}" "${context_path}"; then
        echo -e "${GREEN}✅ Successfully built ${service}${NC}"
        
        # Save cache for future builds
        echo -e "${BLUE}💾 Saving cache for ${service}${NC}"
        docker save "${cache_image}" -o "${cache_file}" 2>/dev/null || true
        
        # Analyze image size
        local image_size=$(docker images "${image_name}" --format "table {{.Size}}" | tail -1)
        echo -e "${GREEN}📊 ${service} image size: ${image_size}${NC}"
        
        return 0
    else
        echo -e "${RED}❌ Failed to build ${service}${NC}"
        return 1
    fi
}

# Function to run parallel builds
run_parallel_builds() {
    local pids=()
    local failed_services=()
    
    echo -e "${BLUE}🔄 Starting parallel builds (max ${PARALLEL_BUILDS} concurrent)${NC}"
    
    for service in "${SERVICES[@]}"; do
        # Wait if we've reached max parallel builds
        while [[ ${#pids[@]} -ge ${PARALLEL_BUILDS} ]]; do
            for i in "${!pids[@]}"; do
                if ! kill -0 "${pids[i]}" 2>/dev/null; then
                    wait "${pids[i]}"
                    if [[ $? -ne 0 ]]; then
                        failed_services+=("${service}")
                    fi
                    unset pids[i]
                    pids=("${pids[@]}")  # Re-index array
                fi
            done
            sleep 1
        done
        
        # Start build in background
        build_service "${service}" &
        pids+=($!)
        
        echo -e "${BLUE}🚀 Started build for ${service} (PID: $!)${NC}"
    done
    
    # Wait for all remaining builds to complete
    for pid in "${pids[@]}"; do
        wait "${pid}"
        if [[ $? -ne 0 ]]; then
            failed_services+=("unknown")
        fi
    done
    
    # Report results
    if [[ ${#failed_services[@]} -eq 0 ]]; then
        echo -e "${GREEN}🎉 All services built successfully!${NC}"
        return 0
    else
        echo -e "${RED}❌ Failed to build ${#failed_services[@]} services${NC}"
        return 1
    fi
}

# Function to optimize existing images
optimize_images() {
    echo -e "${YELLOW}🗜️  Optimizing images...${NC}"
    
    for service in "${SERVICES[@]}"; do
        local image_name="${REGISTRY_PREFIX}/${service}:${COMMIT_SHA}"
        
        # Check if image exists
        if docker images -q "${image_name}" >/dev/null; then
            # Remove intermediate layers and unused data
            echo -e "${BLUE}🧹 Optimizing ${service} image${NC}"
            
            # Get before size
            local before_size=$(docker images "${image_name}" --format "{{.Size}}")
            
            # Create optimized version (if docker-squash is available)
            if command -v docker-squash >/dev/null 2>&1; then
                docker-squash "${image_name}" -t "${image_name}-optimized" >/dev/null 2>&1 || true
                docker tag "${image_name}-optimized" "${image_name}" 2>/dev/null || true
                docker rmi "${image_name}-optimized" 2>/dev/null || true
            fi
            
            # Get after size
            local after_size=$(docker images "${image_name}" --format "{{.Size}}")
            echo -e "${GREEN}📈 ${service}: ${before_size} → ${after_size}${NC}"
        fi
    done
}

# Function to generate build report
generate_build_report() {
    local report_file="docker-build-report.json"
    
    echo -e "${BLUE}📋 Generating build report...${NC}"
    
    cat > "${report_file}" << EOF
{
  "build_info": {
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "commit_sha": "${COMMIT_SHA}",
    "registry_prefix": "${REGISTRY_PREFIX}",
    "buildkit_enabled": ${ENABLE_BUILDKIT}
  },
  "images": [
EOF
    
    local first=true
    for service in "${SERVICES[@]}"; do
        local image_name="${REGISTRY_PREFIX}/${service}:${COMMIT_SHA}"
        
        if docker images -q "${image_name}" >/dev/null; then
            [[ ${first} == false ]] && echo "    ," >> "${report_file}"
            
            local size=$(docker images "${image_name}" --format "{{.Size}}")
            local created=$(docker images "${image_name}" --format "{{.CreatedAt}}")
            
            cat >> "${report_file}" << EOF
    {
      "service": "${service}",
      "image": "${image_name}",
      "size": "${size}",
      "created": "${created}"
    }
EOF
            first=false
        fi
    done
    
    cat >> "${report_file}" << EOF
  ]
}
EOF
    
    echo -e "${GREEN}📄 Build report saved to ${report_file}${NC}"
}

# Function to cleanup old images and cache
cleanup_old_data() {
    echo -e "${YELLOW}🧹 Cleaning up old data...${NC}"
    
    # Remove dangling images
    docker image prune -f >/dev/null 2>&1 || true
    
    # Remove old cache files (older than 7 days)
    find "${BUILD_CACHE_DIR}" -name "*.tar" -type f -mtime +7 -delete 2>/dev/null || true
    
    # Remove unused volumes
    docker volume prune -f >/dev/null 2>&1 || true
    
    echo -e "${GREEN}✅ Cleanup completed${NC}"
}

# Main execution
main() {
    local start_time=$(date +%s)
    
    # Ensure prerequisites
    if ! command -v docker >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not installed${NC}"
        exit 1
    fi
    
    # Check Docker daemon
    if ! docker info >/dev/null 2>&1; then
        echo -e "${RED}❌ Docker daemon is not running${NC}"
        exit 1
    fi
    
    # Run cleanup first
    cleanup_old_data
    
    # Run builds
    if run_parallel_builds; then
        # Optimize images
        optimize_images
        
        # Generate report
        generate_build_report
        
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo -e "${GREEN}🎉 Build completed successfully in ${duration}s${NC}"
        echo -e "${BLUE}📊 Summary:${NC}"
        docker images "${REGISTRY_PREFIX}/*:${COMMIT_SHA}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
        
        exit 0
    else
        echo -e "${RED}❌ Build failed${NC}"
        exit 1
    fi
}

# Handle script arguments
case "${1:-build}" in
    "build")
        main
        ;;
    "cleanup")
        cleanup_old_data
        ;;
    "report")
        generate_build_report
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [build|cleanup|report|help]"
        echo "  build   - Build all services with optimizations (default)"
        echo "  cleanup - Clean up old images and cache"
        echo "  report  - Generate build report"
        echo "  help    - Show this help message"
        ;;
    *)
        echo -e "${RED}❌ Unknown command: $1${NC}"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
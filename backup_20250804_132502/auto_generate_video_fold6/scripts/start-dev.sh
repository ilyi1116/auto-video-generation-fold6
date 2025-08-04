#!/bin/bash

# Voice Cloning System - Development Startup Script

set -e

echo "🚀 Starting Voice Cloning System Development Environment..."

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose >/dev/null 2>&1; then
    echo "❌ docker-compose is not installed. Please install docker-compose."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "📄 Creating .env file from .env.example..."
    cp .env.example .env
    echo "✅ .env file created. Please review and customize it if needed."
fi

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

services=("postgres:5432" "redis:6379" "api-gateway:8000" "auth-service:8001" "data-service:8002" "inference-service:8003")

for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    if docker-compose exec -T $name sh -c "nc -z localhost $port" >/dev/null 2>&1; then
        echo "✅ $name is ready"
    else
        echo "⚠️  $name might not be ready yet"
    fi
done

echo ""
echo "🎉 Voice Cloning System is starting up!"
echo ""
echo "📊 Service URLs:"
echo "   • API Gateway:       http://localhost:8000"
echo "   • Auth Service:      http://localhost:8001"
echo "   • Data Service:      http://localhost:8002"
echo "   • Inference Service: http://localhost:8003"
echo "   • API Docs:          http://localhost:8000/docs"
echo "   • PostgreSQL:        localhost:5432"
echo "   • Redis:             localhost:6379"
echo "   • MinIO Console:     http://localhost:9001"
echo ""
echo "🔧 Development Commands:"
echo "   • View logs:       docker-compose logs -f"
echo "   • Stop services:   docker-compose down"
echo "   • Restart:         docker-compose restart"
echo "   • Clean up:        docker-compose down -v"
echo ""
echo "📚 Next steps:"
echo "   1. Test the API: curl http://localhost:8000/health"
echo "   2. Register a user: curl -X POST http://localhost:8000/api/v1/auth/register -d '{\"email\":\"test@example.com\",\"username\":\"testuser\",\"password\":\"testpass123\"}' -H 'Content-Type: application/json'"
echo "   3. Check API documentation at http://localhost:8000/docs"
echo ""
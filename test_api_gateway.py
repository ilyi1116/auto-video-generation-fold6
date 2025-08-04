#!/usr/bin/env python3
"""Simple API Gateway test"""

import os
import sys
from typing import List

# Set environment variables for testing
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-development")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "info")

try:
    # Test basic FastAPI functionality
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    print("✅ FastAPI imported successfully")

    # Test basic imports
    import structlog
    print("✅ structlog imported successfully")
    
    # Create simple test app
    app = FastAPI(
        title="Test API Gateway",
        version="1.0.0",
        description="Simple API Gateway test"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
    
    # Simple health check
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "api-gateway-test"}
    
    @app.get("/")
    async def root():
        return {"message": "API Gateway Test", "version": "1.0.0"}
    
    print("✅ Test API Gateway created successfully")
    print("✅ Available endpoints: /health, /")
    print("✅ Ready to start with: uvicorn test_api_gateway:app --host 0.0.0.0 --port 8000")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error creating test app: {e}")
    sys.exit(1)
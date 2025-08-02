import pytest
from fastapi.testclient import TestClient

def test_root_endpoint(client: TestClient):
    """測試根端點"""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Auto Video Generation System API"}

def test_health_check(client: TestClient):
    """測試健康檢查端點"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_cors_headers(client: TestClient):
    """測試 CORS 標頭"""
    response = client.options("/")
    assert response.status_code == 200
    assert "access-control-allow-origin" in response.headers 
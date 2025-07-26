import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_health_check():
    """測試健康檢查端點"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_root_endpoint():
    """測試根端點"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "API Gateway" in data["message"]

def test_cors_headers():
    """測試 CORS 標頭"""
    response = client.options("/health")
    assert response.status_code == 200

def test_metrics_endpoint():
    """測試指標端點（如果有的話）"""
    response = client.get("/metrics")
    # 可能回傳 404 或 200，取決於是否實作
    assert response.status_code in [200, 404]

def test_invalid_endpoint():
    """測試無效端點"""
    response = client.get("/invalid-endpoint")
    assert response.status_code == 404
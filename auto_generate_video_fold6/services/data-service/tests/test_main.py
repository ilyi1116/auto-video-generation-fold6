import pytest
from app.main import app
from fastapi.testclient import TestClient

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
    assert "Data Service" in data["message"]


def test_upload_endpoint_no_auth():
    """測試未授權的上傳請求"""
    response = client.post("/api/v1/upload/")
    assert response.status_code in [401, 403]  # 未授權


def test_process_endpoint_no_auth():
    """測試未授權的處理請求"""
    response = client.get("/api/v1/process/status/1")
    assert response.status_code in [401, 403]  # 未授權

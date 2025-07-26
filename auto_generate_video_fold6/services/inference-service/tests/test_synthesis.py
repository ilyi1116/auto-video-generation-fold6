import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
import json

from app.main import app


class TestSynthesisEndpoints:
    """Test synthesis-related endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_synthesis_without_auth(self, client):
        """Test synthesis endpoint without authentication"""
        response = client.post("/api/v1/synthesize", json={
            "text": "Hello world",
            "model_id": 1
        })
        assert response.status_code == 403  # Unauthorized
    
    def test_synthesis_with_auth(
        self, 
        client, 
        mock_auth_service, 
        mock_database, 
        mock_s3_storage,
        mock_model_manager,
        sample_voice_model,
        sample_synthesis_request
    ):
        """Test successful synthesis with authentication"""
        # Mock database responses
        mock_database.fetch_one.return_value = sample_voice_model
        mock_database.execute.return_value = 1  # job_id
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.post(
            "/api/v1/synthesize", 
            json=sample_synthesis_request,
            headers=headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["model_id"] == 1
        assert data["text"] == sample_synthesis_request["text"]
    
    def test_synthesis_model_not_found(
        self, 
        client, 
        mock_auth_service, 
        mock_database
    ):
        """Test synthesis with non-existent model"""
        # Mock database to return None (model not found)
        mock_database.fetch_one.return_value = None
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.post("/api/v1/synthesize", json={
            "text": "Hello world",
            "model_id": 999
        }, headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_synthesis_with_return_audio(
        self, 
        client, 
        mock_auth_service, 
        mock_database, 
        mock_s3_storage,
        mock_model_manager,
        sample_voice_model
    ):
        """Test synthesis with return_audio=True"""
        # Mock database responses
        mock_database.fetch_one.return_value = sample_voice_model
        mock_database.execute.return_value = 1  # job_id
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.post("/api/v1/synthesize", json={
            "text": "Hello world",
            "model_id": 1,
            "return_audio": True
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "audio_url" in data
        assert "processing_time" in data
    
    def test_batch_synthesis(
        self, 
        client, 
        mock_auth_service, 
        mock_database,
        sample_voice_model
    ):
        """Test batch synthesis"""
        # Mock database responses
        mock_database.fetch_one.return_value = sample_voice_model
        mock_database.execute.return_value = 1  # job_id
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.post("/api/v1/synthesize/batch", json={
            "texts": ["Hello world", "How are you?"],
            "model_id": 1
        }, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["batch_size"] == 2
        assert len(data["job_ids"]) == 2
    
    def test_get_synthesis_jobs(
        self, 
        client, 
        mock_auth_service, 
        mock_database
    ):
        """Test getting synthesis jobs"""
        # Mock database response
        mock_database.fetch_all.return_value = [
            {
                "id": 1,
                "status": "completed",
                "text": "Hello world",
                "model_id": 1,
                "audio_url": "http://example.com/audio.wav",
                "audio_duration": 2.5,
                "processing_time": 1.2,
                "created_at": "2024-01-01T00:00:00",
                "completed_at": "2024-01-01T00:00:01"
            }
        ]
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.get("/api/v1/jobs", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["job_id"] == 1
        assert data[0]["status"] == "completed"
    
    def test_get_synthesis_job_by_id(
        self, 
        client, 
        mock_auth_service, 
        mock_database
    ):
        """Test getting specific synthesis job"""
        # Mock database response
        mock_database.fetch_one.return_value = {
            "id": 1,
            "status": "completed",
            "text": "Hello world",
            "model_id": 1,
            "audio_url": "http://example.com/audio.wav",
            "audio_duration": 2.5,
            "processing_time": 1.2,
            "created_at": "2024-01-01T00:00:00",
            "completed_at": "2024-01-01T00:00:01"
        }
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.get("/api/v1/jobs/1", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == 1
        assert data["status"] == "completed"
    
    def test_get_synthesis_job_not_found(
        self, 
        client, 
        mock_auth_service, 
        mock_database
    ):
        """Test getting non-existent synthesis job"""
        # Mock database to return None
        mock_database.fetch_one.return_value = None
        
        headers = {"Authorization": "Bearer fake-token"}
        response = client.get("/api/v1/jobs/999", headers=headers)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_synthesis_validation_errors(self, client, mock_auth_service):
        """Test synthesis input validation"""
        headers = {"Authorization": "Bearer fake-token"}
        
        # Test empty text
        response = client.post("/api/v1/synthesize", json={
            "text": "",
            "model_id": 1
        }, headers=headers)
        assert response.status_code == 422
        
        # Test text too long
        response = client.post("/api/v1/synthesize", json={
            "text": "x" * 1001,  # Over the 1000 character limit
            "model_id": 1
        }, headers=headers)
        assert response.status_code == 422
        
        # Test invalid speed
        response = client.post("/api/v1/synthesize", json={
            "text": "Hello world",
            "model_id": 1,
            "speed": 3.0  # Over the 2.0 limit
        }, headers=headers)
        assert response.status_code == 422
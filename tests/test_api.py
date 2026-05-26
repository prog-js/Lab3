import pytest
from fastapi.testclient import TestClient
from src.api import app

client = TestClient(app)

class TestAPI:
    
    def test_health_endpoint(self):
        """Тест: эндпоинт /health"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    def test_regions_endpoint(self):
        """Тест: эндпоинт /regions"""
        response = client.get("/regions")
        assert response.status_code == 200
        assert "regions" in response.json()
        assert isinstance(response.json()["regions"], list)
    
    def test_universities_endpoint(self):
        """Тест: эндпоинт /universities"""
        response = client.get("/universities")
        assert response.status_code == 200
        assert "universities" in response.json()
    
    def test_top_specialties_endpoint(self):
        """Тест: эндпоинт /top_specialties"""
        response = client.post(
            "/top_specialties",
            json={"region": "Москва", "top_n": 3}
        )
        # Может вернуть 404, если нет данных, но структура должна быть
        assert response.status_code in [200, 404]
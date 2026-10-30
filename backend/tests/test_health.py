"""Unit tests for the health check endpoint."""

from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)


def test_health_check_status_and_schema():
    """Verify GET /api/v1/health returns 200 OK and expected JSON schema."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "clausetrace-api"
    assert payload["version"] == "2.0.0"
    assert payload["llm_provider"] == "meta-llama"
    assert payload["primary_model"] == settings.META_PRIMARY_MODEL
    assert isinstance(payload["api_key_configured"], bool)

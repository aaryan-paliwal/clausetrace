"""Tests for workspaces and deontic graph API router."""
import io
import os
import tempfile
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import init_db
from app.config import settings

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    original_path = settings.DATABASE_PATH
    settings.DATABASE_PATH = path
    init_db(path)
    yield path
    settings.DATABASE_PATH = original_path
    if os.path.exists(path):
        os.remove(path)


def test_list_and_seed_workspaces():
    # Initial call should auto-seed default workspaces and compile startup_founder_legal
    response = client.get("/api/v1/workspaces")
    assert response.status_code == 200
    workspaces = response.json()
    assert len(workspaces) >= 1
    ws_ids = [w["id"] for w in workspaces]
    assert "ws_startup_legal" in ws_ids


def test_get_workspace_graph():
    # First trigger list to auto-seed
    client.get("/api/v1/workspaces")

    response = client.get("/api/v1/workspaces/ws_startup_legal/graph")
    assert response.status_code == 200
    graph = response.json()

    assert graph["workspace_id"] == "ws_startup_legal"
    metrics = graph["summary_metrics"]
    assert metrics["total_documents"] == 3
    assert metrics["total_clauses"] > 0
    assert metrics["total_rules"] > 0
    assert metrics["active_conflicts"] > 0

    assert len(graph["nodes"]) > 0
    assert len(graph["edges"]) > 0
    assert len(graph["conflicts"]) > 0


def test_upload_document_recompiles_graph():
    # Setup workspace
    client.get("/api/v1/workspaces")

    doc_content = b"""# Supplementary Service Agreement
## 1.1 Notice Period
The Contractor may terminate upon forty-five (45) days prior written notice.
"""
    file_payload = {"file": ("supplement.md", io.BytesIO(doc_content), "text/markdown")}

    response = client.post(
        "/api/v1/workspaces/ws_startup_legal/documents",
        files=file_payload,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["clauses_created"] >= 1
    assert data["summary_metrics"]["total_documents"] == 4

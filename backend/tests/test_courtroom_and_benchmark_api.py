"""Tests for Courtroom, Counterfactual, and Benchmark API endpoints."""
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


def test_courtroom_ask_and_stream_endpoints():
    # 1. Trigger list to auto-seed startup founder legal
    client.get("/api/v1/workspaces")

    # 2. Ask courtroom endpoint
    ask_res = client.post(
        "/api/v1/workspaces/ws_startup_legal/courtroom/ask",
        json={"query": "What is the Executive base salary?"},
    )
    assert ask_res.status_code == 200
    verdict = ask_res.json()
    assert verdict["verdict_state"] == "ANSWERABLE"
    assert "advocate_brief" in verdict
    assert "skeptic_brief" in verdict

    # 3. Stream courtroom endpoint
    stream_res = client.post(
        "/api/v1/workspaces/ws_startup_legal/courtroom/stream",
        json={"query": "What is the Executive base salary?"},
    )
    assert stream_res.status_code == 200
    stream_text = stream_res.text
    assert "event: retrieval" in stream_text
    assert "event: verdict" in stream_text


def test_conflict_patch_and_apply_endpoints():
    # Setup workspace
    client.get("/api/v1/workspaces")
    graph_res = client.get("/api/v1/workspaces/ws_startup_legal/graph")
    conflicts = graph_res.json()["conflicts"]
    assert len(conflicts) > 0
    conflict_id = conflicts[0]["id"]

    # 1. Generate verified patch
    patch_res = client.post(
        f"/api/v1/workspaces/ws_startup_legal/conflicts/{conflict_id}/patch"
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["verification_passed"] is True
    assert patch_data["remaining_conflicts"] == 0

    # 2. Apply patch
    graph_after_patch = client.get("/api/v1/workspaces/ws_startup_legal/graph")
    # Patch was created and recorded in patches table
    patch_id = graph_after_patch.json().get("patches", [{}])[0].get("id")
    if not patch_id:
        from app.db.database import get_db_context
        from app.db.repository import Repository
        with get_db_context(settings.DATABASE_PATH) as conn:
            repo = Repository(conn)
            patch_id = repo.list_patches()[0]["id"]

    apply_res = client.post(
        f"/api/v1/workspaces/ws_startup_legal/patches/{patch_id}/apply"
    )
    assert apply_res.status_code == 200
    assert apply_res.json()["status"] == "applied"


def test_benchmark_endpoints():
    # Run short benchmark summary
    res = client.get("/api/v1/benchmark/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "sample_evaluation" in data
    eval_metrics = data["sample_evaluation"]["metrics"]
    assert eval_metrics["courtroom_engine"]["accuracy"] > 0.0

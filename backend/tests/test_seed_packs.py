"""Tests for seeding workspace packs and loading 60-case benchmark."""
import os
import tempfile
import pytest
from app.db.database import get_db_context, init_db
from app.db.repository import Repository
from app.db.seed import load_benchmark_60, seed_workspace_pack


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_load_benchmark_60():
    benchmark_data = load_benchmark_60()
    assert "cases" in benchmark_data
    cases = benchmark_data["cases"]
    assert len(cases) == 60

    states = set(c["expected_state"] for c in cases)
    assert states == {"ANSWERABLE", "CONTRADICTION", "NOT_COVERED"}

    # Validate first case structure
    case_0 = cases[0]
    assert "id" in case_0
    assert "question" in case_0
    assert "expected_state" in case_0
    assert "expected_source_chunks" in case_0


def test_seed_startup_founder_legal_pack(temp_db):
    result = seed_workspace_pack("ws_startup", "startup_founder_legal", db_path=temp_db)
    assert result["workspace_id"] == "ws_startup"
    assert result["seeded_docs"] == 3
    assert result["seeded_clauses"] > 5

    with get_db_context(temp_db) as conn:
        repo = Repository(conn)
        docs = repo.list_documents("ws_startup")
        assert len(docs) == 3
        doc_titles = [d["title"] for d in docs]
        assert any("Founder Employment" in t for t in doc_titles)
        assert any("Ip And Invention" in t for t in doc_titles)
        assert any("Contractor And Sla" in t for t in doc_titles)

        clauses = repo.list_clauses(workspace_id="ws_startup")
        assert len(clauses) > 10


def test_seed_university_policy_pack(temp_db):
    result = seed_workspace_pack("ws_uni", "university_policy", db_path=temp_db)
    assert result["workspace_id"] == "ws_uni"
    assert result["seeded_docs"] >= 5

    with get_db_context(temp_db) as conn:
        repo = Repository(conn)
        docs = repo.list_documents("ws_uni")
        assert len(docs) >= 5

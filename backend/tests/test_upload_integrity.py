"""Tests for document upload integrity, workspace isolation, and deduplication."""
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


def test_upload_document_belongs_to_selected_workspace():
    """Verify uploaded documents strictly belong to the specified workspace."""
    client.get("/api/v1/workspaces")

    content = b"""# Supplementary Service Addendum
Section 1.1 Scope
The Contractor shall deliver engineering services.
Section 1.2 Confidentiality
All work product shall remain strictly confidential for 3 years.
"""
    file_payload = ("test_addendum.md", io.BytesIO(content), "text/markdown")

    res = client.post(
        "/api/v1/workspaces/ws_startup_legal/documents",
        files={"file": file_payload},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    doc_id = data["doc_id"]

    # Verify document exists in startup_legal graph
    graph_startup = client.get("/api/v1/workspaces/ws_startup_legal/graph").json()
    doc_startup_ids = [d["id"] for d in graph_startup["documents"]]
    assert doc_id in doc_startup_ids

    # Verify document does NOT exist in university_policy graph
    graph_uni = client.get("/api/v1/workspaces/ws_university_policy/graph").json()
    doc_uni_ids = [d["id"] for d in graph_uni["documents"]]
    assert doc_id not in doc_uni_ids


def test_graph_refresh_includes_new_document():
    """Verify the graph metrics and clause nodes update after document upload."""
    client.get("/api/v1/workspaces")

    graph_before = client.get("/api/v1/workspaces/ws_startup_legal/graph").json()
    count_before = graph_before["summary_metrics"]["total_documents"]

    new_content = b"""# Bonus Amendment
Section 9.1 Performance Incentive
A bonus of 15% shall be awarded upon product release.
"""
    file_payload = ("bonus_amendment.md", io.BytesIO(new_content), "text/markdown")
    res = client.post(
        "/api/v1/workspaces/ws_startup_legal/documents",
        files={"file": file_payload},
    )
    assert res.status_code == 200

    graph_after = client.get("/api/v1/workspaces/ws_startup_legal/graph").json()
    assert graph_after["summary_metrics"]["total_documents"] == count_before + 1
    # Verify clause node present
    found_clause = any(c.get("heading") == "Performance Incentive" for c in graph_after["clauses"])
    assert found_clause is True


def test_failed_upload_does_not_produce_false_success():
    """Verify empty or corrupt files return 400 error rather than false success."""
    client.get("/api/v1/workspaces")

    empty_payload = ("empty.txt", io.BytesIO(b"   \n\t  "), "text/plain")
    res = client.post(
        "/api/v1/workspaces/ws_startup_legal/documents",
        files={"file": empty_payload},
    )
    assert res.status_code == 400
    assert "no readable text" in res.json()["detail"].lower()


def test_content_hash_deduplication_and_workspace_isolation():
    """
    Verify content-hash deduplication requirements:
    - Same workspace and same content: identify duplicate (replaces without duplicating).
    - Same workspace and different content: retain both documents (even if same filename).
    - Different workspaces: retain independent copies.
    """
    client.get("/api/v1/workspaces")

    content_a = b"""# Non Disclosure Agreement Version A
Section 1.1 Term
The NDA lasts 2 years for commercial discussions.
"""
    file_payload_1 = ("nda.md", io.BytesIO(content_a), "text/markdown")
    res1 = client.post(
        "/api/v1/workspaces/ws_startup_legal/documents",
        files={"file": file_payload_1},
    )
    assert res1.status_code == 200
    doc_1_id = res1.json()["doc_id"]

    # 1. Same workspace and SAME content -> replaces previous document, count stays same
    file_payload_same = ("nda_copy.md", io.BytesIO(content_a), "text/markdown")
    res_same = client.post(
        "/api/v1/workspaces/ws_startup_legal/documents",
        files={"file": file_payload_same},
    )
    assert res_same.status_code == 200

    graph_after_same = client.get("/api/v1/workspaces/ws_startup_legal/graph").json()
    # The old doc should have been replaced
    assert not any(d["id"] == doc_1_id for d in graph_after_same["documents"])
    assert any(d["id"] == res_same.json()["doc_id"] for d in graph_after_same["documents"])

    count_after_same = graph_after_same["summary_metrics"]["total_documents"]

    # 2. Same workspace and DIFFERENT content -> retain both documents (even with same filename 'nda.md')
    content_b = b"""# Non Disclosure Agreement Version B
Section 1.1 Term
The NDA lasts 10 years with extended patent disclosures.
"""
    file_payload_diff = ("nda.md", io.BytesIO(content_b), "text/markdown")
    res_diff = client.post(
        "/api/v1/workspaces/ws_startup_legal/documents",
        files={"file": file_payload_diff},
    )
    assert res_diff.status_code == 200

    graph_after_diff = client.get("/api/v1/workspaces/ws_startup_legal/graph").json()
    assert graph_after_diff["summary_metrics"]["total_documents"] == count_after_same + 1
    # Both documents exist in ws_startup_legal
    doc_ids_startup = [d["id"] for d in graph_after_diff["documents"]]
    assert res_same.json()["doc_id"] in doc_ids_startup
    assert res_diff.json()["doc_id"] in doc_ids_startup

    # 3. Different workspace -> retain independent copy of content_a
    file_payload_other_ws = ("nda.md", io.BytesIO(content_a), "text/markdown")
    res_other = client.post(
        "/api/v1/workspaces/ws_university_policy/documents",
        files={"file": file_payload_other_ws},
    )
    assert res_other.status_code == 200
    other_doc_id = res_other.json()["doc_id"]

    graph_uni = client.get("/api/v1/workspaces/ws_university_policy/graph").json()
    doc_ids_uni = [d["id"] for d in graph_uni["documents"]]
    assert other_doc_id in doc_ids_uni
    # ws_startup_legal still has its documents intact
    graph_startup_final = client.get("/api/v1/workspaces/ws_startup_legal/graph").json()
    assert res_same.json()["doc_id"] in [d["id"] for d in graph_startup_final["documents"]]

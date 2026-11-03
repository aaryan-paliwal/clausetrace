"""Tests for document upload integrity, workspace isolation, and deduplication."""
import io
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


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


def test_repeated_upload_deduplication():
    """Verify repeated upload of the same document filename updates rather than duplicates records."""
    client.get("/api/v1/workspaces")

    content_v1 = b"""# Non Disclosure Agreement
Section 1.1 Term
The NDA lasts 2 years.
"""
    file_payload_1 = ("nda.md", io.BytesIO(content_v1), "text/markdown")
    res1 = client.post(
        "/api/v1/workspaces/ws_startup_legal/documents",
        files={"file": file_payload_1},
    )
    assert res1.status_code == 200

    graph_mid = client.get("/api/v1/workspaces/ws_startup_legal/graph").json()
    nda_docs_mid = [d for d in graph_mid["documents"] if d["filename"] == "nda.md"]
    assert len(nda_docs_mid) == 1
    mid_doc_count = graph_mid["summary_metrics"]["total_documents"]

    # Re-upload same filename with amended content
    content_v2 = b"""# Non Disclosure Agreement
Section 1.1 Term
The NDA lasts 5 years.
"""
    file_payload_2 = ("nda.md", io.BytesIO(content_v2), "text/markdown")
    res2 = client.post(
        "/api/v1/workspaces/ws_startup_legal/documents",
        files={"file": file_payload_2},
    )
    assert res2.status_code == 200

    graph_final = client.get("/api/v1/workspaces/ws_startup_legal/graph").json()
    nda_docs_final = [d for d in graph_final["documents"] if d["filename"] == "nda.md"]
    assert len(nda_docs_final) == 1
    # Total documents count should not increase on replacement
    assert graph_final["summary_metrics"]["total_documents"] == mid_doc_count

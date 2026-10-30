"""Tests for structural clause parser and graph-expanded hybrid retriever."""
import os
import tempfile
import pytest
from app.db.database import get_db_context, init_db
from app.db.repository import Repository
from app.engines.parser import extract_text_from_upload, parse_document_into_clauses
from app.engines.retrieval import HybridGraphRetriever, compute_embedding


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_parse_document_exact_char_offsets():
    raw_markdown = """# Employment Agreement

## 1. Term of Employment
The employment shall commence on January 1, 2025.

## 2. Termination Notice
Either party may terminate upon thirty (30) days prior written notice.

## 3. Confidentiality
Employee shall hold all trade secrets in strict confidence.
"""
    clauses = parse_document_into_clauses(
        doc_id="doc_test",
        workspace_id="ws_test",
        raw_text=raw_markdown,
    )

    assert len(clauses) >= 3

    # CRITICAL: Verify raw_text[char_start:char_end] == clause['text']
    for clause in clauses:
        start = clause["char_start"]
        end = clause["char_end"]
        extracted_text = raw_markdown[start:end]
        assert extracted_text == clause["text"], f"Offset mismatch in clause {clause['id']}"


def test_extract_text_from_upload_markdown():
    content = b"# Legal Notice\nThis is a sample plain markdown document."
    extracted = extract_text_from_upload("test.md", content)
    assert "Legal Notice" in extracted
    assert "sample plain markdown" in extracted


def test_compute_embedding_vector_properties():
    emb1 = compute_embedding("The company shall provide 30 days termination notice.")
    emb2 = compute_embedding("Termination notice of 30 days is required by employer.")
    emb3 = compute_embedding("Student physical attendance must exceed seventy-five percent.")

    assert len(emb1) == 256
    assert len(emb2) == 256

    # Verify cosine similarity is higher between similar legal clauses
    from app.engines.retrieval import _cosine_similarity
    sim_1_2 = _cosine_similarity(emb1, emb2)
    sim_1_3 = _cosine_similarity(emb1, emb3)
    assert sim_1_2 > sim_1_3


def test_hybrid_retriever_with_graph_expansion(temp_db):
    with get_db_context(temp_db) as conn:
        repo = Repository(conn)
        repo.create_workspace("ws_test", "Test Workspace")
        repo.create_document("doc_1", "ws_test", "Employment", "emp.md", "...")

        # Clause A: Notice requirement
        cl_a = repo.create_clause(
            clause_id="cl_a",
            doc_id="doc_1",
            workspace_id="ws_test",
            section_number="2.1",
            heading="Notice",
            text="The Company shall provide 30 days written notice before termination.",
            char_start=0,
            char_end=70,
            embedding=compute_embedding("The Company shall provide 30 days written notice before termination."),
        )

        # Clause B: Override/Addendum immediate termination (different words, but linked conflict)
        cl_b = repo.create_clause(
            clause_id="cl_b",
            doc_id="doc_1",
            workspace_id="ws_test",
            section_number="9.4",
            heading="Addendum Default",
            text="Immediate cancellation occurs upon any delivery milestone default.",
            char_start=71,
            char_end=140,
            embedding=compute_embedding("Immediate cancellation occurs upon any delivery milestone default."),
        )

        # Link A and B via conflict
        repo.create_deontic_rule(
            rule_id="r_a", clause_id="cl_a", doc_id="doc_1", workspace_id="ws_test",
            subject="Company", modality="MUST", action_category="TERMINATION",
            action_summary="Provide 30 days notice", conditions=[], exceptions=[],
            exact_quote="30 days written notice",
        )
        repo.create_deontic_rule(
            rule_id="r_b", clause_id="cl_b", doc_id="doc_1", workspace_id="ws_test",
            subject="Company", modality="MAY", action_category="TERMINATION",
            action_summary="Immediate cancellation", conditions=[], exceptions=[],
            is_override=True, exact_quote="Immediate cancellation occurs",
        )
        repo.create_conflict(
            conflict_id="conf_1", workspace_id="ws_test", rule_a_id="r_a", rule_b_id="r_b",
            clause_a_id="cl_a", clause_b_id="cl_b", conflict_type="DIRECT_MODALITY_CLASH",
            severity="HIGH", collision_axis="notice_duration", explanation="Direct collision",
        )

    retriever = HybridGraphRetriever(db_path=temp_db)
    # Query matching only Clause A's terminology
    results = retriever.retrieve("ws_test", "What is the required notice period for termination?", top_k=1, enable_graph_expansion=True)

    clause_ids = [r["id"] for r in results]
    assert "cl_a" in clause_ids
    # 1-hop graph expansion should pull cl_b because of the active conflict
    assert "cl_b" in clause_ids

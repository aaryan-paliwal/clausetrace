"""Tests for deterministic document-grounded evidence validation."""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import get_db_context
from app.db.repository import Repository
from app.engines.courtroom import AdversarialCourtroomEngine
from app.llm.schemas import DocumentFinding, FindingCategory

client = TestClient(app)


@pytest.fixture
def seeded_workspace():
    """Ensure startup legal is seeded and retrieve a valid document and clause."""
    client.get("/api/v1/workspaces")
    with get_db_context() as conn:
        repo = Repository(conn)
        docs = repo.list_documents("ws_startup_legal")
        assert len(docs) > 0
        doc = docs[0]
        clauses = repo.list_clauses(doc_id=doc["id"])
        assert len(clauses) > 0
        clause = clauses[0]
        return doc, clause


def test_valid_direct_document_evidence(seeded_workspace):
    """Verify that accurate document ID, clause ID, offsets, and exact quote pass validation."""
    doc, clause = seeded_workspace
    engine = AdversarialCourtroomEngine()

    raw_text = doc["raw_text"]
    char_start = clause["char_start"]
    char_end = min(clause["char_end"], char_start + 50)
    exact_quote = raw_text[char_start:char_end]

    valid_finding = DocumentFinding(
        category=FindingCategory.DIRECT_DOCUMENT_EVIDENCE,
        statement="Direct evidence of employment terms.",
        clause_id=clause["id"],
        doc_id=doc["id"],
        char_start=char_start,
        char_end=char_end,
        evidence_quote=exact_quote,
    )

    sanitized = engine.validate_and_sanitize_findings("ws_startup_legal", [valid_finding])
    assert len(sanitized) == 1
    assert sanitized[0].category == FindingCategory.DIRECT_DOCUMENT_EVIDENCE
    assert sanitized[0].evidence_quote == exact_quote
    assert sanitized[0].doc_id == doc["id"]
    assert sanitized[0].clause_id == clause["id"]


def test_incorrect_offsets_demoted(seeded_workspace):
    """Verify that findings with character offsets out of bounds or invalid range are demoted."""
    doc, clause = seeded_workspace
    engine = AdversarialCourtroomEngine()

    finding_out_of_bounds = DocumentFinding(
        category=FindingCategory.DIRECT_DOCUMENT_EVIDENCE,
        statement="Claim with out of bounds offsets.",
        clause_id=clause["id"],
        doc_id=doc["id"],
        char_start=999999,
        char_end=1000050,
        evidence_quote="Some quote",
    )

    finding_inverted_offsets = DocumentFinding(
        category=FindingCategory.DIRECT_DOCUMENT_EVIDENCE,
        statement="Claim with inverted offsets.",
        clause_id=clause["id"],
        doc_id=doc["id"],
        char_start=50,
        char_end=10,
        evidence_quote="Some quote",
    )

    sanitized = engine.validate_and_sanitize_findings(
        "ws_startup_legal", [finding_out_of_bounds, finding_inverted_offsets]
    )
    assert len(sanitized) == 2
    assert sanitized[0].category == FindingCategory.UNSUPPORTED_CONCLUSION
    assert sanitized[1].category == FindingCategory.UNSUPPORTED_CONCLUSION


def test_fabricated_quotation_demoted(seeded_workspace):
    """Verify that findings where the quote does not match the original document substring are demoted."""
    doc, clause = seeded_workspace
    engine = AdversarialCourtroomEngine()

    char_start = clause["char_start"]
    char_end = min(clause["char_end"], char_start + 40)

    finding_fabricated = DocumentFinding(
        category=FindingCategory.DIRECT_DOCUMENT_EVIDENCE,
        statement="Claim with fabricated text.",
        clause_id=clause["id"],
        doc_id=doc["id"],
        char_start=char_start,
        char_end=char_end,
        evidence_quote="THIS FABRICATED SENTENCE DOES NOT EXIST IN THE DOCUMENT",
    )

    sanitized = engine.validate_and_sanitize_findings("ws_startup_legal", [finding_fabricated])
    assert len(sanitized) == 1
    assert sanitized[0].category == FindingCategory.UNSUPPORTED_CONCLUSION


def test_nonexistent_document_id_demoted(seeded_workspace):
    """Verify that findings referencing an unknown doc_id are demoted to UNSUPPORTED_CONCLUSION."""
    doc, clause = seeded_workspace
    engine = AdversarialCourtroomEngine()

    finding_ghost_doc = DocumentFinding(
        category=FindingCategory.DIRECT_DOCUMENT_EVIDENCE,
        statement="Claim referencing phantom document.",
        clause_id=clause["id"],
        doc_id="doc_phantom_99999",
        char_start=0,
        char_end=20,
        evidence_quote="Some text",
    )

    sanitized = engine.validate_and_sanitize_findings("ws_startup_legal", [finding_ghost_doc])
    assert len(sanitized) == 1
    assert sanitized[0].category == FindingCategory.UNSUPPORTED_CONCLUSION


def test_nonexistent_clause_id_demoted(seeded_workspace):
    """Verify that findings referencing a nonexistent clause_id are demoted to UNSUPPORTED_CONCLUSION."""
    doc, clause = seeded_workspace
    engine = AdversarialCourtroomEngine()

    finding_ghost_clause = DocumentFinding(
        category=FindingCategory.DIRECT_DOCUMENT_EVIDENCE,
        statement="Claim referencing nonexistent clause.",
        clause_id="clause_phantom_99999",
        doc_id=doc["id"],
        char_start=0,
        char_end=20,
        evidence_quote="Some text",
    )

    sanitized = engine.validate_and_sanitize_findings("ws_startup_legal", [finding_ghost_clause])
    assert len(sanitized) == 1
    assert sanitized[0].category == FindingCategory.UNSUPPORTED_CONCLUSION


def test_unsupported_conclusions_remain_classified():
    """Verify that explicit UNSUPPORTED_CONCLUSION findings remain explicitly classified as unsupported."""
    engine = AdversarialCourtroomEngine()

    unsupported_finding = DocumentFinding(
        category=FindingCategory.UNSUPPORTED_CONCLUSION,
        statement="Statutory penalty under section 42 of unverified code.",
    )

    sanitized = engine.validate_and_sanitize_findings("ws_startup_legal", [unsupported_finding])
    assert len(sanitized) == 1
    assert sanitized[0].category == FindingCategory.UNSUPPORTED_CONCLUSION


def test_inference_from_evidence_validation(seeded_workspace):
    """Verify that INFERENCE_FROM_EVIDENCE requires valid doc and clause references."""
    doc, clause = seeded_workspace
    engine = AdversarialCourtroomEngine()

    # Valid inference
    valid_inference = DocumentFinding(
        category=FindingCategory.INFERENCE_FROM_EVIDENCE,
        statement="Termination right inferred from covenant structure.",
        doc_id=doc["id"],
        clause_id=clause["id"],
    )
    res_valid = engine.validate_and_sanitize_findings("ws_startup_legal", [valid_inference])
    assert res_valid[0].category == FindingCategory.INFERENCE_FROM_EVIDENCE
    assert res_valid[0].doc_id == doc["id"]

    # Invalid inference with bogus clause -> demoted to UNSUPPORTED_CONCLUSION
    invalid_inference = DocumentFinding(
        category=FindingCategory.INFERENCE_FROM_EVIDENCE,
        statement="Speculative conclusion without real clause backing.",
        doc_id=doc["id"],
        clause_id="bogus_clause_123",
    )
    res_invalid = engine.validate_and_sanitize_findings("ws_startup_legal", [invalid_inference])
    assert res_invalid[0].category == FindingCategory.UNSUPPORTED_CONCLUSION


def test_potential_conflict_validation(seeded_workspace):
    """Verify that POTENTIAL_CONFLICT validates clause references when provided."""
    doc, clause = seeded_workspace
    engine = AdversarialCourtroomEngine()

    # Valid conflict reference
    valid_conflict = DocumentFinding(
        category=FindingCategory.POTENTIAL_CONFLICT,
        statement="Conflict between notice periods.",
        doc_id=doc["id"],
        clause_id=clause["id"],
    )
    res_valid = engine.validate_and_sanitize_findings("ws_startup_legal", [valid_conflict])
    assert res_valid[0].category == FindingCategory.POTENTIAL_CONFLICT

    # Invalid conflict reference with bogus doc -> demoted
    invalid_conflict = DocumentFinding(
        category=FindingCategory.POTENTIAL_CONFLICT,
        statement="Alleged conflict in unknown document.",
        doc_id="bogus_doc_xyz",
    )
    res_invalid = engine.validate_and_sanitize_findings("ws_startup_legal", [invalid_conflict])
    assert res_invalid[0].category == FindingCategory.UNSUPPORTED_CONCLUSION


def test_missing_information_strips_fabricated_sources(seeded_workspace):
    """Verify that MISSING_INFORMATION findings do not retain fabricated source references."""
    doc, clause = seeded_workspace
    engine = AdversarialCourtroomEngine()

    missing_with_fake_source = DocumentFinding(
        category=FindingCategory.MISSING_INFORMATION,
        statement="Cure period not defined.",
        doc_id=doc["id"],
        clause_id=clause["id"],
        char_start=0,
        evidence_quote="Fake quote",
    )
    res = engine.validate_and_sanitize_findings("ws_startup_legal", [missing_with_fake_source])
    assert res[0].category == FindingCategory.MISSING_INFORMATION
    assert res[0].doc_id is None
    assert res[0].clause_id is None
    assert res[0].evidence_quote is None

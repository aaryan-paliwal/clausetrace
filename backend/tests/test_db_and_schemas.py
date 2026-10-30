"""Tests for SQLite WAL persistence and deontic schemas."""
import os
import tempfile
import pytest
from app.db.database import get_db_context, init_db
from app.db.repository import Repository
from app.llm.schemas import (
    ActionCategory,
    ConflictType,
    DeonticModality,
    ExtractedDeonticRule,
    ExtractedRuleList,
    PairwiseConflictAudit,
    VerdictState,
    CitationSpan,
    AgentBrief,
    CourtroomVerdict,
    CounterfactualPatchResult,
)


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_pydantic_schemas_validation():
    rule = ExtractedDeonticRule(
        subject="Employee",
        modality=DeonticModality.MUST_NOT,
        action_category=ActionCategory.CONFIDENTIALITY,
        action_summary="Disclose proprietary trade secrets",
        conditions=["During employment", "For 2 years post termination"],
        exceptions=["Authorized in writing by CEO"],
        is_override=False,
        temporal_scope="2 years",
        numeric_constraint=None,
        exact_quote="Employee must not disclose any proprietary trade secrets.",
    )
    assert rule.modality == DeonticModality.MUST_NOT
    assert rule.action_category == ActionCategory.CONFIDENTIALITY

    rule_list = ExtractedRuleList(rules=[rule])
    assert len(rule_list.rules) == 1

    audit = PairwiseConflictAudit(
        has_conflict=True,
        conflict_type=ConflictType.DIRECT_MODALITY_CLASH,
        severity="HIGH",
        collision_axis="notice_period",
        reasoning="Rule A requires 30 days while Rule B allows immediate termination without notice.",
        winning_rule_id=None,
    )
    assert audit.has_conflict is True
    assert audit.conflict_type == ConflictType.DIRECT_MODALITY_CLASH

    citation = CitationSpan(
        clause_id="clause_001",
        doc_id="doc_001",
        doc_title="Founder Employment Agreement",
        section_number="4.2",
        verbatim_quote="Either party may terminate upon 30 days written notice.",
        char_start=120,
        char_end=178,
    )
    assert citation.section_number == "4.2"

    advocate = AgentBrief(
        agent_role="Prosecutor",
        thesis="Immediate termination breached section 4.2 notice rights",
        arguments=["No cure period was extended", "Notice requirement is non-waivable"],
        cited_clause_ids=["clause_001"],
        flagged_gaps_or_undefined_terms=[],
    )
    skeptic = AgentBrief(
        agent_role="Defense",
        thesis="Addendum overrides employment agreement",
        arguments=["Addendum was signed later in time"],
        cited_clause_ids=["clause_002"],
        flagged_gaps_or_undefined_terms=["Critical Deliverable Breach"],
    )

    verdict = CourtroomVerdict(
        verdict_state=VerdictState.CONTRADICTION,
        benchmark_compat_state="CONTRADICTION",
        confidence_score=0.95,
        executive_ruling="Irreconcilable conflict between baseline notice and immediate termination addendum.",
        advocate_brief=advocate,
        skeptic_brief=skeptic,
        missing_prerequisites=[],
        verified_citations=[citation],
    )
    assert verdict.verdict_state == VerdictState.CONTRADICTION

    patch = CounterfactualPatchResult(
        conflict_id="conf_001",
        target_clause_id="clause_002",
        exploit_actor="Employer",
        exploit_scenario="Forfeiture of unvested equity via immediate bad-faith termination",
        financial_or_legal_impact="Total loss of 25% equity stake without cure opportunity",
        original_text="Client may terminate immediately for cause.",
        patched_text="Client may terminate upon 15 business days notice with opportunity to cure.",
        rationale="Harmonizes with Employment Agreement cure provisions.",
        verification_passed=True,
        initial_conflicts=1,
        remaining_conflicts=0,
    )
    assert patch.verification_passed is True


def test_sqlite_repository_crud_lifecycle(temp_db):
    with get_db_context(temp_db) as conn:
        repo = Repository(conn)

        # 1. Workspace
        ws = repo.create_workspace("ws_test", "Test Workspace", "Testing SQLite CRUD", "startup_founder_legal")
        assert ws["id"] == "ws_test"
        assert ws["name"] == "Test Workspace"
        assert len(repo.list_workspaces()) == 1

        # 2. Document
        doc = repo.create_document(
            doc_id="doc_1",
            workspace_id="ws_test",
            title="Founder Agreement",
            filename="01_founder.md",
            raw_text="Sample raw contract text here.",
            doc_type="contract",
            authority_rank=1,
        )
        assert doc["id"] == "doc_1"
        assert doc["workspace_id"] == "ws_test"
        assert len(repo.list_documents("ws_test")) == 1

        # 3. Clause
        clause = repo.create_clause(
            clause_id="cl_1",
            doc_id="doc_1",
            workspace_id="ws_test",
            section_number="3.1",
            heading="Termination Notice",
            text="Either party may terminate upon 30 days notice.",
            char_start=0,
            char_end=48,
            embedding=[0.1, 0.2, 0.3],
        )
        assert clause["id"] == "cl_1"
        assert len(repo.list_clauses(workspace_id="ws_test")) == 1

        # 4. Deontic Rule
        rule = repo.create_deontic_rule(
            rule_id="r_1",
            clause_id="cl_1",
            doc_id="doc_1",
            workspace_id="ws_test",
            subject="Either party",
            modality=DeonticModality.MAY.value,
            action_category=ActionCategory.TERMINATION.value,
            action_summary="Terminate agreement upon notice",
            conditions=["Written notice delivered"],
            exceptions=[],
            is_override=False,
            temporal_scope="30 days",
            numeric_constraint="30",
            exact_quote="Either party may terminate upon 30 days notice.",
            char_start=0,
            char_end=48,
        )
        assert rule["id"] == "r_1"
        assert rule["conditions"] == ["Written notice delivered"]
        assert len(repo.list_deontic_rules(workspace_id="ws_test")) == 1

        rule2 = repo.create_deontic_rule(
            rule_id="r_2",
            clause_id="cl_1",
            doc_id="doc_1",
            workspace_id="ws_test",
            subject="Company",
            modality=DeonticModality.MUST_NOT.value,
            action_category=ActionCategory.TERMINATION.value,
            action_summary="Terminate without notice",
            conditions=[],
            exceptions=[],
            is_override=False,
            exact_quote="Company must not terminate without notice.",
        )
        assert rule2["id"] == "r_2"

        # 5. Conflict
        conflict = repo.create_conflict(
            conflict_id="conf_1",
            workspace_id="ws_test",
            rule_a_id="r_1",
            rule_b_id="r_2",
            clause_a_id="cl_1",
            clause_b_id="cl_1",
            conflict_type=ConflictType.DIRECT_MODALITY_CLASH.value,
            severity="HIGH",
            collision_axis="notice_duration",
            explanation="Modality clash on notice requirements",
        )
        assert conflict["id"] == "conf_1"
        assert len(repo.list_conflicts("ws_test")) == 1

        # 6. Patch
        patch = repo.create_patch(
            patch_id="patch_1",
            conflict_id="conf_1",
            target_clause_id="cl_1",
            exploit_actor="Company",
            exploit_scenario="Immediate firing",
            financial_or_legal_impact="Loss of equity",
            original_text="Either party may terminate upon 30 days notice.",
            patched_text="Either party may terminate upon 30 days notice with written cure period.",
            rationale="Clarify notice and cure period.",
            verification_passed=True,
            remaining_conflicts=0,
        )
        assert patch["id"] == "patch_1"
        assert patch["verification_passed"] is True
        assert len(repo.list_patches("conf_1")) == 1

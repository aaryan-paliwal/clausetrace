"""Tests for the 3-Agent Adversarial Courtroom Engine."""
import os
import tempfile
import pytest
from app.db.database import init_db
from app.db.seed import seed_workspace_pack
from app.engines.courtroom import AdversarialCourtroomEngine
from app.engines.deontic_compiler import DeonticRuleGraphCompiler
from app.llm.schemas import VerdictState


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.mark.asyncio
async def test_courtroom_verdicts(temp_db):
    # Seed startup founder legal and compile
    seed_workspace_pack("ws_startup", "startup_founder_legal", db_path=temp_db)
    compiler = DeonticRuleGraphCompiler(db_path=temp_db)
    await compiler.compile_workspace("ws_startup")

    courtroom = AdversarialCourtroomEngine(db_path=temp_db)

    # 1. Test Contradiction / Conflict outcome on notice & cure
    v_contra = await courtroom.evaluate_query(
        workspace_id="ws_startup",
        query="Can the company immediately terminate employment without notice or cure upon a missed milestone?",
    )
    assert v_contra.verdict_state in [VerdictState.CONTRADICTION, VerdictState.EXPLOITABLE_LOOPHOLE]
    assert v_contra.advocate_brief is not None
    assert v_contra.skeptic_brief is not None
    assert len(v_contra.verified_citations) > 0

    # 2. Test Exploitable Loophole outcome on Critical Deliverable Breach
    v_loophole = await courtroom.evaluate_query(
        workspace_id="ws_startup",
        query="What defines a Critical Deliverable Breach that triggers termination?",
    )
    assert v_loophole.verdict_state in [VerdictState.EXPLOITABLE_LOOPHOLE, VerdictState.CONTRADICTION]

    # 3. Test Answerable outcome on base salary
    v_ans = await courtroom.evaluate_query(
        workspace_id="ws_startup",
        query="What is the base salary of the Executive?",
    )
    assert v_ans.verdict_state == VerdictState.ANSWERABLE
    assert v_ans.confidence_score > 0.7

    # 4. Test Not Covered outcome on out-of-scope query
    v_not_covered = await courtroom.evaluate_query(
        workspace_id="ws_startup",
        query="Can employees bring dogs and pets into the office cafeteria?",
    )
    assert v_not_covered.verdict_state == VerdictState.NOT_COVERED
    assert v_not_covered.benchmark_compat_state == "NOT_COVERED"
    assert len(v_not_covered.verified_citations) == 0


@pytest.mark.asyncio
async def test_courtroom_sse_streaming(temp_db):
    seed_workspace_pack("ws_startup", "startup_founder_legal", db_path=temp_db)
    courtroom = AdversarialCourtroomEngine(db_path=temp_db)

    events = []
    async for event in courtroom.stream_courtroom_events("ws_startup", "What is the Executive salary?"):
        events.append(event)

    assert len(events) >= 3
    assert any("event: retrieval" in e for e in events)
    assert any("event: verdict" in e for e in events)

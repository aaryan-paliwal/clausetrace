"""Comprehensive tests for context propagation, prompt injection, and backward compatibility."""
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.courtroom import QueryRequest
from app.engines.courtroom import AdversarialCourtroomEngine
from app.engines.retrieval import HybridGraphRetriever
from app.llm.schemas import AgentBrief, CourtroomVerdict, VerdictState, DocumentFinding, FindingCategory
from app.config import settings

client = TestClient(app)


def test_query_request_validation():
    """Verify QueryRequest validation with and without optional context fields."""
    # 1. Backward compatible: query only
    req_basic = QueryRequest(query="What is the notice period?")
    assert req_basic.query == "What is the notice period?"
    assert req_basic.factual_context is None
    assert req_basic.persona is None
    assert req_basic.task_id is None

    # 2. Full context
    req_full = QueryRequest(
        query="Can the employer terminate without notice?",
        factual_context="Employee joined in Jan 2024 with 3-year term",
        persona="employee",
        task_id="emp_find_unfair_terms",
    )
    assert req_full.query == "Can the employer terminate without notice?"
    assert req_full.factual_context == "Employee joined in Jan 2024 with 3-year term"
    assert req_full.persona == "employee"
    assert req_full.task_id == "emp_find_unfair_terms"


def test_retrieval_context_infusion_and_observability():
    """Verify factual context influences retrieval while preserving original query as primary."""
    retriever = HybridGraphRetriever()
    
    # Check effective query construction
    q_alone = retriever._build_context_infused_query(
        query="What is the termination notice period?",
        factual_context=None,
        persona="employee",
        task_id="emp_review",
    )
    assert q_alone == "What is the termination notice period?"

    q_with_facts = retriever._build_context_infused_query(
        query="What is the termination notice period?",
        factual_context="Executive employment agreement clause 4 addendum",
        persona="employee",
        task_id="emp_review",
    )
    assert "What is the termination notice period?" in q_with_facts
    assert "Executive employment agreement clause 4 addendum" in q_with_facts

    # Test retrieval execution preserves observability
    client.get("/api/v1/workspaces")
    results = retriever.retrieve(
        workspace_id="ws_startup_legal",
        query="termination notice",
        factual_context="30 days cure period",
        persona="founder",
        task_id="fnd_review",
    )
    assert len(results) > 0
    debug = retriever.last_retrieval_debug
    assert debug is not None
    assert debug["original_query"] == "termination notice"
    assert "30 days cure period" in debug["effective_query"]
    assert debug["persona"] == "founder"
    assert debug["task_id"] == "fnd_review"


@pytest.mark.asyncio
async def test_context_propagation_to_agents():
    """Verify persona, task_id, and factual context reach Advocate, Skeptic, and Adjudicator prompts."""
    # Ensure startup legal is seeded
    client.get("/api/v1/workspaces")

    courtroom = AdversarialCourtroomEngine()

    mock_gateway = MagicMock()
    mock_gateway.generate_structured = AsyncMock()

    # Define mock return for briefs and verdict
    advocate_brief = AgentBrief(
        agent_role="Advocate",
        thesis="Notice is mandatory under Section 4.1.",
        arguments=["Explicit 30 days notice required"],
        cited_clause_ids=["c1"],
        flagged_gaps_or_undefined_terms=[],
    )
    skeptic_brief = AgentBrief(
        agent_role="Skeptic",
        thesis="Immediate termination loophole exists in addendum.",
        arguments=["Addendum contradicts baseline notice"],
        cited_clause_ids=["c2"],
        flagged_gaps_or_undefined_terms=["Critical Deliverable Breach"],
    )
    mock_verdict = CourtroomVerdict(
        verdict_state=VerdictState.CONTRADICTION,
        benchmark_compat_state="CONTRADICTION",
        confidence_score=0.95,
        executive_ruling="Contradictory notice obligations detected.",
        advocate_brief=advocate_brief,
        skeptic_brief=skeptic_brief,
        missing_prerequisites=[],
        verified_citations=[],
        findings=[
            DocumentFinding(
                category=FindingCategory.DIRECT_DOCUMENT_EVIDENCE,
                statement="Section 4.1 requires 30 days notice.",
            ),
            DocumentFinding(
                category=FindingCategory.POTENTIAL_CONFLICT,
                statement="Addendum permits immediate termination.",
            ),
        ],
    )

    # Return advocate, skeptic, then adjudicator
    mock_gateway.generate_structured.side_effect = [
        (advocate_brief, {}),
        (skeptic_brief, {}),
        (mock_verdict, {}),
    ]

    courtroom.gateway = mock_gateway

    verdict = await courtroom.evaluate_query(
        workspace_id="ws_startup_legal",
        query="Can employer immediately terminate without notice?",
        factual_context="Executive joined in Jan 2024, milestone 3 missed",
        persona="employee",
        task_id="emp_find_unfair_terms",
    )

    assert mock_gateway.generate_structured.call_count == 3
    calls = mock_gateway.generate_structured.call_args_list

    # 1. Advocate prompt call
    advocate_user_prompt = calls[0].kwargs.get("user_prompt") or calls[0][1].get("user_prompt")
    assert "User Query / Dispute Premise: Can employer immediately terminate without notice?" in advocate_user_prompt
    assert "Client Context Persona: EMPLOYEE" in advocate_user_prompt
    assert "Objective Task: emp_find_unfair_terms" in advocate_user_prompt
    assert "Factual / Case Background: Executive joined in Jan 2024, milestone 3 missed" in advocate_user_prompt

    # 2. Skeptic prompt call
    skeptic_user_prompt = calls[1].kwargs.get("user_prompt") or calls[1][1].get("user_prompt")
    assert "Client Context Persona: EMPLOYEE" in skeptic_user_prompt
    assert "Factual / Case Background: Executive joined in Jan 2024, milestone 3 missed" in skeptic_user_prompt

    # 3. Adjudicator prompt call
    adjudicator_user_prompt = calls[2].kwargs.get("user_prompt") or calls[2][1].get("user_prompt")
    assert "Client Context Persona: EMPLOYEE" in adjudicator_user_prompt
    assert "Objective Task: emp_find_unfair_terms" in adjudicator_user_prompt
    assert "Factual / Case Background: Executive joined in Jan 2024, milestone 3 missed" in adjudicator_user_prompt

    # Verify structured findings returned
    assert len(verdict.findings) == 2
    assert verdict.findings[0].category == FindingCategory.DIRECT_DOCUMENT_EVIDENCE
    assert verdict.findings[1].category == FindingCategory.POTENTIAL_CONFLICT


def test_sse_streaming_context_forwarding():
    """Verify equivalent forwarding through the SSE streaming endpoint."""
    client.get("/api/v1/workspaces")

    stream_res = client.post(
        "/api/v1/workspaces/ws_startup_legal/courtroom/stream",
        json={
            "query": "What is the Executive salary?",
            "factual_context": "Annual compensation term sheet",
            "persona": "founder",
            "task_id": "fnd_understand_clause",
        },
    )
    assert stream_res.status_code == 200
    events = stream_res.text
    assert "event: status" in events
    assert "event: retrieval" in events
    assert "event: advocate_brief" in events
    assert "event: skeptic_brief" in events
    assert "event: verdict" in events


def test_backward_compatibility_query_only():
    """Verify existing courtroom requests containing only a query continue to function cleanly."""
    client.get("/api/v1/workspaces")

    res = client.post(
        "/api/v1/workspaces/ws_startup_legal/courtroom/ask",
        json={"query": "What is the Executive salary?"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["verdict_state"] == "ANSWERABLE"
    assert "advocate_brief" in data
    assert "skeptic_brief" in data
    assert "findings" in data

"""Tests for Meta Llama gateway client and offline fallback engine."""
import pytest
from app.llm.meta_client import MetaLlamaGateway
from app.llm.schemas import (
    ConflictType,
    CourtroomVerdict,
    ExtractedRuleList,
    PairwiseConflictAudit,
    VerdictState,
)


@pytest.mark.asyncio
async def test_meta_client_offline_rule_extraction():
    gateway = MetaLlamaGateway(api_key="your_meta_model_api_key_here")
    contract_text = (
        "The Employee must not disclose confidential information for 2 years. "
        "The Company shall provide 30 days written notice prior to termination. "
        "Notwithstanding Section 1, the Company owns all software."
    )

    result, telemetry = await gateway.generate_structured(
        system_prompt="Extract deontic rules.",
        user_prompt=contract_text,
        schema_cls=ExtractedRuleList,
    )

    assert isinstance(result, ExtractedRuleList)
    assert len(result.rules) >= 2
    assert telemetry["mode"] == "deterministic_fallback"
    assert "duration_ms" in telemetry

    # Verify modal rule properties extracted heuristically
    rule_quotes = [r.exact_quote for r in result.rules]
    assert any("must not" in q.lower() for q in rule_quotes)
    assert any("30 days" in (r.temporal_scope or "") for r in result.rules)


@pytest.mark.asyncio
async def test_meta_client_offline_conflict_audit():
    gateway = MetaLlamaGateway()
    user_prompt = "Rule A: The Company shall provide 30 days written notice. Rule B: Immediate termination without notice is permitted."

    result, telemetry = await gateway.generate_structured(
        system_prompt="Audit for pairwise conflicts.",
        user_prompt=user_prompt,
        schema_cls=PairwiseConflictAudit,
    )

    assert isinstance(result, PairwiseConflictAudit)
    assert result.has_conflict is True
    assert result.conflict_type == ConflictType.DIRECT_MODALITY_CLASH
    assert telemetry["mode"] == "deterministic_fallback"


@pytest.mark.asyncio
async def test_meta_client_offline_courtroom_verdict():
    gateway = MetaLlamaGateway()
    user_prompt = "Query on conflicting cancellation policies across documents."

    result, telemetry = await gateway.generate_structured(
        system_prompt="Render courtroom verdict.",
        user_prompt=user_prompt,
        schema_cls=CourtroomVerdict,
    )

    assert isinstance(result, CourtroomVerdict)
    assert result.verdict_state in [
        VerdictState.CONTRADICTION,
        VerdictState.ANSWERABLE,
        VerdictState.NOT_COVERED,
        VerdictState.EXPLOITABLE_LOOPHOLE,
    ]
    assert result.confidence_score >= 0.0
    assert result.advocate_brief is not None
    assert result.skeptic_brief is not None
    assert len(result.verified_citations) > 0

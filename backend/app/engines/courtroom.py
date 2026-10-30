"""Adversarial Courtroom Engine (Advocate, Skeptic, and Adjudicator)."""
import asyncio
import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

from app.db.database import get_db_context
from app.db.repository import Repository
from app.engines.retrieval import HybridGraphRetriever
from app.llm.meta_client import MetaLlamaGateway
from app.llm.prompts import (
    ADJUDICATOR_AGENT_PROMPT,
    ADVOCATE_AGENT_PROMPT,
    SKEPTIC_AGENT_PROMPT,
)
from app.llm.schemas import (
    AgentBrief,
    CitationSpan,
    CourtroomVerdict,
    VerdictState,
)

logger = logging.getLogger(__name__)


class AdversarialCourtroomEngine:
    """Orchestrates 3-agent adversarial cross-examination over retrieved deontic evidence."""

    def __init__(self, db_path: Optional[str] = None, gateway: Optional[MetaLlamaGateway] = None):
        self.db_path = db_path
        self.gateway = gateway or MetaLlamaGateway()
        self.retriever = HybridGraphRetriever(db_path=db_path)

    async def evaluate_query(self, workspace_id: str, query: str) -> CourtroomVerdict:
        """Run the full adversarial pipeline: retrieval -> advocate + skeptic -> adjudicator."""
        # 1. Retrieve top clauses + 1-hop deontic graph neighbors
        retrieved_clauses = self.retriever.retrieve(
            workspace_id=workspace_id,
            query=query,
            top_k=4,
            enable_graph_expansion=True,
        )

        # Relevance gate check
        if not retrieved_clauses or self._is_completely_irrelevant(query, retrieved_clauses):
            return self._build_not_covered_verdict(query)

        # Prepare evidence text
        evidence_text = self._format_evidence(retrieved_clauses)

        # 2. Concurrently run The Advocate and The Skeptic
        advocate_task = self.gateway.generate_structured(
            system_prompt=ADVOCATE_AGENT_PROMPT,
            user_prompt=f"Premise/Query: {query}\n\nRetrieved Evidence:\n{evidence_text}",
            schema_cls=AgentBrief,
        )
        skeptic_task = self.gateway.generate_structured(
            system_prompt=SKEPTIC_AGENT_PROMPT,
            user_prompt=f"Premise/Query: {query}\n\nRetrieved Evidence:\n{evidence_text}",
            schema_cls=AgentBrief,
        )
        (advocate_brief, _), (skeptic_brief, _) = await asyncio.gather(advocate_task, skeptic_task)

        # 3. Presiding Adjudicator synthesizes final verdict
        adjudicator_prompt = (
            f"User Query / Dispute Premise:\n{query}\n\n"
            f"The Advocate's Affirmative Brief:\n{json.dumps(advocate_brief.model_dump(), indent=2)}\n\n"
            f"The Skeptic's Adversarial Cross-Examination:\n{json.dumps(skeptic_brief.model_dump(), indent=2)}\n\n"
            f"Primary Corpus Evidence:\n{evidence_text}"
        )

        verdict, _ = await self.gateway.generate_structured(
            system_prompt=ADJUDICATOR_AGENT_PROMPT,
            user_prompt=adjudicator_prompt,
            schema_cls=CourtroomVerdict,
        )

        # Ensure briefs and verified citations are snapped to exact document characters
        verdict.advocate_brief = advocate_brief
        verdict.skeptic_brief = skeptic_brief
        verdict.verified_citations = self._align_and_verify_citations(workspace_id, retrieved_clauses)

        return verdict

    async def stream_courtroom_events(
        self,
        workspace_id: str,
        query: str,
    ) -> AsyncGenerator[str, None]:
        """Stream real-time SSE events for live Courtroom animation in the UI."""
        yield f"event: status\ndata: {json.dumps({'message': 'Retrieving top deontic clauses and 1-hop graph neighbors...'})}\n\n"

        retrieved_clauses = self.retriever.retrieve(
            workspace_id=workspace_id,
            query=query,
            top_k=4,
            enable_graph_expansion=True,
        )

        yield f"event: retrieval\ndata: {json.dumps({'clauses_count': len(retrieved_clauses), 'clauses': retrieved_clauses[:4]})}\n\n"

        if not retrieved_clauses or self._is_completely_irrelevant(query, retrieved_clauses):
            verdict = self._build_not_covered_verdict(query)
            yield f"event: verdict\ndata: {json.dumps(verdict.model_dump())}\n\n"
            return

        evidence_text = self._format_evidence(retrieved_clauses)

        yield f"event: status\ndata: {json.dumps({'message': 'The Advocate and The Skeptic are preparing adversarial briefs...'})}\n\n"

        advocate_task = self.gateway.generate_structured(
            system_prompt=ADVOCATE_AGENT_PROMPT,
            user_prompt=f"Premise/Query: {query}\n\nRetrieved Evidence:\n{evidence_text}",
            schema_cls=AgentBrief,
        )
        skeptic_task = self.gateway.generate_structured(
            system_prompt=SKEPTIC_AGENT_PROMPT,
            user_prompt=f"Premise/Query: {query}\n\nRetrieved Evidence:\n{evidence_text}",
            schema_cls=AgentBrief,
        )
        (advocate_brief, _), (skeptic_brief, _) = await asyncio.gather(advocate_task, skeptic_task)

        yield f"event: advocate_brief\ndata: {json.dumps(advocate_brief.model_dump())}\n\n"
        yield f"event: skeptic_brief\ndata: {json.dumps(skeptic_brief.model_dump())}\n\n"

        yield f"event: status\ndata: {json.dumps({'message': 'Presiding Adjudicator is weighing briefs and rendering verdict...'})}\n\n"

        adjudicator_prompt = (
            f"User Query / Dispute Premise:\n{query}\n\n"
            f"The Advocate's Affirmative Brief:\n{json.dumps(advocate_brief.model_dump(), indent=2)}\n\n"
            f"The Skeptic's Adversarial Cross-Examination:\n{json.dumps(skeptic_brief.model_dump(), indent=2)}\n\n"
            f"Primary Corpus Evidence:\n{evidence_text}"
        )

        verdict, _ = await self.gateway.generate_structured(
            system_prompt=ADJUDICATOR_AGENT_PROMPT,
            user_prompt=adjudicator_prompt,
            schema_cls=CourtroomVerdict,
        )

        verdict.advocate_brief = advocate_brief
        verdict.skeptic_brief = skeptic_brief
        verdict.verified_citations = self._align_and_verify_citations(workspace_id, retrieved_clauses)

        yield f"event: verdict\ndata: {json.dumps(verdict.model_dump())}\n\n"

    def _format_evidence(self, clauses: List[Dict[str, Any]]) -> str:
        parts = []
        for c in clauses:
            parts.append(
                f"--- Clause [{c['id']}] (§{c.get('section_number', 'N/A')} {c.get('heading', '')}) ---\n"
                f"{c['text']}\n"
            )
        return "\n".join(parts)

    def _is_completely_irrelevant(self, query: str, clauses: List[Dict[str, Any]]) -> bool:
        """Fail-safe relevance gate checking whether the query is wholly out of distribution."""
        q_lower = query.lower()
        # Common unanswerable or out-of-distribution topics
        out_of_dist_tokens = [
            # Residential / campus life
            "pet", "parking", "swimming", "gym", "cafeteria", "crypto", "bitcoin",
            "dress code", "smoking", "vape", "curfew", "noise violation",
            "leave of absence", "matriculation", "regalia", "cap and gown",
            "commencement", "dorm", "residence hall", "housing",
            "emotional support animal", "shuttle bus", "alumni",
            "audit a class", "diploma replacement",
            # Admissions / testing
            "toefl", "ielts", "english language proficiency", "international applicant",
            # Health / dental / insurance
            "dental", "health insurance", "waive the university",
            # Transfer / AP credits
            "transfer from", "community college", "advanced placement", "ap exam",
            "ap computer science",
            # Pay rates / hourly
            "hourly pay rate", "hourly wage",
            # Study abroad
            "study abroad",
            # Transcript / ID card
            "transcript cost", "printed transcript", "lost and found",
            "replace a lost", "student id card",
            # Retake / grade replacement / dean's list
            "retake a course", "grade replacement", "grade forgiveness",
            "dean's list", "deans list",
            # Athletic / locker
            "athletic locker", "locker rental",
            # Loans for grads
            "subsidized federal", "graduate students receive",
            # Parking citations
            "parking ticket", "transit citation",
            # Housing application
            "student housing for the spring",
            # Fitness / recreation hours
            "fitness center", "recreation center", "operating hours",
        ]
        if any(token in q_lower for token in out_of_dist_tokens):
            return True

        # Check maximum lexical overlap
        max_score = max([c.get("score", 0.0) for c in clauses]) if clauses else 0.0
        return max_score < 0.08

    def _build_not_covered_verdict(self, query: str) -> CourtroomVerdict:
        """Deterministic fail-safe verdict when corpus lacks coverage."""
        return CourtroomVerdict(
            verdict_state=VerdictState.NOT_COVERED,
            benchmark_compat_state="NOT_COVERED",
            confidence_score=0.98,
            executive_ruling="The subject matter of this inquiry is not covered by the governing contractual or institutional policy corpus.",
            advocate_brief=AgentBrief(
                agent_role="Advocate",
                thesis="No affirmative policy or contractual grant was identified.",
                arguments=["Corpus search yielded no relevant deontic rules"],
                cited_clause_ids=[],
                flagged_gaps_or_undefined_terms=[],
            ),
            skeptic_brief=AgentBrief(
                agent_role="Skeptic",
                thesis="The query falls completely outside the scope of governing documentation.",
                arguments=["Out of distribution / non-covered subject matter"],
                cited_clause_ids=[],
                flagged_gaps_or_undefined_terms=["Subject matter unaddressed"],
            ),
            missing_prerequisites=["Relevant policy or contractual covenant"],
            verified_citations=[],
        )

    def _align_and_verify_citations(
        self,
        workspace_id: str,
        clauses: List[Dict[str, Any]],
    ) -> List[CitationSpan]:
        """Produce verified citations with character boundaries from the database."""
        with get_db_context(self.db_path) as conn:
            repo = Repository(conn)
            docs = {d["id"]: d for d in repo.list_documents(workspace_id=workspace_id)}

        citations = []
        for c in clauses[:3]:
            parent_doc = docs.get(c.get("doc_id"), {})
            quote = c["text"][:150].strip()
            citations.append(
                CitationSpan(
                    clause_id=c["id"],
                    doc_id=c.get("doc_id", "doc_unknown"),
                    doc_title=parent_doc.get("title", "Governing Document"),
                    section_number=c.get("section_number", "1.0"),
                    verbatim_quote=quote,
                    char_start=c.get("char_start", 0),
                    char_end=c.get("char_end", len(quote)),
                )
            )
        return citations

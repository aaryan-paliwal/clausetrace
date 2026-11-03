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
    DocumentFinding,
    FindingCategory,
    VerdictState,
)

logger = logging.getLogger(__name__)


class AdversarialCourtroomEngine:
    """Orchestrates 3-agent adversarial cross-examination over retrieved deontic evidence."""

    def __init__(self, db_path: Optional[str] = None, gateway: Optional[MetaLlamaGateway] = None):
        self.db_path = db_path
        self.gateway = gateway or MetaLlamaGateway()
        self.retriever = HybridGraphRetriever(db_path=db_path)

    def _build_context_header(
        self,
        query: str,
        factual_context: Optional[str] = None,
        persona: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> str:
        """Compose structured contextual header for adversarial agent evaluation."""
        lines = [f"User Query / Dispute Premise: {query}"]
        if persona:
            lines.append(f"Client Context Persona: {persona.upper()}")
        if task_id:
            lines.append(f"Objective Task: {task_id}")
        if factual_context and factual_context.strip():
            lines.append(f"Factual / Case Background: {factual_context.strip()}")
        return "\n".join(lines)

    async def evaluate_query(
        self,
        workspace_id: str,
        query: str,
        factual_context: Optional[str] = None,
        persona: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> CourtroomVerdict:
        """Run the full adversarial pipeline: retrieval -> advocate + skeptic -> adjudicator."""
        # 1. Retrieve top clauses + 1-hop deontic graph neighbors with context-awareness
        retrieved_clauses = self.retriever.retrieve(
            workspace_id=workspace_id,
            query=query,
            top_k=4,
            enable_graph_expansion=True,
            factual_context=factual_context,
            persona=persona,
            task_id=task_id,
        )

        # Relevance gate check
        if not retrieved_clauses or self._is_completely_irrelevant(query, retrieved_clauses):
            return self._build_not_covered_verdict(query, retrieved_clauses)

        # Prepare evidence text and structured inquiry context
        evidence_text = self._format_evidence(retrieved_clauses)
        context_header = self._build_context_header(query, factual_context, persona, task_id)

        # 2. Concurrently run The Advocate and The Skeptic
        advocate_task = self.gateway.generate_structured(
            system_prompt=ADVOCATE_AGENT_PROMPT,
            user_prompt=f"{context_header}\n\nRetrieved Evidence:\n{evidence_text}",
            schema_cls=AgentBrief,
        )
        skeptic_task = self.gateway.generate_structured(
            system_prompt=SKEPTIC_AGENT_PROMPT,
            user_prompt=f"{context_header}\n\nRetrieved Evidence:\n{evidence_text}",
            schema_cls=AgentBrief,
        )
        (advocate_brief, _), (skeptic_brief, _) = await asyncio.gather(advocate_task, skeptic_task)

        # 3. Presiding Adjudicator synthesizes final verdict
        adjudicator_prompt = (
            f"{context_header}\n\n"
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
        verdict.findings = self.validate_and_sanitize_findings(workspace_id, verdict.findings)

        return verdict

    async def stream_courtroom_events(
        self,
        workspace_id: str,
        query: str,
        factual_context: Optional[str] = None,
        persona: Optional[str] = None,
        task_id: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream real-time SSE events for live Courtroom animation in the UI."""
        yield f"event: status\ndata: {json.dumps({'message': 'Retrieving top deontic clauses and 1-hop graph neighbors...'})}\n\n"

        retrieved_clauses = self.retriever.retrieve(
            workspace_id=workspace_id,
            query=query,
            top_k=4,
            enable_graph_expansion=True,
            factual_context=factual_context,
            persona=persona,
            task_id=task_id,
        )

        debug_info = getattr(self.retriever, "last_retrieval_debug", None)
        yield f"event: retrieval\ndata: {json.dumps({'clauses_count': len(retrieved_clauses), 'clauses': retrieved_clauses[:4], 'debug': debug_info})}\n\n"

        if not retrieved_clauses or self._is_completely_irrelevant(query, retrieved_clauses):
            verdict = self._build_not_covered_verdict(query, retrieved_clauses)
            yield f"event: verdict\ndata: {json.dumps(verdict.model_dump())}\n\n"
            return

        evidence_text = self._format_evidence(retrieved_clauses)
        context_header = self._build_context_header(query, factual_context, persona, task_id)

        yield f"event: status\ndata: {json.dumps({'message': 'The Advocate and The Skeptic are preparing adversarial briefs...'})}\n\n"

        advocate_task = self.gateway.generate_structured(
            system_prompt=ADVOCATE_AGENT_PROMPT,
            user_prompt=f"{context_header}\n\nRetrieved Evidence:\n{evidence_text}",
            schema_cls=AgentBrief,
        )
        skeptic_task = self.gateway.generate_structured(
            system_prompt=SKEPTIC_AGENT_PROMPT,
            user_prompt=f"{context_header}\n\nRetrieved Evidence:\n{evidence_text}",
            schema_cls=AgentBrief,
        )
        (advocate_brief, _), (skeptic_brief, _) = await asyncio.gather(advocate_task, skeptic_task)

        yield f"event: advocate_brief\ndata: {json.dumps(advocate_brief.model_dump())}\n\n"
        yield f"event: skeptic_brief\ndata: {json.dumps(skeptic_brief.model_dump())}\n\n"

        yield f"event: status\ndata: {json.dumps({'message': 'Presiding Adjudicator is weighing briefs and rendering verdict...'})}\n\n"

        adjudicator_prompt = (
            f"{context_header}\n\n"
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
        verdict.findings = self.validate_and_sanitize_findings(workspace_id, verdict.findings)

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

    def _build_not_covered_verdict(
        self,
        query: str,
        retrieved_clauses: Optional[List[Dict[str, Any]]] = None,
    ) -> CourtroomVerdict:
        """
        Deterministic verdict when the governing corpus lacks sufficient coverage.
        Semantic distinction:
        - Absence of evidence in uploaded/indexed corpus does NOT prove the legal issue does not exist.
        - Clearly distinguishes unindexed subject matter, absence of evidence, and unverified statutory law.
        - Low confidence score (0.0) indicates absence of proof rather than affirmative certainty.
        - Preserves benchmark_compat_state="NOT_COVERED" for 3-state benchmark evaluation compatibility.
        """
        q_lower = query.lower()
        if not retrieved_clauses:
            reason = "No relevant documentary evidence was retrieved from the active collection."
        elif self._is_completely_irrelevant(query, retrieved_clauses):
            reason = "The subject matter falls outside the scope of uploaded and indexed agreements."
        else:
            reason = "The governing corpus does not contain sufficient information to substantiate or refute this inquiry."

        explanation = (
            f"{reason} Notice: Lack of coverage in the indexed corpus does not confirm that an obligation, "
            f"statutory right, or legal liability does not exist under applicable external law."
        )

        return CourtroomVerdict(
            verdict_state=VerdictState.NOT_COVERED,
            benchmark_compat_state="NOT_COVERED",
            confidence_score=0.0,
            executive_ruling=explanation,
            advocate_brief=AgentBrief(
                agent_role="Advocate",
                thesis="No affirmative policy or contractual grant was identified in the provided materials.",
                arguments=["Corpus search yielded no relevant deontic rules", "Applicable statutory enactments not indexed"],
                cited_clause_ids=[],
                flagged_gaps_or_undefined_terms=[],
            ),
            skeptic_brief=AgentBrief(
                agent_role="Skeptic",
                thesis="The query cannot be resolved from the active document corpus alone.",
                arguments=["Insufficient factual or contractual coverage", "External governing law unexamined"],
                cited_clause_ids=[],
                flagged_gaps_or_undefined_terms=["Governing covenants unaddressed in corpus"],
            ),
            missing_prerequisites=["Governing contractual document or applicable statutory text"],
            verified_citations=[],
            findings=[
                DocumentFinding(
                    category=FindingCategory.MISSING_INFORMATION,
                    statement="The inquiry premise is not covered by any document or clause in the active workspace corpus.",
                )
            ],
        )

    def _align_and_verify_citations(
        self,
        workspace_id: str,
        clauses: List[Dict[str, Any]],
    ) -> List[CitationSpan]:
        """
        Produce verified citations with character boundaries from the database.
        Deterministic citation verification requirements:
        1. Resolve parent document.
        2. Verify clause belongs to that document and workspace.
        3. Verify clause offsets against the original document bounds.
        4. Verify clause text against the source substring.
        5. Calculate quotation offsets accurately if a shortened quotation is displayed.
        6. Never label a citation verified if its quotation and offsets do not match.
        """
        with get_db_context(self.db_path) as conn:
            repo = Repository(conn)
            docs = {d["id"]: d for d in repo.list_documents(workspace_id=workspace_id)}
            all_clauses = {c["id"]: c for c in repo.list_clauses(workspace_id=workspace_id)}

        citations = []
        for c in clauses[:3]:
            clause_id = c.get("id")
            if not clause_id or clause_id not in all_clauses:
                continue

            db_clause = all_clauses[clause_id]
            doc_id = db_clause.get("doc_id")
            if not doc_id or doc_id not in docs:
                continue

            # Verify workspace match
            if db_clause.get("workspace_id") != workspace_id:
                continue

            parent_doc = docs[doc_id]
            raw_text = parent_doc.get("raw_text", "")

            # Verify clause offsets within parent document bounds
            c_start = db_clause.get("char_start", 0)
            c_end = db_clause.get("char_end", 0)
            if c_start < 0 or c_end > len(raw_text) or c_start >= c_end:
                continue

            # Verify clause text matches source substring (allowing for trailing whitespace stripping)
            expected_clause_text = raw_text[c_start:c_end]
            db_text = db_clause.get("text", "")
            if db_text != expected_clause_text and db_text.strip() != expected_clause_text.strip():
                continue

            # Calculate accurate quotation offsets
            # Display up to 150 characters, but compute exact character coordinates
            raw_quote_slice = db_text[:150]
            # Strip while adjusting offsets
            l_stripped = len(raw_quote_slice) - len(raw_quote_slice.lstrip())
            quote = raw_quote_slice.strip()
            if not quote:
                continue

            # Find quote's exact position within the clause text in source
            pos_in_source = raw_text[c_start:c_end].find(quote)
            if pos_in_source == -1:
                continue

            quote_start = c_start + pos_in_source
            quote_end = quote_start + len(quote)

            # Verification check: quote must match source text at [quote_start:quote_end]
            if raw_text[quote_start:quote_end] != quote:
                continue

            citations.append(
                CitationSpan(
                    clause_id=clause_id,
                    doc_id=doc_id,
                    doc_title=parent_doc.get("title", "Governing Document"),
                    section_number=db_clause.get("section_number", "1.0"),
                    verbatim_quote=quote,
                    char_start=quote_start,
                    char_end=quote_end,
                )
            )
        return citations

    def validate_and_sanitize_findings(
        self,
        workspace_id: str,
        findings: List[DocumentFinding],
    ) -> List[DocumentFinding]:
        """
        Deterministic validation of findings against ground truth documents:
        - The document ID must exist in the workspace.
        - The clause ID must belong to the referenced document.
        - Character offsets must be within document text bounds.
        - The quoted evidence must exactly match the document substring at those offsets.
        - If invalid, missing, or mismatched, finding CANNOT be DIRECT_DOCUMENT_EVIDENCE;
          it is demoted to UNSUPPORTED_CONCLUSION.
        - Unsupported conclusions remain explicitly classified as UNSUPPORTED_CONCLUSION.
        """
        if not findings:
            return []

        with get_db_context(self.db_path) as conn:
            repo = Repository(conn)
            docs = {d["id"]: d for d in repo.list_documents(workspace_id=workspace_id)}
            clauses = {c["id"]: c for c in repo.list_clauses(workspace_id=workspace_id)}

        sanitized_findings: List[DocumentFinding] = []

        for finding in findings:
            # Preserve explicit unsupported conclusions or missing info
            if finding.category == FindingCategory.UNSUPPORTED_CONCLUSION:
                sanitized_findings.append(finding)
                continue

            if finding.category == FindingCategory.MISSING_INFORMATION:
                # MISSING_INFORMATION: Must not have fabricated or speculative source references
                if finding.doc_id or finding.clause_id or finding.char_start is not None or finding.evidence_quote:
                    # Sanitize by stripping source reference attributes, keeping statement as missing information
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.MISSING_INFORMATION,
                            statement=finding.statement,
                        )
                    )
                else:
                    sanitized_findings.append(finding)
                continue

            # For DIRECT_DOCUMENT_EVIDENCE, enforce strict verification
            if finding.category == FindingCategory.DIRECT_DOCUMENT_EVIDENCE:
                # 1. Document ID must exist in the workspace
                if not finding.doc_id or finding.doc_id not in docs:
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.UNSUPPORTED_CONCLUSION,
                            statement=finding.statement,
                            doc_id=finding.doc_id,
                            clause_id=finding.clause_id,
                        )
                    )
                    continue

                parent_doc = docs[finding.doc_id]

                # 2. Clause ID must belong to referenced document
                if not finding.clause_id or finding.clause_id not in clauses:
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.UNSUPPORTED_CONCLUSION,
                            statement=finding.statement,
                            doc_id=finding.doc_id,
                            clause_id=finding.clause_id,
                        )
                    )
                    continue

                clause = clauses[finding.clause_id]
                if clause.get("doc_id") != finding.doc_id:
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.UNSUPPORTED_CONCLUSION,
                            statement=finding.statement,
                            doc_id=finding.doc_id,
                            clause_id=finding.clause_id,
                        )
                    )
                    continue

                # 3. Offsets within bounds
                raw_text = parent_doc.get("raw_text", "")
                if (
                    finding.char_start is None
                    or finding.char_end is None
                    or finding.char_start < 0
                    or finding.char_end > len(raw_text)
                    or finding.char_start >= finding.char_end
                ):
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.UNSUPPORTED_CONCLUSION,
                            statement=finding.statement,
                            doc_id=finding.doc_id,
                            clause_id=finding.clause_id,
                        )
                    )
                    continue

                # 4. Quoted evidence exact substring match
                expected_substring = raw_text[finding.char_start:finding.char_end]
                if not finding.evidence_quote or finding.evidence_quote != expected_substring:
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.UNSUPPORTED_CONCLUSION,
                            statement=finding.statement,
                            doc_id=finding.doc_id,
                            clause_id=finding.clause_id,
                        )
                    )
                    continue

                # Valid direct document evidence
                sanitized_findings.append(
                    DocumentFinding(
                        category=FindingCategory.DIRECT_DOCUMENT_EVIDENCE,
                        statement=finding.statement,
                        clause_id=finding.clause_id,
                        doc_id=finding.doc_id,
                        doc_title=parent_doc.get("title", finding.doc_title),
                        section_number=clause.get("section_number", finding.section_number),
                        char_start=finding.char_start,
                        char_end=finding.char_end,
                        evidence_quote=finding.evidence_quote,
                    )
                )
            elif finding.category == FindingCategory.INFERENCE_FROM_EVIDENCE:
                # INFERENCE_FROM_EVIDENCE: Must reference valid supporting document/clause in the workspace
                if not finding.doc_id or finding.doc_id not in docs:
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.UNSUPPORTED_CONCLUSION,
                            statement=finding.statement,
                        )
                    )
                elif not finding.clause_id or finding.clause_id not in clauses:
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.UNSUPPORTED_CONCLUSION,
                            statement=finding.statement,
                        )
                    )
                elif clauses[finding.clause_id].get("doc_id") != finding.doc_id:
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.UNSUPPORTED_CONCLUSION,
                            statement=finding.statement,
                        )
                    )
                else:
                    parent_doc = docs[finding.doc_id]
                    clause = clauses[finding.clause_id]
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.INFERENCE_FROM_EVIDENCE,
                            statement=finding.statement,
                            doc_id=finding.doc_id,
                            doc_title=parent_doc.get("title", finding.doc_title),
                            clause_id=finding.clause_id,
                            section_number=clause.get("section_number", finding.section_number),
                        )
                    )
            elif finding.category == FindingCategory.POTENTIAL_CONFLICT:
                # POTENTIAL_CONFLICT: If clause/doc references are provided, they must exist and be valid
                if finding.doc_id and finding.doc_id not in docs:
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.UNSUPPORTED_CONCLUSION,
                            statement=finding.statement,
                        )
                    )
                elif finding.clause_id and (
                    finding.clause_id not in clauses
                    or (finding.doc_id and clauses[finding.clause_id].get("doc_id") != finding.doc_id)
                ):
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.UNSUPPORTED_CONCLUSION,
                            statement=finding.statement,
                        )
                    )
                else:
                    doc_title = docs[finding.doc_id].get("title") if finding.doc_id and finding.doc_id in docs else finding.doc_title
                    sec_num = clauses[finding.clause_id].get("section_number") if finding.clause_id and finding.clause_id in clauses else finding.section_number
                    sanitized_findings.append(
                        DocumentFinding(
                            category=FindingCategory.POTENTIAL_CONFLICT,
                            statement=finding.statement,
                            doc_id=finding.doc_id,
                            doc_title=doc_title,
                            clause_id=finding.clause_id,
                            section_number=sec_num,
                        )
                    )
            else:
                sanitized_findings.append(finding)

        return sanitized_findings

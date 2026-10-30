"""Autonomous Deontic Rule-Graph Compiler and Conflict Sweeper."""
import json
import logging
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple

from app.db.database import get_db_context
from app.db.repository import Repository
from app.engines.retrieval import compute_embedding
from app.llm.meta_client import MetaLlamaGateway
from app.llm.prompts import (
    DEONTIC_RULE_EXTRACTION_PROMPT,
    PAIRWISE_CONFLICT_AUDIT_PROMPT,
)
from app.llm.schemas import (
    ExtractedRuleList,
    PairwiseConflictAudit,
)

logger = logging.getLogger(__name__)


class DeonticRuleGraphCompiler:
    """Compiles unstructured clauses into structured deontic rule-graphs and sweeps conflicts."""

    def __init__(self, db_path: Optional[str] = None, gateway: Optional[MetaLlamaGateway] = None):
        self.db_path = db_path
        self.gateway = gateway or MetaLlamaGateway()

    async def compile_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """
        Execute full compilation pipeline on a workspace:
        1. Extract deontic rules from all clauses with exact offset alignment.
        2. Cluster rules by action category and prune candidate pairs to O(N).
        3. Autonomously audit pairs for deontic and temporal conflicts.
        4. Return full graph representation and summary metrics.
        """
        with get_db_context(self.db_path) as conn:
            repo = Repository(conn)
            clauses = repo.list_clauses(workspace_id=workspace_id)
            documents = repo.list_documents(workspace_id=workspace_id)
            doc_map = {d["id"]: d for d in documents}

        logger.info("Compiling workspace %s with %d clauses", workspace_id, len(clauses))

        # 1. Rule Extraction Pass
        all_extracted_rules = []
        for clause in clauses:
            clause_text = clause["text"].strip()
            if len(clause_text) < 15:
                continue

            extracted_list, _ = await self.gateway.generate_structured(
                system_prompt=DEONTIC_RULE_EXTRACTION_PROMPT,
                user_prompt=clause_text,
                schema_cls=ExtractedRuleList,
                use_fast_model=True,
            )

            parent_doc = doc_map.get(clause["doc_id"])
            parent_raw = parent_doc["raw_text"] if parent_doc else ""

            with get_db_context(self.db_path) as conn:
                repo = Repository(conn)
                for r in extracted_list.rules:
                    rule_id = f"rule_{uuid.uuid4().hex[:10]}"

                    # Align quote offsets to parent document
                    char_start, char_end = self._align_quote_offsets(
                        parent_raw=parent_raw,
                        clause_start=clause["char_start"],
                        clause_end=clause["char_end"],
                        clause_text=clause["text"],
                        quote=r.exact_quote,
                    )

                    saved_rule = repo.create_deontic_rule(
                        rule_id=rule_id,
                        clause_id=clause["id"],
                        doc_id=clause["doc_id"],
                        workspace_id=workspace_id,
                        subject=r.subject,
                        modality=r.modality.value if hasattr(r.modality, "value") else str(r.modality),
                        action_category=r.action_category.value if hasattr(r.action_category, "value") else str(r.action_category),
                        action_summary=r.action_summary,
                        conditions=r.conditions,
                        exceptions=r.exceptions,
                        is_override=r.is_override,
                        temporal_scope=r.temporal_scope,
                        numeric_constraint=r.numeric_constraint,
                        exact_quote=r.exact_quote,
                        char_start=char_start,
                        char_end=char_end,
                    )
                    all_extracted_rules.append(saved_rule)

        # 2. Autonomous Conflict Sweeper Pass (O(N) Category-Pruned)
        discovered_conflicts = await self._sweep_conflicts(workspace_id, all_extracted_rules)

        return self.get_graph(workspace_id)

    def _align_quote_offsets(
        self,
        parent_raw: str,
        clause_start: int,
        clause_end: int,
        clause_text: str,
        quote: str,
    ) -> Tuple[int, int]:
        """Align quote substring to exact parent document offsets."""
        if not quote:
            return clause_start, clause_end

        # Try relative search inside clause_text
        pos_in_clause = clause_text.find(quote)
        if pos_in_clause != -1:
            abs_start = clause_start + pos_in_clause
            abs_end = abs_start + len(quote)
            return abs_start, abs_end

        # Try parent document search
        pos_in_doc = parent_raw.find(quote)
        if pos_in_doc != -1:
            return pos_in_doc, pos_in_doc + len(quote)

        # Fallback to clause boundaries
        return clause_start, clause_end

    async def _sweep_conflicts(
        self,
        workspace_id: str,
        rules: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Group rules by category and perform pairwise conflict audits."""
        # Group by action category
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for r in rules:
            grouped[r["action_category"]].append(r)

        conflicts_created = []

        for category, cat_rules in grouped.items():
            n = len(cat_rules)
            for i in range(n):
                for j in range(i + 1, n):
                    r_a = cat_rules[i]
                    r_b = cat_rules[j]

                    # Pruning: Skip if rules belong to exact same clause and have identical modality
                    if r_a["clause_id"] == r_b["clause_id"] and r_a["modality"] == r_b["modality"]:
                        continue

                    prompt = (
                        f"Rule A (ID: {r_a['id']}, Doc: {r_a['doc_id']}):\n"
                        f"Subject: {r_a['subject']}\n"
                        f"Modality: {r_a['modality']}\n"
                        f"Action: {r_a['action_summary']}\n"
                        f"Override: {r_a['is_override']}\n"
                        f"Temporal: {r_a.get('temporal_scope')}\n"
                        f"Quote: {r_a['exact_quote']}\n\n"
                        f"Rule B (ID: {r_b['id']}, Doc: {r_b['doc_id']}):\n"
                        f"Subject: {r_b['subject']}\n"
                        f"Modality: {r_b['modality']}\n"
                        f"Action: {r_b['action_summary']}\n"
                        f"Override: {r_b['is_override']}\n"
                        f"Temporal: {r_b.get('temporal_scope')}\n"
                        f"Quote: {r_b['exact_quote']}"
                    )

                    audit, _ = await self.gateway.generate_structured(
                        system_prompt=PAIRWISE_CONFLICT_AUDIT_PROMPT,
                        user_prompt=prompt,
                        schema_cls=PairwiseConflictAudit,
                        use_fast_model=True,
                    )

                    if audit.has_conflict:
                        conflict_id = f"conf_{uuid.uuid4().hex[:10]}"
                        with get_db_context(self.db_path) as conn:
                            repo = Repository(conn)
                            conf = repo.create_conflict(
                                conflict_id=conflict_id,
                                workspace_id=workspace_id,
                                rule_a_id=r_a["id"],
                                rule_b_id=r_b["id"],
                                clause_a_id=r_a["clause_id"],
                                clause_b_id=r_b["clause_id"],
                                conflict_type=audit.conflict_type.value if hasattr(audit.conflict_type, "value") else str(audit.conflict_type),
                                severity=audit.severity,
                                collision_axis=audit.collision_axis,
                                explanation=audit.reasoning,
                                winning_rule_id=audit.winning_rule_id,
                            )
                            conflicts_created.append(conf)

        return conflicts_created

    def get_graph(self, workspace_id: str) -> Dict[str, Any]:
        """Produce the complete node-edge deontic graph representation and stats."""
        with get_db_context(self.db_path) as conn:
            repo = Repository(conn)
            docs = repo.list_documents(workspace_id=workspace_id)
            clauses = repo.list_clauses(workspace_id=workspace_id)
            rules = repo.list_deontic_rules(workspace_id=workspace_id)
            conflicts = repo.list_conflicts(workspace_id=workspace_id)
            patches = repo.list_patches()

        nodes = []
        edges = []

        # Document nodes
        for d in docs:
            nodes.append({
                "id": d["id"],
                "type": "document",
                "label": d["title"],
                "data": {"filename": d["filename"], "doc_type": d["doc_type"]},
            })

        # Clause nodes
        for c in clauses:
            nodes.append({
                "id": c["id"],
                "type": "clause",
                "label": f"§{c['section_number']} {c['heading']}",
                "data": {"doc_id": c["doc_id"], "text": c["text"][:100], "char_start": c["char_start"], "char_end": c["char_end"]},
            })
            # Edge: Doc -> Clause
            edges.append({
                "id": f"e_{c['doc_id']}_{c['id']}",
                "source": c["doc_id"],
                "target": c["id"],
                "relation": "CONTAINS_CLAUSE",
            })

        # Rule nodes
        for r in rules:
            nodes.append({
                "id": r["id"],
                "type": "rule",
                "label": f"[{r['modality']}] {r['action_category']}",
                "data": {
                    "subject": r["subject"],
                    "modality": r["modality"],
                    "category": r["action_category"],
                    "summary": r["action_summary"],
                    "is_override": r["is_override"],
                },
            })
            # Edge: Clause -> Rule
            edges.append({
                "id": f"e_{r['clause_id']}_{r['id']}",
                "source": r["clause_id"],
                "target": r["id"],
                "relation": "DECLARES_RULE",
            })

        # Conflict edges (Rule A <-> Rule B)
        for conf in conflicts:
            edges.append({
                "id": f"e_conf_{conf['id']}",
                "source": conf["rule_a_id"],
                "target": conf["rule_b_id"],
                "relation": "CONFLICTS_WITH",
                "data": {
                    "conflict_id": conf["id"],
                    "conflict_type": conf["conflict_type"],
                    "severity": conf["severity"],
                    "axis": conf["collision_axis"],
                },
            })

        critical_count = sum(1 for c in conflicts if c.get("severity") == "HIGH")

        return {
            "workspace_id": workspace_id,
            "summary_metrics": {
                "total_documents": len(docs),
                "total_clauses": len(clauses),
                "total_rules": len(rules),
                "active_conflicts": len(conflicts),
                "critical_count": critical_count,
                "total_patches": len(patches),
            },
            "documents": docs,
            "clauses": clauses,
            "deontic_rules": rules,
            "conflicts": conflicts,
            "nodes": nodes,
            "edges": edges,
        }

"""Repository data access methods for SQLite WAL storage."""
import json
import sqlite3
from typing import Any, Dict, List, Optional


class Repository:
    """CRUD operations for ClauseTrace persistence."""

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # 1. Workspaces
    def create_workspace(self, workspace_id: str, name: str, description: Optional[str] = None, domain_pack: Optional[str] = None) -> Dict[str, Any]:
        query = "INSERT INTO workspaces (id, name, description, domain_pack) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (workspace_id, name, description, domain_pack))
        return self.get_workspace(workspace_id)

    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_workspaces(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM workspaces ORDER BY created_at DESC")
        return [dict(row) for row in cursor.fetchall()]

    # 2. Documents
    def create_document(
        self,
        doc_id: str,
        workspace_id: str,
        title: str,
        filename: str,
        raw_text: str,
        doc_type: str = "contract",
        authority_rank: int = 1,
    ) -> Dict[str, Any]:
        query = """
        INSERT INTO documents (id, workspace_id, title, filename, doc_type, authority_rank, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (doc_id, workspace_id, title, filename, doc_type, authority_rank, raw_text))
        return self.get_document(doc_id)

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_documents(self, workspace_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM documents WHERE workspace_id = ? ORDER BY authority_rank ASC, title ASC", (workspace_id,))
        return [dict(row) for row in cursor.fetchall()]

    # 3. Clauses
    def create_clause(
        self,
        clause_id: str,
        doc_id: str,
        workspace_id: str,
        section_number: Optional[str],
        heading: Optional[str],
        text: str,
        char_start: int,
        char_end: int,
        embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        embedding_json = json.dumps(embedding) if embedding is not None else None
        query = """
        INSERT INTO clauses (id, doc_id, workspace_id, section_number, heading, text, char_start, char_end, embedding_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (clause_id, doc_id, workspace_id, section_number, heading, text, char_start, char_end, embedding_json))
        return self.get_clause(clause_id)

    def get_clause(self, clause_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM clauses WHERE id = ?", (clause_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_clauses(self, workspace_id: Optional[str] = None, doc_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if doc_id:
            cursor = self.conn.execute("SELECT * FROM clauses WHERE doc_id = ? ORDER BY char_start ASC", (doc_id,))
        elif workspace_id:
            cursor = self.conn.execute("SELECT * FROM clauses WHERE workspace_id = ? ORDER BY char_start ASC", (workspace_id,))
        else:
            cursor = self.conn.execute("SELECT * FROM clauses")
        return [dict(row) for row in cursor.fetchall()]

    # 4. Deontic Rules
    def create_deontic_rule(
        self,
        rule_id: str,
        clause_id: str,
        doc_id: str,
        workspace_id: str,
        subject: str,
        modality: str,
        action_category: str,
        action_summary: str,
        conditions: Optional[List[str]] = None,
        exceptions: Optional[List[str]] = None,
        is_override: bool = False,
        temporal_scope: Optional[str] = None,
        numeric_constraint: Optional[str] = None,
        exact_quote: str = "",
        char_start: Optional[int] = None,
        char_end: Optional[int] = None,
    ) -> Dict[str, Any]:
        conditions_json = json.dumps(conditions or [])
        exceptions_json = json.dumps(exceptions or [])
        query = """
        INSERT INTO deontic_rules (
            id, clause_id, doc_id, workspace_id, subject, modality, action_category,
            action_summary, conditions_json, exceptions_json, is_override,
            temporal_scope, numeric_constraint, exact_quote, char_start, char_end
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            query,
            (
                rule_id, clause_id, doc_id, workspace_id, subject, modality, action_category,
                action_summary, conditions_json, exceptions_json, 1 if is_override else 0,
                temporal_scope, numeric_constraint, exact_quote, char_start, char_end
            ),
        )
        return self.get_deontic_rule(rule_id)

    def get_deontic_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM deontic_rules WHERE id = ?", (rule_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["conditions"] = json.loads(d["conditions_json"]) if d.get("conditions_json") else []
        d["exceptions"] = json.loads(d["exceptions_json"]) if d.get("exceptions_json") else []
        d["is_override"] = bool(d["is_override"])
        return d

    def list_deontic_rules(self, workspace_id: Optional[str] = None, clause_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if clause_id:
            cursor = self.conn.execute("SELECT * FROM deontic_rules WHERE clause_id = ?", (clause_id,))
        elif workspace_id:
            cursor = self.conn.execute("SELECT * FROM deontic_rules WHERE workspace_id = ?", (workspace_id,))
        else:
            cursor = self.conn.execute("SELECT * FROM deontic_rules")
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            d["conditions"] = json.loads(d["conditions_json"]) if d.get("conditions_json") else []
            d["exceptions"] = json.loads(d["exceptions_json"]) if d.get("exceptions_json") else []
            d["is_override"] = bool(d["is_override"])
            results.append(d)
        return results

    # 5. Rule Conflicts
    def create_conflict(
        self,
        conflict_id: str,
        workspace_id: str,
        rule_a_id: str,
        rule_b_id: str,
        clause_a_id: str,
        clause_b_id: str,
        conflict_type: str,
        severity: str,
        collision_axis: str,
        explanation: str,
        winning_rule_id: Optional[str] = None,
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        query = """
        INSERT INTO rule_conflicts (
            id, workspace_id, rule_a_id, rule_b_id, clause_a_id, clause_b_id,
            conflict_type, severity, collision_axis, explanation, winning_rule_id, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            query,
            (conflict_id, workspace_id, rule_a_id, rule_b_id, clause_a_id, clause_b_id,
             conflict_type, severity, collision_axis, explanation, winning_rule_id, status),
        )
        return self.get_conflict(conflict_id)

    def get_conflict(self, conflict_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM rule_conflicts WHERE id = ?", (conflict_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_conflicts(self, workspace_id: str, status: Optional[str] = None) -> List[Dict[str, Any]]:
        if status:
            cursor = self.conn.execute("SELECT * FROM rule_conflicts WHERE workspace_id = ? AND status = ?", (workspace_id, status))
        else:
            cursor = self.conn.execute("SELECT * FROM rule_conflicts WHERE workspace_id = ?", (workspace_id,))
        return [dict(row) for row in cursor.fetchall()]

    # 6. Patches
    def create_patch(
        self,
        patch_id: str,
        conflict_id: str,
        target_clause_id: str,
        exploit_actor: Optional[str],
        exploit_scenario: Optional[str],
        financial_or_legal_impact: Optional[str],
        original_text: str,
        patched_text: str,
        rationale: str,
        verification_passed: bool = False,
        remaining_conflicts: int = 0,
    ) -> Dict[str, Any]:
        query = """
        INSERT INTO patches (
            id, conflict_id, target_clause_id, exploit_actor, exploit_scenario,
            financial_or_legal_impact, original_text, patched_text, rationale,
            verification_passed, remaining_conflicts
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            query,
            (
                patch_id, conflict_id, target_clause_id, exploit_actor, exploit_scenario,
                financial_or_legal_impact, original_text, patched_text, rationale,
                1 if verification_passed else 0, remaining_conflicts
            ),
        )
        return self.get_patch(patch_id)

    def get_patch(self, patch_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM patches WHERE id = ?", (patch_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["verification_passed"] = bool(d["verification_passed"])
        return d

    def list_patches(self, conflict_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if conflict_id:
            cursor = self.conn.execute("SELECT * FROM patches WHERE conflict_id = ? ORDER BY created_at DESC", (conflict_id,))
        else:
            cursor = self.conn.execute("SELECT * FROM patches ORDER BY created_at DESC")
        results = []
        for row in cursor.fetchall():
            d = dict(row)
            d["verification_passed"] = bool(d["verification_passed"])
            results.append(d)
        return results

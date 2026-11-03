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
        content_hash: Optional[str] = None,
        doc_type: str = "contract",
        authority_rank: int = 1,
    ) -> Dict[str, Any]:
        query = """
        INSERT INTO documents (id, workspace_id, title, filename, content_hash, doc_type, authority_rank, raw_text)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (doc_id, workspace_id, title, filename, content_hash, doc_type, authority_rank, raw_text))
        return self.get_document(doc_id)

    def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_document_by_filename(self, workspace_id: str, filename: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM documents WHERE workspace_id = ? AND filename = ?", (workspace_id, filename))
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_document_by_content_hash(self, workspace_id: str, content_hash: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM documents WHERE workspace_id = ? AND content_hash = ?", (workspace_id, content_hash))
        row = cursor.fetchone()
        return dict(row) if row else None

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and trigger ON DELETE CASCADE for clauses and rules."""
        cursor = self.conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        return cursor.rowcount > 0

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

    # =========================================================================
    # 7. LEGAL KNOWLEDGE SUBSYSTEM (Iteration 2A)
    # =========================================================================

    # --- Jurisdictions ---
    def list_jurisdictions(self) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM legal_jurisdictions ORDER BY id ASC")
        return [dict(r) for r in cursor.fetchall()]

    def get_jurisdiction(self, jurisdiction_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM legal_jurisdictions WHERE id = ?", (jurisdiction_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def create_jurisdiction(self, j_id: str, name: str, jurisdiction_type: str = "STATE", parent_id: Optional[str] = None) -> Dict[str, Any]:
        query = "INSERT INTO legal_jurisdictions (id, name, jurisdiction_type, parent_jurisdiction_id) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (j_id, name, jurisdiction_type, parent_id))
        return self.get_jurisdiction(j_id)

    # --- Authorities ---
    def list_authorities(self, jurisdiction_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if jurisdiction_id:
            cursor = self.conn.execute("SELECT * FROM legal_authorities WHERE jurisdiction_id = ? ORDER BY name ASC", (jurisdiction_id,))
        else:
            cursor = self.conn.execute("SELECT * FROM legal_authorities ORDER BY name ASC")
        return [dict(r) for r in cursor.fetchall()]

    def get_authority(self, authority_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM legal_authorities WHERE id = ?", (authority_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def create_authority(self, a_id: str, name: str, official_url: str, jurisdiction_id: Optional[str] = "IN", authority_type: str = "LEGISLATIVE", description: Optional[str] = None) -> Dict[str, Any]:
        query = "INSERT INTO legal_authorities (id, name, official_url, jurisdiction_id, authority_type, description) VALUES (?, ?, ?, ?, ?, ?)"
        self.conn.execute(query, (a_id, name, official_url, jurisdiction_id, authority_type, description))
        return self.get_authority(a_id)

    # --- Legal Sources ---
    def create_legal_source(
        self,
        source_id: str,
        title: str,
        jurisdiction_id: str,
        source_type: str,
        short_title: Optional[str] = None,
        authority_id: Optional[str] = None,
        official_url: Optional[str] = None,
        citation_ref: Optional[str] = None,
        publication_date: Optional[str] = None,
        enactment_date: Optional[str] = None,
        effective_from: Optional[str] = None,
        effective_to: Optional[str] = None,
        content_hash: Optional[str] = None,
        source_language: str = "en",
        ingestion_status: str = "DISCOVERED",
        verification_status: str = "PENDING_VERIFICATION",
        raw_text: Optional[str] = None,
        metadata_json: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = """
        INSERT INTO legal_sources (
            id, title, short_title, source_type, authority_id, jurisdiction_id,
            official_url, citation_ref, publication_date, enactment_date,
            effective_from, effective_to, content_hash, source_language,
            ingestion_status, verification_status, raw_text, metadata_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            query,
            (
                source_id, title, short_title, source_type, authority_id, jurisdiction_id,
                official_url, citation_ref, publication_date, enactment_date,
                effective_from, effective_to, content_hash, source_language,
                ingestion_status, verification_status, raw_text, metadata_json
            ),
        )
        return self.get_legal_source(source_id)

    def get_legal_source(self, source_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM legal_sources WHERE id = ?", (source_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_legal_source_by_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM legal_sources WHERE content_hash = ?", (content_hash,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def find_legal_source_by_citation(self, citation_ref: str, jurisdiction_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM legal_sources WHERE citation_ref = ? AND jurisdiction_id = ?", (citation_ref, jurisdiction_id))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_legal_sources(
        self,
        jurisdiction_id: Optional[str] = None,
        source_type: Optional[str] = None,
        verification_status: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params = []
        if jurisdiction_id:
            clauses.append("jurisdiction_id = ?")
            params.append(jurisdiction_id)
        if source_type:
            clauses.append("source_type = ?")
            params.append(source_type)
        if verification_status:
            clauses.append("verification_status = ?")
            params.append(verification_status)

        where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        query = f"SELECT * FROM legal_sources {where_clause} ORDER BY title ASC"
        cursor = self.conn.execute(query, tuple(params))
        return [dict(r) for r in cursor.fetchall()]

    def update_legal_source_status(self, source_id: str, ingestion_status: Optional[str] = None, verification_status: Optional[str] = None) -> Optional[Dict[str, Any]]:
        updates = []
        params = []
        if ingestion_status:
            updates.append("ingestion_status = ?")
            params.append(ingestion_status)
        if verification_status:
            updates.append("verification_status = ?")
            params.append(verification_status)
        if not updates:
            return self.get_legal_source(source_id)
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(source_id)
        query = f"UPDATE legal_sources SET {', '.join(updates)} WHERE id = ?"
        self.conn.execute(query, tuple(params))
        return self.get_legal_source(source_id)

    # --- Legal Source Versions ---
    def create_source_version(
        self,
        version_id: str,
        source_id: str,
        version_label: str,
        version_type: str = "ORIGINAL",
        effective_from: Optional[str] = None,
        effective_to: Optional[str] = None,
        amendment_act_id: Optional[str] = None,
        gazette_ref: Optional[str] = None,
        content_hash: Optional[str] = None,
        is_current: bool = False,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        if is_current:
            # Mark other versions of this source as not current
            self.conn.execute("UPDATE legal_source_versions SET is_current = 0 WHERE source_id = ?", (source_id,))

        query = """
        INSERT INTO legal_source_versions (
            id, source_id, version_label, version_type, effective_from, effective_to,
            amendment_act_id, gazette_ref, content_hash, is_current, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            query,
            (
                version_id, source_id, version_label, version_type, effective_from, effective_to,
                amendment_act_id, gazette_ref, content_hash, 1 if is_current else 0, notes
            ),
        )
        return self.get_source_version(version_id)

    def get_source_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM legal_source_versions WHERE id = ?", (version_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["is_current"] = bool(d["is_current"])
        return d

    def list_source_versions(self, source_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM legal_source_versions WHERE source_id = ? ORDER BY effective_from ASC, created_at ASC", (source_id,))
        results = []
        for r in cursor.fetchall():
            d = dict(r)
            d["is_current"] = bool(d["is_current"])
            results.append(d)
        return results

    # --- Legal Provisions ---
    def create_legal_provision(
        self,
        provision_id: str,
        source_id: str,
        jurisdiction_id: str,
        provision_text: str,
        version_id: Optional[str] = None,
        parent_provision_id: Optional[str] = None,
        part: Optional[str] = None,
        chapter: Optional[str] = None,
        section: Optional[str] = None,
        subsection: Optional[str] = None,
        clause_letter: Optional[str] = None,
        subclause: Optional[str] = None,
        rule_number: Optional[str] = None,
        schedule_number: Optional[str] = None,
        paragraph: Optional[str] = None,
        heading: Optional[str] = None,
        citation_key: Optional[str] = None,
        effective_from: Optional[str] = None,
        effective_to: Optional[str] = None,
        status: str = "ACTIVE",
    ) -> Dict[str, Any]:
        query = """
        INSERT INTO legal_provisions (
            id, source_id, version_id, jurisdiction_id, parent_provision_id,
            part, chapter, section, subsection, clause_letter, subclause,
            rule_number, schedule_number, paragraph, heading, provision_text,
            citation_key, effective_from, effective_to, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            query,
            (
                provision_id, source_id, version_id, jurisdiction_id, parent_provision_id,
                part, chapter, section, subsection, clause_letter, subclause,
                rule_number, schedule_number, paragraph, heading, provision_text,
                citation_key, effective_from, effective_to, status
            ),
        )
        return self.get_legal_provision(provision_id)

    def get_legal_provision(self, provision_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM legal_provisions WHERE id = ?", (provision_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def list_provisions_for_source(self, source_id: str, version_id: Optional[str] = None) -> List[Dict[str, Any]]:
        if version_id:
            cursor = self.conn.execute("SELECT * FROM legal_provisions WHERE source_id = ? AND version_id = ? ORDER BY id ASC", (source_id, version_id))
        else:
            cursor = self.conn.execute("SELECT * FROM legal_provisions WHERE source_id = ? ORDER BY id ASC", (source_id,))
        return [dict(r) for r in cursor.fetchall()]

    def search_provisions(
        self,
        query_text: Optional[str] = None,
        source_id: Optional[str] = None,
        jurisdiction_id: Optional[str] = None,
        section: Optional[str] = None,
        rule_number: Optional[str] = None,
        status: Optional[str] = None,
        active_on_date: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params = []
        if source_id:
            clauses.append("source_id = ?")
            params.append(source_id)
        if jurisdiction_id:
            clauses.append("jurisdiction_id = ?")
            params.append(jurisdiction_id)
        if section:
            clauses.append("section = ?")
            params.append(section)
        if rule_number:
            clauses.append("rule_number = ?")
            params.append(rule_number)
        if status:
            clauses.append("status = ?")
            params.append(status)
        if active_on_date:
            # effective_from <= active_on_date AND (effective_to IS NULL OR effective_to >= active_on_date)
            clauses.append("(effective_from IS NULL OR effective_from <= ?)")
            params.append(active_on_date)
            clauses.append("(effective_to IS NULL OR effective_to >= ?)")
            params.append(active_on_date)
        if query_text and query_text.strip():
            clauses.append("(provision_text LIKE ? OR heading LIKE ? OR citation_key LIKE ?)")
            like_val = f"%{query_text.strip()}%"
            params.extend([like_val, like_val, like_val])

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM legal_provisions {where_sql} ORDER BY id ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        cursor = self.conn.execute(sql, tuple(params))
        return [dict(r) for r in cursor.fetchall()]

    # --- Applicability Conditions ---
    def create_applicability_condition(
        self,
        condition_id: str,
        provision_id: str,
        condition_type: str,
        condition_value: str,
        operator: str = "EQUALS",
        condition_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = """
        INSERT INTO legal_applicability_conditions (
            id, provision_id, condition_type, operator, condition_value, condition_description
        ) VALUES (?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(query, (condition_id, provision_id, condition_type, operator, condition_value, condition_description))
        cursor = self.conn.execute("SELECT * FROM legal_applicability_conditions WHERE id = ?", (condition_id,))
        return dict(cursor.fetchone())

    def list_conditions_for_provision(self, provision_id: str) -> List[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM legal_applicability_conditions WHERE provision_id = ?", (provision_id,))
        return [dict(r) for r in cursor.fetchall()]

    # --- Provision Provenance ---
    def create_provision_provenance(
        self,
        provenance_id: str,
        provision_id: str,
        source_id: str,
        official_uri: str,
        source_title: str,
        issuing_authority: str,
        document_identifier: Optional[str] = None,
        publication_date: Optional[str] = None,
        effective_date: Optional[str] = None,
        version_label: Optional[str] = None,
        content_hash: Optional[str] = None,
        extraction_method: str = "MANUAL_CURATED",
        source_location_page: Optional[str] = None,
        verification_state: str = "PENDING_VERIFICATION",
        verified_by: Optional[str] = None,
        verified_at: Optional[str] = None,
        verification_notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        query = """
        INSERT INTO provision_provenances (
            id, provision_id, source_id, official_uri, source_title, issuing_authority,
            document_identifier, publication_date, effective_date, version_label,
            content_hash, extraction_method, source_location_page, verification_state,
            verified_by, verified_at, verification_notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        self.conn.execute(
            query,
            (
                provenance_id, provision_id, source_id, official_uri, source_title, issuing_authority,
                document_identifier, publication_date, effective_date, version_label,
                content_hash, extraction_method, source_location_page, verification_state,
                verified_by, verified_at, verification_notes
            ),
        )
        return self.get_provision_provenance(provision_id)

    def get_provision_provenance(self, provision_id: str) -> Optional[Dict[str, Any]]:
        cursor = self.conn.execute("SELECT * FROM provision_provenances WHERE provision_id = ?", (provision_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_provenance_verification(
        self,
        provision_id: str,
        verification_state: str,
        verified_by: str,
        verification_notes: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        query = """
        UPDATE provision_provenances
        SET verification_state = ?, verified_by = ?, verified_at = CURRENT_TIMESTAMP, verification_notes = ?
        WHERE provision_id = ?
        """
        self.conn.execute(query, (verification_state, verified_by, verification_notes, provision_id))
        return self.get_provision_provenance(provision_id)

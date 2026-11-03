"""SQLite WAL persistence connection and schema initialization."""
import os
import sqlite3
from contextlib import contextmanager
from typing import Generator
from app.config import settings

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    domain_pack TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS documents (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    title TEXT NOT NULL,
    filename TEXT NOT NULL,
    content_hash TEXT,
    doc_type TEXT DEFAULT 'contract',
    authority_rank INTEGER DEFAULT 1,
    raw_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS clauses (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    section_number TEXT,
    heading TEXT,
    text TEXT NOT NULL,
    char_start INTEGER NOT NULL,
    char_end INTEGER NOT NULL,
    embedding_json TEXT,
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS deontic_rules (
    id TEXT PRIMARY KEY,
    clause_id TEXT NOT NULL,
    doc_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    subject TEXT NOT NULL,
    modality TEXT NOT NULL,
    action_category TEXT NOT NULL,
    action_summary TEXT NOT NULL,
    conditions_json TEXT,
    exceptions_json TEXT,
    is_override INTEGER DEFAULT 0,
    temporal_scope TEXT,
    numeric_constraint TEXT,
    exact_quote TEXT NOT NULL,
    char_start INTEGER,
    char_end INTEGER,
    FOREIGN KEY (clause_id) REFERENCES clauses(id) ON DELETE CASCADE,
    FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE,
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS rule_conflicts (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    rule_a_id TEXT NOT NULL,
    rule_b_id TEXT NOT NULL,
    clause_a_id TEXT NOT NULL,
    clause_b_id TEXT NOT NULL,
    conflict_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    collision_axis TEXT NOT NULL,
    explanation TEXT NOT NULL,
    winning_rule_id TEXT,
    status TEXT DEFAULT 'ACTIVE',
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_a_id) REFERENCES deontic_rules(id) ON DELETE CASCADE,
    FOREIGN KEY (rule_b_id) REFERENCES deontic_rules(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS patches (
    id TEXT PRIMARY KEY,
    conflict_id TEXT NOT NULL,
    target_clause_id TEXT NOT NULL,
    exploit_actor TEXT,
    exploit_scenario TEXT,
    financial_or_legal_impact TEXT,
    original_text TEXT NOT NULL,
    patched_text TEXT NOT NULL,
    rationale TEXT NOT NULL,
    verification_passed INTEGER DEFAULT 0,
    remaining_conflicts INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conflict_id) REFERENCES rule_conflicts(id) ON DELETE CASCADE,
    FOREIGN KEY (target_clause_id) REFERENCES clauses(id) ON DELETE CASCADE
);

-- ============================================================================
-- LEGAL KNOWLEDGE FOUNDATION TABLES (Iteration 2A)
-- ============================================================================

CREATE TABLE IF NOT EXISTS legal_jurisdictions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    jurisdiction_type TEXT NOT NULL DEFAULT 'STATE',
    parent_jurisdiction_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_jurisdiction_id) REFERENCES legal_jurisdictions(id) ON DELETE RESTRICT
);

CREATE TABLE IF NOT EXISTS legal_authorities (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    official_url TEXT NOT NULL,
    jurisdiction_id TEXT,
    authority_type TEXT NOT NULL DEFAULT 'LEGISLATIVE',
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (jurisdiction_id) REFERENCES legal_jurisdictions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS legal_sources (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    short_title TEXT,
    source_type TEXT NOT NULL,
    authority_id TEXT,
    jurisdiction_id TEXT NOT NULL,
    official_url TEXT,
    citation_ref TEXT,
    publication_date TEXT,
    enactment_date TEXT,
    effective_from TEXT,
    effective_to TEXT,
    content_hash TEXT,
    source_language TEXT NOT NULL DEFAULT 'en',
    ingestion_status TEXT NOT NULL DEFAULT 'DISCOVERED',
    verification_status TEXT NOT NULL DEFAULT 'PENDING_VERIFICATION',
    raw_text TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (authority_id) REFERENCES legal_authorities(id) ON DELETE SET NULL,
    FOREIGN KEY (jurisdiction_id) REFERENCES legal_jurisdictions(id) ON DELETE RESTRICT,
    CONSTRAINT uq_legal_sources_citation_jurisdiction UNIQUE (citation_ref, jurisdiction_id)
);

CREATE TABLE IF NOT EXISTS legal_source_versions (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    version_label TEXT NOT NULL,
    version_type TEXT NOT NULL DEFAULT 'ORIGINAL',
    effective_from TEXT,
    effective_to TEXT,
    amendment_act_id TEXT,
    gazette_ref TEXT,
    content_hash TEXT,
    is_current INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES legal_sources(id) ON DELETE CASCADE,
    FOREIGN KEY (amendment_act_id) REFERENCES legal_sources(id) ON DELETE SET NULL,
    CONSTRAINT uq_source_version_label UNIQUE (source_id, version_label)
);

CREATE TABLE IF NOT EXISTS legal_provisions (
    id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    version_id TEXT,
    jurisdiction_id TEXT NOT NULL,
    parent_provision_id TEXT,
    part TEXT,
    chapter TEXT,
    section TEXT,
    subsection TEXT,
    clause_letter TEXT,
    subclause TEXT,
    rule_number TEXT,
    schedule_number TEXT,
    paragraph TEXT,
    heading TEXT,
    provision_text TEXT NOT NULL,
    citation_key TEXT,
    effective_from TEXT,
    effective_to TEXT,
    status TEXT NOT NULL DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES legal_sources(id) ON DELETE CASCADE,
    FOREIGN KEY (version_id) REFERENCES legal_source_versions(id) ON DELETE SET NULL,
    FOREIGN KEY (jurisdiction_id) REFERENCES legal_jurisdictions(id) ON DELETE RESTRICT,
    FOREIGN KEY (parent_provision_id) REFERENCES legal_provisions(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS legal_applicability_conditions (
    id TEXT PRIMARY KEY,
    provision_id TEXT NOT NULL,
    condition_type TEXT NOT NULL,
    operator TEXT NOT NULL DEFAULT 'EQUALS',
    condition_value TEXT NOT NULL,
    condition_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provision_id) REFERENCES legal_provisions(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS provision_provenances (
    id TEXT PRIMARY KEY,
    provision_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    official_uri TEXT NOT NULL,
    source_title TEXT NOT NULL,
    issuing_authority TEXT NOT NULL,
    document_identifier TEXT,
    publication_date TEXT,
    effective_date TEXT,
    version_label TEXT,
    content_hash TEXT,
    extraction_method TEXT NOT NULL DEFAULT 'MANUAL_CURATED',
    source_location_page TEXT,
    verification_state TEXT NOT NULL DEFAULT 'PENDING_VERIFICATION',
    verified_by TEXT,
    verified_at TIMESTAMP,
    verification_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (provision_id) REFERENCES legal_provisions(id) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES legal_sources(id) ON DELETE CASCADE,
    CONSTRAINT uq_provision_provenance UNIQUE (provision_id, source_id)
);
"""


def get_db_path(db_path: str = None) -> str:
    path = db_path or settings.DATABASE_PATH
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    return path


def get_connection(db_path: str = None) -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


@contextmanager
def get_db_context(db_path: str = None) -> Generator[sqlite3.Connection, None, None]:
    conn = get_connection(db_path)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str = None) -> None:
    """Initialize database tables and seed official legal authorities and jurisdictions."""
    with get_db_context(db_path) as conn:
        conn.executescript(SCHEMA_SQL)
        # Migrate existing documents table to include content_hash if missing
        try:
            conn.execute("ALTER TABLE documents ADD COLUMN content_hash TEXT")
        except sqlite3.OperationalError:
            pass  # column already exists

        # Seed core jurisdictions
        jurisdictions = [
            ("IN", "India (Central)", "CENTRAL", None),
            ("IN-DL", "National Capital Territory of Delhi", "UNION_TERRITORY", "IN"),
            ("IN-MH", "State of Maharashtra", "STATE", "IN"),
            ("IN-KA", "State of Karnataka", "STATE", "IN"),
            ("IN-TN", "State of Tamil Nadu", "STATE", "IN"),
            ("IN-TG", "State of Telangana", "STATE", "IN"),
            ("IN-HR", "State of Haryana", "STATE", "IN"),
            ("IN-UP", "State of Uttar Pradesh", "STATE", "IN"),
        ]
        conn.executemany(
            """
            INSERT OR IGNORE INTO legal_jurisdictions (id, name, jurisdiction_type, parent_jurisdiction_id)
            VALUES (?, ?, ?, ?)
            """,
            jurisdictions,
        )

        # Seed trusted official authorities
        authorities = [
            (
                "INDIA_CODE",
                "India Code: Digital Repository of All Central and State Acts",
                "https://www.indiacode.nic.in",
                "IN",
                "LEGISLATIVE",
                "Official repository of Central and State legislations maintained by the Legislative Department, Ministry of Law and Justice.",
            ),
            (
                "EG_INDIA",
                "The Gazette of India (e-Gazette)",
                "https://egazette.gov.in",
                "IN",
                "GAZETTE",
                "Official digital gazette publication authority under Directorate of Printing, Ministry of Housing and Urban Affairs.",
            ),
            (
                "MOLE",
                "Ministry of Labour and Employment, Government of India",
                "https://labour.gov.in",
                "IN",
                "EXECUTIVE",
                "Central ministry responsible for labour standards, employment codes, notifications and rules.",
            ),
            (
                "SCI",
                "Supreme Court of India",
                "https://main.sci.gov.in",
                "IN",
                "JUDICIAL",
                "Apex judicial authority interpreting Indian statutes and constitutional validity.",
            ),
            (
                "ECOURTS",
                "eCourts Services India",
                "https://ecourts.gov.in",
                "IN",
                "JUDICIAL",
                "National portal for judicial proceedings, High Court judgments and subordinate court registries.",
            ),
            (
                "MH_GAZETTE",
                "Maharashtra Government Gazette",
                "https://egazette.mahaonline.gov.in",
                "IN-MH",
                "GAZETTE",
                "Official state gazette portal for Maharashtra government notifications and rules.",
            ),
            (
                "KA_LABOUR",
                "Department of Labour, Government of Karnataka",
                "https://labour.karnataka.gov.in",
                "IN-KA",
                "EXECUTIVE",
                "State labour department issuing Karnataka state-specific rules, notifications, and minimum wage updates.",
            ),
        ]
        conn.executemany(
            """
            INSERT OR IGNORE INTO legal_authorities (id, name, official_url, jurisdiction_id, authority_type, description)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            authorities,
        )

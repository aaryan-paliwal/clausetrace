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
    """Initialize database tables."""
    with get_db_context(db_path) as conn:
        conn.executescript(SCHEMA_SQL)

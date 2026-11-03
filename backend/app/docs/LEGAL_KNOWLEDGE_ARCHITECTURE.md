# ClauseTrace — Indian Legal Knowledge Foundation Architecture (Iteration 2A)

## 1. Overview & Objectives

ClauseTrace is an evidence-grounded legal intelligence system initially specializing in the Indian corporate and employment ecosystem. 

Iteration 2A establishes an auditable, normalized, and jurisdiction-aware **Legal Knowledge Subsystem**. It decouples private user contracts and policies from official legal authorities, enabling future statutory compliance checks against:

- Central Acts and Codes (e.g. Code on Wages, 2019).
- State-specific Acts and Rules (e.g. Karnataka/Maharashtra state rules).
- Gazette notifications, amendments, and commencement orders.
- Section/subsection/clause hierarchies with explicit temporal and geographical scope.

---

## 2. Entity Relationship Diagram (ERD)

```mermaid
erDiagram
    LEGAL_JURISDICTION ||--o{ LEGAL_SOURCE : "applies within"
    LEGAL_AUTHORITY ||--o{ LEGAL_SOURCE : "publishes / issues"
    LEGAL_SOURCE ||--o{ LEGAL_SOURCE_VERSION : "tracks amendments"
    LEGAL_SOURCE ||--o{ LEGAL_PROVISION : "contains"
    LEGAL_SOURCE_VERSION ||--o{ LEGAL_PROVISION : "defines"
    LEGAL_PROVISION ||--o{ LEGAL_PROVISION : "parent of"
    LEGAL_PROVISION ||--o{ LEGAL_APPLICABILITY_CONDITION : "specifies"
    LEGAL_PROVISION ||--o{ PROVISION_PROVENANCE : "traceable via"

    LEGAL_JURISDICTION {
        string id PK "e.g. IN, IN-DL, IN-MH, IN-KA"
        string name "e.g. India (Central), State of Maharashtra"
        string jurisdiction_type "CENTRAL | STATE | UNION_TERRITORY | LOCAL"
        string parent_jurisdiction_id FK
    }

    LEGAL_AUTHORITY {
        string id PK "e.g. INDIA_CODE, EG_INDIA, MOLE, SCI"
        string name "e.g. India Code, The Gazette of India"
        string official_url "https://..."
        string jurisdiction_id FK
        string authority_type "LEGISLATIVE | EXECUTIVE | JUDICIAL | GAZETTE"
    }

    LEGAL_SOURCE {
        string id PK "Unique slug e.g. code-on-wages-2019"
        string title "Code on Wages, 2019"
        string short_title "Wages Code"
        string source_type "ACT | RULES | GAZETTE_NOTIFICATION | CIRCULAR"
        string authority_id FK
        string jurisdiction_id FK
        string citation_ref "Act No. 29 of 2019"
        date publication_date
        date enactment_date
        date effective_from
        date effective_to
        string content_hash "SHA-256 of text"
        string source_language "en"
        string ingestion_status "DISCOVERED | RETRIEVED | PARSED | VERIFIED | FAILED"
        string verification_status "PENDING_VERIFICATION | VERIFIED | REJECTED | SUPERSEDED"
    }

    LEGAL_SOURCE_VERSION {
        string id PK
        string source_id FK
        string version_label "e.g. Original Enacted Version"
        string version_type "ORIGINAL | AMENDED | CONSOLIDATED | REPEALED | NOT_IN_FORCE"
        date effective_from
        date effective_to
        boolean is_current
        string content_hash
    }

    LEGAL_PROVISION {
        string id PK
        string source_id FK
        string version_id FK
        string jurisdiction_id FK
        string parent_provision_id FK
        string part
        string chapter
        string section
        string subsection
        string clause_letter
        string heading
        text provision_text
        string citation_key "e.g. Code on Wages, 2019 § 6(1)"
        date effective_from
        date effective_to
        string status "ACTIVE | REPEALED | AMENDED | NOT_YET_ENFORCED"
    }

    LEGAL_APPLICABILITY_CONDITION {
        string id PK
        string provision_id FK
        string condition_type "JURISDICTION | ESTABLISHMENT_TYPE | INDUSTRY | EMPLOYEE_CATEGORY | THRESHOLD"
        string operator "EQUALS | IN | GTE | LTE | EXCLUDES"
        string condition_value
        text condition_description
    }

    PROVISION_PROVENANCE {
        string id PK
        string provision_id FK
        string source_id FK
        string official_uri
        string source_title
        string issuing_authority
        string document_identifier
        date publication_date
        date effective_date
        string content_hash "SHA-256 of provision"
        string extraction_method "MANUAL_CURATED | OFFICIAL_XML | PDF_PARSER"
        string verification_state "PENDING_VERIFICATION | VERIFIED | REJECTED | SUPERSEDED"
        string verified_by
        timestamp verified_at
        text verification_notes
    }
```

---

## 3. Provenance & Verification Policy

1. **Zero Auto-Verification:**  
   Every legal provision entering the system—regardless of whether parsed via PDF, text extraction, or manual curation—is strictly initialized with status `PENDING_VERIFICATION`. A parser success does **not** equal legal verification.
2. **Explicit Verification Audit:**  
   A provision can only transition to `VERIFIED` via an explicit audit endpoint (`PATCH /api/v1/legal/provisions/{id}/verification`), requiring the auditor's identity (`verified_by`), timestamp (`verified_at`), and verification notes.
3. **Immutable Content Hashing:**  
   Both legal source raw instruments and individual statutory provisions are hashed via SHA-256 (`content_hash`). If text alters, the hash mismatches and flags integrity violations.
4. **Historical Preservation:**  
   When amendments or consolidated revisions are introduced, historical versions are preserved with `effective_from` and `effective_to` dates. Historical records are never overwritten.

---

## 4. REST API Endpoints

Mounted under prefix `/api/v1/legal`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/jurisdictions` | List all supported central and state jurisdictions. |
| `GET` | `/authorities` | List trusted official sources (India Code, e-Gazette, MOLE, Supreme Court). |
| `POST` | `/sources` | Register a new authoritative legal instrument. |
| `GET` | `/sources` | List legal sources filtered by jurisdiction, type, or verification status. |
| `GET` | `/sources/{id}` | Get full source details and version history. |
| `POST` | `/sources/{id}/versions` | Register an amendment or consolidated version. |
| `POST` | `/sources/{id}/provisions` | Ingest structured legal provisions with provenance attached. |
| `GET` | `/sources/{id}/provisions` | List provisions under a specific source and version. |
| `GET` | `/provisions/{id}` | Retrieve provision details with provenance and applicability conditions. |
| `POST` | `/provisions/search` | Search provisions with structured filters (jurisdiction, effective date, query text). |
| `GET` | `/provisions/{id}/provenance` | Retrieve official URI, issuing authority, and verification state. |
| `PATCH` | `/provisions/{id}/verification` | Update verification status (audited transition to `VERIFIED` or `REJECTED`). |
| `POST` | `/corpus/seed-initial-codes` | Initialize initial corpus for the 4 central Labour Codes. |

---

## 5. PostgreSQL Migration Assessment

- **Current State:** The database layer operates on SQLite with WAL mode (`journal_mode=WAL; PRAGMA foreign_keys=ON;`).
- **PostgreSQL Compatibility:**  
  All 7 new tables use ANSI SQL syntax, standard types (`VARCHAR`, `TEXT`, `TIMESTAMP WITH TIME ZONE`, `BOOLEAN`), and strict composite/foreign-key constraints.
- **Migration Script:**  
  A drop-in PostgreSQL migration script has been authored at:  
  `backend/app/db/migrations/pg_legal_knowledge_v1.sql`.
- **Database Switch Strategy:**  
  When deploying against PostgreSQL 16+, configuring `DATABASE_URL=postgresql://user:password@host:5432/dbname` will allow replacing the connection provider in `app/db/database.py` seamlessly without requiring changes to table schema definitions.

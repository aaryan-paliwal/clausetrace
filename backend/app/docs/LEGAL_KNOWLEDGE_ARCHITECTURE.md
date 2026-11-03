# ClauseTrace — Indian Legal Knowledge Foundation Architecture (Iteration 2A & 2A.1)

## 1. Overview & Objectives

ClauseTrace is an evidence-grounded legal intelligence system specializing in the Indian corporate and employment ecosystem. 

Iteration 2A & 2A.1 establish an auditable, normalized, and jurisdiction-aware **Legal Knowledge Subsystem**. It decouples private user contracts and policies from official legal authorities, enabling statutory compliance checks against:

- Central Acts and Codes (e.g. Code on Wages, 2019; Industrial Relations Code, 2020; Code on Social Security, 2020; OSHWC Code, 2020).
- Official Gazette commencement notifications and section-level appointed dates.
- Subordinate Central and State Rules (e.g. draft/final rules notified by Central Government and states like Karnataka/Maharashtra).
- Section/subsection/clause hierarchies with explicit temporal and geographical scope.

---

## 2. Statutory Commencement & Gazette Ground Truth

Pursuant to official Central Government Gazette Notifications published on **21 November 2025** (reference: Press Information Bureau release **PIB PRID 2192463**), the four central Labour Codes were appointed to come into force on **21 November 2025**:

1. **Code on Wages, 2019 (Act No. 29 of 2019):**  
   Commenced via **S.O. 5322(E)** dated 21 November 2025.  
   - *Sections Commenced:* Sections 1 to 41, 42(4) to 42(9), 43 to 66, 67(1), 67(2)(a)-(r), (u)-(zc), 67(3)-(5), 68, 69.
   - *Provision-Level Exception:* Section 42(1) to 42(3) (Central and State Advisory Board constitution) were withheld from enforcement and marked `NOT_YET_ENFORCED`.
2. **Industrial Relations Code, 2020 (Act No. 35 of 2020):**  
   Commenced via **S.O. 5320(E)** dated 21 November 2025.
3. **Code on Social Security, 2020 (Act No. 36 of 2020):**  
   Commenced via **S.O. 5319(E)** dated 21 November 2025.
4. **Occupational Safety, Health and Working Conditions Code, 2020 (Act No. 37 of 2020):**  
   Commenced via **S.O. 5321(E)** dated 21 November 2025.

### Distinct Statutory Layers:
- **Act Commencement vs Subordinate Rules:** While the statutory provisions took effect on 2025-11-21, administrative rules notification occurs in separate tranches (Central Rules and State-level Rules published by individual state labor departments). The metadata schema explicitly tracks `rules_notification_status` and `state_rules_status` independently from Act `effective_from`.
- **Provision-Level Granularity:** Statutes do not always commence in full. ClauseTrace models status at the individual provision level (`ACTIVE`, `NOT_YET_ENFORCED`, `AMENDED`, `REPEALED`).

---

## 3. Entity Relationship Diagram (ERD)

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
        date effective_from "2025-11-21"
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
        date effective_from "2025-11-21"
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
        string official_uri "https://egazette.gov.in"
        string source_title
        string issuing_authority
        string document_identifier "S.O. 5322(E)"
        date publication_date
        date effective_date "2025-11-21"
        string content_hash "SHA-256 of provision"
        string extraction_method "MANUAL_CURATED | OFFICIAL_XML | PDF_PARSER"
        string verification_state "PENDING_VERIFICATION | VERIFIED | REJECTED | SUPERSEDED"
        string verified_by
        timestamp verified_at
        text verification_notes
    }
```

---

## 4. Provenance & Scoped Verification Security

1. **Zero Auto-Verification:**  
   Every legal provision entering the system—regardless of whether parsed via PDF, text extraction, or manual curation—is strictly initialized with status `PENDING_VERIFICATION`. A parser success does **not** equal legal verification.
2. **Scoped Auditor Authorization:**  
   Updates to statutory verification status (`PATCH /api/v1/legal/provisions/{id}/verification`) are guarded by the `X-Auditor-Key` header checked against `AUDITOR_API_KEY`. Unauthenticated or unauthorized callers receive `403 Forbidden`.
   > [!NOTE]
   > **Security Limitation Notice:** The auditor header provides scoped token authorization for Administrative/Auditor API interactions. Full enterprise multi-tenant RBAC or OAuth2 session management will be added when user account identity workflows are introduced in future platform iterations.
3. **Immutable Content Hashing:**  
   Both legal source raw instruments and individual statutory provisions are hashed via SHA-256 (`content_hash`). If text alters, the hash mismatches and flags integrity violations.
4. **Historical Preservation:**  
   When amendments or consolidated revisions are introduced, historical versions are preserved with `effective_from` and `effective_to` dates. Historical records are never overwritten.

---

## 5. REST API Endpoints

Mounted under prefix `/api/v1/legal`:

| Method | Endpoint | Authorization | Description |
| :--- | :--- | :--- | :--- |
| `GET` | `/jurisdictions` | Public | List all supported central and state jurisdictions. |
| `GET` | `/authorities` | Public | List trusted official sources (India Code, e-Gazette, MOLE, Supreme Court). |
| `POST` | `/sources` | Public | Register a new authoritative legal instrument. |
| `GET` | `/sources` | Public | List legal sources filtered by jurisdiction, type, or verification status. |
| `GET` | `/sources/{id}` | Public | Get full source details and version history. |
| `POST` | `/sources/{id}/versions` | Public | Register an amendment or consolidated version. |
| `POST` | `/sources/{id}/provisions` | Public | Ingest structured legal provisions with provenance attached. |
| `GET` | `/sources/{id}/provisions` | Public | List provisions under a specific source and version. |
| `GET` | `/provisions/{id}` | Public | Retrieve provision details with provenance and applicability conditions. |
| `POST` | `/provisions/search` | Public | Search provisions with structured filters (jurisdiction, effective date, query text). |
| `GET` | `/provisions/{id}/provenance` | Public | Retrieve official URI, issuing authority, and verification state. |
| `PATCH` | `/provisions/{id}/verification` | `X-Auditor-Key` | Update verification status (audited transition to `VERIFIED` or `REJECTED`). |
| `POST` | `/corpus/seed-initial-codes` | Public | Initialize initial corpus for the 4 central Labour Codes. |

---

## 6. PostgreSQL Migration Assessment & Operational Status

- **Current Runtime Persistence:**  
  The application runtime operates strictly on SQLite with Write-Ahead Logging (`journal_mode=WAL; PRAGMA foreign_keys=ON;`) located at `data/clausetrace.db`.
- **PostgreSQL Readiness (Schema DDL Level):**  
  All 7 legal knowledge foundation tables are prepared for PostgreSQL 16+ with complete ANSI DDL at:  
  `backend/app/db/migrations/pg_legal_knowledge_v1.sql`.
- **Operational Reality:**  
  PostgreSQL is **not** currently wired into the runtime `app/db/database.py` connection factory. The SQLite engine is the single active runtime store. When deploying against external PostgreSQL, configuring `DATABASE_URL` and switching the connection pool in `database.py` will activate the PostgreSQL tables without requiring table schema redesigns.

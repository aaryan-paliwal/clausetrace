-- PostgreSQL DDL Migration for ClauseTrace Legal Knowledge Foundation
-- Iteration 2A: Indian Legal Knowledge Subsystem

CREATE TABLE IF NOT EXISTS legal_jurisdictions (
    id VARCHAR(32) PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    jurisdiction_type VARCHAR(32) NOT NULL DEFAULT 'STATE', -- CENTRAL, STATE, UNION_TERRITORY, LOCAL
    parent_jurisdiction_id VARCHAR(32) REFERENCES legal_jurisdictions(id) ON DELETE RESTRICT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS legal_authorities (
    id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    official_url TEXT NOT NULL,
    jurisdiction_id VARCHAR(32) REFERENCES legal_jurisdictions(id) ON DELETE SET NULL,
    authority_type VARCHAR(64) NOT NULL DEFAULT 'LEGISLATIVE', -- LEGISLATIVE, EXECUTIVE, JUDICIAL, GAZETTE
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS legal_sources (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    short_title VARCHAR(128),
    source_type VARCHAR(64) NOT NULL, -- ACT, AMENDMENT_ACT, RULES, REGULATION, GAZETTE_NOTIFICATION, CIRCULAR, ORDER, JUDGMENT
    authority_id VARCHAR(64) REFERENCES legal_authorities(id) ON DELETE SET NULL,
    jurisdiction_id VARCHAR(32) NOT NULL REFERENCES legal_jurisdictions(id) ON DELETE RESTRICT,
    official_url TEXT,
    citation_ref VARCHAR(128),
    publication_date DATE,
    enactment_date DATE,
    effective_from DATE,
    effective_to DATE,
    content_hash VARCHAR(64),
    source_language VARCHAR(16) NOT NULL DEFAULT 'en',
    ingestion_status VARCHAR(32) NOT NULL DEFAULT 'DISCOVERED', -- DISCOVERED, RETRIEVED, PARSED, PENDING_VERIFICATION, VERIFIED, FAILED
    verification_status VARCHAR(32) NOT NULL DEFAULT 'PENDING_VERIFICATION', -- PENDING_VERIFICATION, VERIFIED, REJECTED, SUPERSEDED
    raw_text TEXT,
    metadata_json TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_legal_sources_citation_jurisdiction UNIQUE (citation_ref, jurisdiction_id)
);

CREATE TABLE IF NOT EXISTS legal_source_versions (
    id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) NOT NULL REFERENCES legal_sources(id) ON DELETE CASCADE,
    version_label VARCHAR(128) NOT NULL,
    version_type VARCHAR(32) NOT NULL DEFAULT 'ORIGINAL', -- ORIGINAL, AMENDED, CONSOLIDATED, REPEALED, NOT_IN_FORCE
    effective_from DATE,
    effective_to DATE,
    amendment_act_id VARCHAR(64) REFERENCES legal_sources(id) ON DELETE SET NULL,
    gazette_ref VARCHAR(255),
    content_hash VARCHAR(64),
    is_current BOOLEAN NOT NULL DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_source_version_label UNIQUE (source_id, version_label)
);

CREATE TABLE IF NOT EXISTS legal_provisions (
    id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) NOT NULL REFERENCES legal_sources(id) ON DELETE CASCADE,
    version_id VARCHAR(64) REFERENCES legal_source_versions(id) ON DELETE SET NULL,
    jurisdiction_id VARCHAR(32) NOT NULL REFERENCES legal_jurisdictions(id) ON DELETE RESTRICT,
    parent_provision_id VARCHAR(64) REFERENCES legal_provisions(id) ON DELETE SET NULL,
    part VARCHAR(64),
    chapter VARCHAR(64),
    section VARCHAR(32),
    subsection VARCHAR(32),
    clause_letter VARCHAR(32),
    subclause VARCHAR(32),
    rule_number VARCHAR(32),
    schedule_number VARCHAR(32),
    paragraph VARCHAR(32),
    heading TEXT,
    provision_text TEXT NOT NULL,
    citation_key VARCHAR(255),
    effective_from DATE,
    effective_to DATE,
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE', -- ACTIVE, REPEALED, AMENDED, NOT_YET_ENFORCED
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS legal_applicability_conditions (
    id VARCHAR(64) PRIMARY KEY,
    provision_id VARCHAR(64) NOT NULL REFERENCES legal_provisions(id) ON DELETE CASCADE,
    condition_type VARCHAR(64) NOT NULL, -- JURISDICTION, ESTABLISHMENT_TYPE, INDUSTRY, EMPLOYEE_CATEGORY, THRESHOLD, DATE_RANGE
    operator VARCHAR(32) NOT NULL DEFAULT 'EQUALS', -- EQUALS, IN, GTE, LTE, EXCLUDES
    condition_value TEXT NOT NULL,
    condition_description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS provision_provenances (
    id VARCHAR(64) PRIMARY KEY,
    provision_id VARCHAR(64) NOT NULL REFERENCES legal_provisions(id) ON DELETE CASCADE,
    source_id VARCHAR(64) NOT NULL REFERENCES legal_sources(id) ON DELETE CASCADE,
    official_uri TEXT NOT NULL,
    source_title VARCHAR(255) NOT NULL,
    issuing_authority VARCHAR(255) NOT NULL,
    document_identifier VARCHAR(128),
    publication_date DATE,
    effective_date DATE,
    version_label VARCHAR(128),
    content_hash VARCHAR(64),
    extraction_method VARCHAR(64) NOT NULL DEFAULT 'MANUAL_CURATED', -- MANUAL_CURATED, OFFICIAL_XML, PDF_PARSER
    source_location_page VARCHAR(64),
    verification_state VARCHAR(32) NOT NULL DEFAULT 'PENDING_VERIFICATION', -- DISCOVERED, RETRIEVED, PARSED, PENDING_VERIFICATION, VERIFIED, REJECTED, SUPERSEDED, FAILED
    verified_by VARCHAR(128),
    verified_at TIMESTAMP WITH TIME ZONE,
    verification_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_provision_provenance UNIQUE (provision_id, source_id)
);

CREATE INDEX IF NOT EXISTS idx_provisions_source ON legal_provisions(source_id);
CREATE INDEX IF NOT EXISTS idx_provisions_jurisdiction ON legal_provisions(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_provisions_effective ON legal_provisions(effective_from, effective_to);
CREATE INDEX IF NOT EXISTS idx_sources_jurisdiction ON legal_sources(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_sources_hash ON legal_sources(content_hash);

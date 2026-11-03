"""Pydantic models and schemas for Indian Legal Knowledge Foundation."""
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class JurisdictionType(str, Enum):
    CENTRAL = "CENTRAL"
    STATE = "STATE"
    UNION_TERRITORY = "UNION_TERRITORY"
    LOCAL = "LOCAL"


class LegalAuthorityType(str, Enum):
    LEGISLATIVE = "LEGISLATIVE"
    EXECUTIVE = "EXECUTIVE"
    JUDICIAL = "JUDICIAL"
    GAZETTE = "GAZETTE"


class LegalSourceType(str, Enum):
    ACT = "ACT"
    AMENDMENT_ACT = "AMENDMENT_ACT"
    RULES = "RULES"
    REGULATION = "REGULATION"
    GAZETTE_NOTIFICATION = "GAZETTE_NOTIFICATION"
    CIRCULAR = "CIRCULAR"
    ORDER = "ORDER"
    JUDGMENT = "JUDGMENT"
    OTHER = "OTHER"


class LegalIngestionStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    RETRIEVED = "RETRIEVED"
    PARSED = "PARSED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"


class LegalVerificationStatus(str, Enum):
    DISCOVERED = "DISCOVERED"
    RETRIEVED = "RETRIEVED"
    PARSED = "PARSED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"
    SUPERSEDED = "SUPERSEDED"
    FAILED = "FAILED"


class LegalVersionType(str, Enum):
    ORIGINAL = "ORIGINAL"
    AMENDED = "AMENDED"
    CONSOLIDATED = "CONSOLIDATED"
    REPEALED = "REPEALED"
    NOT_IN_FORCE = "NOT_IN_FORCE"


class ProvisionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    REPEALED = "REPEALED"
    AMENDED = "AMENDED"
    NOT_YET_ENFORCED = "NOT_YET_ENFORCED"


class ApplicabilityConditionType(str, Enum):
    JURISDICTION = "JURISDICTION"
    ESTABLISHMENT_TYPE = "ESTABLISHMENT_TYPE"
    INDUSTRY = "INDUSTRY"
    EMPLOYEE_CATEGORY = "EMPLOYEE_CATEGORY"
    THRESHOLD = "THRESHOLD"
    DATE_RANGE = "DATE_RANGE"


# ---------------------------------------------------------------------------
# JURISDICTION & AUTHORITY SCHEMAS
# ---------------------------------------------------------------------------

class LegalJurisdictionBase(BaseModel):
    id: str = Field(..., description="Stable ISO or standard jurisdiction code e.g. IN, IN-DL, IN-MH")
    name: str = Field(..., description="Official title e.g. India (Central), State of Maharashtra")
    jurisdiction_type: JurisdictionType = JurisdictionType.STATE
    parent_jurisdiction_id: Optional[str] = None


class LegalJurisdictionResponse(LegalJurisdictionBase):
    created_at: Optional[str] = None


class LegalAuthorityBase(BaseModel):
    id: str = Field(..., description="Authority identifier e.g. INDIA_CODE, MOLE, SCI")
    name: str = Field(..., description="Full official title of authority")
    official_url: str = Field(..., description="Authoritative official URL")
    jurisdiction_id: Optional[str] = "IN"
    authority_type: LegalAuthorityType = LegalAuthorityType.LEGISLATIVE
    description: Optional[str] = None


class LegalAuthorityResponse(LegalAuthorityBase):
    created_at: Optional[str] = None


# ---------------------------------------------------------------------------
# LEGAL SOURCE & VERSION SCHEMAS
# ---------------------------------------------------------------------------

class LegalSourceCreate(BaseModel):
    id: str = Field(..., description="Unique slug or identifier e.g. code-on-wages-2019")
    title: str = Field(..., description="Full official title of Act or Legal Instrument")
    short_title: Optional[str] = None
    source_type: LegalSourceType = LegalSourceType.ACT
    authority_id: Optional[str] = None
    jurisdiction_id: str = Field("IN", description="Jurisdiction code (IN, IN-MH, etc.)")
    official_url: Optional[str] = None
    citation_ref: Optional[str] = Field(None, description="e.g. Act No. 29 of 2019")
    publication_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    enactment_date: Optional[str] = Field(None, description="YYYY-MM-DD")
    effective_from: Optional[str] = Field(None, description="Commencement/effective date YYYY-MM-DD")
    effective_to: Optional[str] = Field(None, description="Date repealed or superseded if applicable")
    content_hash: Optional[str] = None
    source_language: str = "en"
    raw_text: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class LegalSourceVersionCreate(BaseModel):
    version_label: str = Field(..., description="e.g. As enacted, 2020 Consolidate")
    version_type: LegalVersionType = LegalVersionType.ORIGINAL
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    amendment_act_id: Optional[str] = None
    gazette_ref: Optional[str] = None
    content_hash: Optional[str] = None
    is_current: bool = True
    notes: Optional[str] = None


class LegalSourceVersionResponse(BaseModel):
    id: str
    source_id: str
    version_label: str
    version_type: str
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    amendment_act_id: Optional[str] = None
    gazette_ref: Optional[str] = None
    content_hash: Optional[str] = None
    is_current: bool = False
    notes: Optional[str] = None
    created_at: Optional[str] = None


class LegalSourceResponse(BaseModel):
    id: str
    title: str
    short_title: Optional[str] = None
    source_type: str
    authority_id: Optional[str] = None
    jurisdiction_id: str
    official_url: Optional[str] = None
    citation_ref: Optional[str] = None
    publication_date: Optional[str] = None
    enactment_date: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    content_hash: Optional[str] = None
    source_language: str = "en"
    ingestion_status: str
    verification_status: str
    raw_text: Optional[str] = None
    metadata_json: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    versions: List[LegalSourceVersionResponse] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# LEGAL PROVISION & PROVENANCE SCHEMAS
# ---------------------------------------------------------------------------

class LegalApplicabilityConditionSchema(BaseModel):
    condition_type: ApplicabilityConditionType
    operator: str = "EQUALS"
    condition_value: str
    condition_description: Optional[str] = None


class ProvisionProvenanceResponse(BaseModel):
    id: str
    provision_id: str
    source_id: str
    official_uri: str
    source_title: str
    issuing_authority: str
    document_identifier: Optional[str] = None
    publication_date: Optional[str] = None
    effective_date: Optional[str] = None
    version_label: Optional[str] = None
    content_hash: Optional[str] = None
    extraction_method: str = "MANUAL_CURATED"
    source_location_page: Optional[str] = None
    verification_state: str
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    verification_notes: Optional[str] = None
    created_at: Optional[str] = None


class LegalProvisionCreate(BaseModel):
    source_id: str
    version_id: Optional[str] = None
    jurisdiction_id: str = "IN"
    parent_provision_id: Optional[str] = None
    part: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    clause_letter: Optional[str] = None
    subclause: Optional[str] = None
    rule_number: Optional[str] = None
    schedule_number: Optional[str] = None
    paragraph: Optional[str] = None
    heading: Optional[str] = None
    provision_text: str
    citation_key: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    status: ProvisionStatus = ProvisionStatus.ACTIVE
    applicability_conditions: List[LegalApplicabilityConditionSchema] = Field(default_factory=list)
    # Provenance fields for ingestion
    official_uri: Optional[str] = None
    source_title: Optional[str] = None
    issuing_authority: Optional[str] = None
    document_identifier: Optional[str] = None
    source_location_page: Optional[str] = None
    extraction_method: str = "MANUAL_CURATED"


class LegalProvisionResponse(BaseModel):
    id: str
    source_id: str
    version_id: Optional[str] = None
    jurisdiction_id: str
    parent_provision_id: Optional[str] = None
    part: Optional[str] = None
    chapter: Optional[str] = None
    section: Optional[str] = None
    subsection: Optional[str] = None
    clause_letter: Optional[str] = None
    subclause: Optional[str] = None
    rule_number: Optional[str] = None
    schedule_number: Optional[str] = None
    paragraph: Optional[str] = None
    heading: Optional[str] = None
    provision_text: str
    citation_key: Optional[str] = None
    effective_from: Optional[str] = None
    effective_to: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    provenance: Optional[ProvisionProvenanceResponse] = None
    applicability_conditions: List[Dict[str, Any]] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# SEARCH & VERIFICATION SCHEMAS
# ---------------------------------------------------------------------------

class LegalSearchFilter(BaseModel):
    query: Optional[str] = None
    source_id: Optional[str] = None
    jurisdiction_id: Optional[str] = None
    section: Optional[str] = None
    rule_number: Optional[str] = None
    status: Optional[str] = None
    active_on_date: Optional[str] = Field(None, description="Check if provision in effect on YYYY-MM-DD")
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)


class VerificationUpdateRequest(BaseModel):
    verification_state: LegalVerificationStatus
    verified_by: str = Field(..., description="User, Auditor or System process identifier")
    verification_notes: Optional[str] = None

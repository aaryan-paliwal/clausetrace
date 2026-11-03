"""REST API router for Indian Legal Knowledge Foundation."""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, Query, status

from app.config import settings
from app.db.database import get_db_context
from app.db.repository import Repository
from app.engines.legal_ingestion import LegalIngestionEngine, seed_initial_indian_legal_corpus
from app.llm.legal_schemas import (
    LegalAuthorityResponse,
    LegalJurisdictionResponse,
    LegalProvisionCreate,
    LegalProvisionResponse,
    LegalSearchFilter,
    LegalSourceCreate,
    LegalSourceResponse,
    LegalSourceVersionCreate,
    LegalSourceVersionResponse,
    ProvisionProvenanceResponse,
    VerificationUpdateRequest,
)

router = APIRouter(prefix="/api/v1/legal", tags=["Legal Knowledge"])


def verify_auditor_access(
    x_auditor_key: Optional[str] = Header(None, alias="X-Auditor-Key"),
) -> str:
    """
    Scoped auditor authorization check for statutory verification state updates.

    Security Model & Scope Limitation:
    This check verifies an administrative auditor key supplied via the 'X-Auditor-Key'
    HTTP header against the configured 'AUDITOR_API_KEY'. It ensures that unauthenticated
    or general-public client requests cannot modify statutory provenance or verification records.
    NOTE: This is a scoped API authorization mechanism and does not constitute full enterprise
    multi-tenant RBAC or OAuth2 session management, which will be implemented in subsequent
    iterations when user identities are integrated into the platform.
    """
    expected_key = getattr(settings, "AUDITOR_API_KEY", "clausetrace-dev-auditor-key")
    if not x_auditor_key or x_auditor_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Auditor authorization required: Invalid or missing 'X-Auditor-Key' header.",
        )
    return x_auditor_key


# ---------------------------------------------------------------------------
# JURISDICTIONS & AUTHORITIES
# ---------------------------------------------------------------------------

@router.get("/jurisdictions", response_model=List[LegalJurisdictionResponse])
async def list_jurisdictions() -> List[Dict[str, Any]]:
    """List supported Indian central, state, and territorial jurisdictions."""
    with get_db_context() as conn:
        repo = Repository(conn)
        return repo.list_jurisdictions()


@router.get("/authorities", response_model=List[LegalAuthorityResponse])
async def list_authorities(jurisdiction_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """List trusted official Indian legal authorities and gazette portals."""
    with get_db_context() as conn:
        repo = Repository(conn)
        return repo.list_authorities(jurisdiction_id=jurisdiction_id)


# ---------------------------------------------------------------------------
# LEGAL SOURCES
# ---------------------------------------------------------------------------

@router.post("/sources", response_model=LegalSourceResponse, status_code=status.HTTP_201_CREATED)
async def register_legal_source(source_in: LegalSourceCreate) -> Dict[str, Any]:
    """Register an authoritative Indian legal instrument (Act, Rules, Notification)."""
    engine = LegalIngestionEngine()
    try:
        created = engine.register_source(source_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    with get_db_context() as conn:
        repo = Repository(conn)
        versions = repo.list_source_versions(created["id"])
        created["versions"] = versions
    return created


@router.get("/sources", response_model=List[LegalSourceResponse])
async def list_legal_sources(
    jurisdiction_id: Optional[str] = Query(None, description="Filter by jurisdiction code e.g. IN, IN-DL"),
    source_type: Optional[str] = Query(None, description="Filter by ACT, RULES, GAZETTE_NOTIFICATION, etc."),
    verification_status: Optional[str] = Query(None, description="Filter by verification state"),
) -> List[Dict[str, Any]]:
    """List registered legal sources matching optional filter criteria."""
    with get_db_context() as conn:
        repo = Repository(conn)
        sources = repo.list_legal_sources(
            jurisdiction_id=jurisdiction_id,
            source_type=source_type,
            verification_status=verification_status,
        )
        for s in sources:
            s["versions"] = repo.list_source_versions(s["id"])
        return sources


@router.get("/sources/{source_id}", response_model=LegalSourceResponse)
async def get_legal_source(source_id: str) -> Dict[str, Any]:
    """Retrieve full details of an authoritative legal source, including version history."""
    with get_db_context() as conn:
        repo = Repository(conn)
        source = repo.get_legal_source(source_id)
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Legal source '{source_id}' not found.")
        source["versions"] = repo.list_source_versions(source_id)
        return source


@router.post("/sources/{source_id}/versions", response_model=LegalSourceVersionResponse, status_code=status.HTTP_201_CREATED)
async def register_source_version(source_id: str, version_in: LegalSourceVersionCreate) -> Dict[str, Any]:
    """Register an amendment, consolidated, or revised version of an existing legal source."""
    engine = LegalIngestionEngine()
    try:
        return engine.create_version(source_id, version_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


# ---------------------------------------------------------------------------
# PROVISION INGESTION & SEARCH
# ---------------------------------------------------------------------------

@router.post("/sources/{source_id}/provisions", response_model=List[LegalProvisionResponse], status_code=status.HTTP_201_CREATED)
async def ingest_source_provisions(source_id: str, provisions: List[LegalProvisionCreate]) -> List[Dict[str, Any]]:
    """
    Ingest parsed or curated legal provisions under an authoritative source.
    All provisions are stamped with provenance and set to PENDING_VERIFICATION.
    """
    engine = LegalIngestionEngine()
    try:
        created_provisions = engine.ingest_provisions(source_id, provisions)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    with get_db_context() as conn:
        repo = Repository(conn)
        res = []
        for p in created_provisions:
            p["provenance"] = repo.get_provision_provenance(p["id"])
            p["applicability_conditions"] = repo.list_conditions_for_provision(p["id"])
            res.append(p)
        return res


@router.get("/sources/{source_id}/provisions", response_model=List[LegalProvisionResponse])
async def list_provisions_for_source(source_id: str, version_id: Optional[str] = Query(None)) -> List[Dict[str, Any]]:
    """List all provisions belonging to a source (optionally restricted to a specific version)."""
    with get_db_context() as conn:
        repo = Repository(conn)
        source = repo.get_legal_source(source_id)
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Legal source '{source_id}' not found.")
        provisions = repo.list_provisions_for_source(source_id, version_id=version_id)
        for p in provisions:
            p["provenance"] = repo.get_provision_provenance(p["id"])
            p["applicability_conditions"] = repo.list_conditions_for_provision(p["id"])
        return provisions


@router.get("/provisions/{provision_id}", response_model=LegalProvisionResponse)
async def get_legal_provision(provision_id: str) -> Dict[str, Any]:
    """Retrieve a single legal provision with full provenance and applicability conditions."""
    with get_db_context() as conn:
        repo = Repository(conn)
        prov = repo.get_legal_provision(provision_id)
        if not prov:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provision '{provision_id}' not found.")
        prov["provenance"] = repo.get_provision_provenance(provision_id)
        prov["applicability_conditions"] = repo.list_conditions_for_provision(provision_id)
        return prov


@router.post("/provisions/search", response_model=List[LegalProvisionResponse])
async def search_provisions(filters: LegalSearchFilter) -> List[Dict[str, Any]]:
    """
    Search legal provisions using structured legal filters:
    - Text query match (provisions, headings, citation keys)
    - Jurisdiction filter (e.g. IN, IN-MH)
    - Effective date filter (provisions in force on given date)
    - Source, section, and status filters
    """
    with get_db_context() as conn:
        repo = Repository(conn)
        provisions = repo.search_provisions(
            query_text=filters.query,
            source_id=filters.source_id,
            jurisdiction_id=filters.jurisdiction_id,
            section=filters.section,
            rule_number=filters.rule_number,
            status=filters.status,
            active_on_date=filters.active_on_date,
            limit=filters.limit,
            offset=filters.offset,
        )
        for p in provisions:
            p["provenance"] = repo.get_provision_provenance(p["id"])
            p["applicability_conditions"] = repo.list_conditions_for_provision(p["id"])
        return provisions


# ---------------------------------------------------------------------------
# PROVENANCE & VERIFICATION AUDIT WORKFLOW
# ---------------------------------------------------------------------------

@router.get("/provisions/{provision_id}/provenance", response_model=ProvisionProvenanceResponse)
async def get_provision_provenance(provision_id: str) -> Dict[str, Any]:
    """Retrieve authoritative provenance, original URL, content hash and verification history."""
    with get_db_context() as conn:
        repo = Repository(conn)
        prov = repo.get_legal_provision(provision_id)
        if not prov:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provision '{provision_id}' not found.")
        provenance = repo.get_provision_provenance(provision_id)
        if not provenance:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provenance not found for provision.")
        return provenance


@router.patch("/provisions/{provision_id}/verification", response_model=ProvisionProvenanceResponse)
async def update_provision_verification_state(
    provision_id: str,
    req: VerificationUpdateRequest,
    _auditor_key: str = Depends(verify_auditor_access),
) -> Dict[str, Any]:
    """
    Audit and update the legal verification status of a provision.
    Transitions can mark a provision as VERIFIED, REJECTED, SUPERSEDED, etc., with auditor attribution.

    Requires scoped auditor authorization via 'X-Auditor-Key' header.
    """
    with get_db_context() as conn:
        repo = Repository(conn)
        prov = repo.get_legal_provision(provision_id)
        if not prov:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provision '{provision_id}' not found.")

        updated = repo.update_provenance_verification(
            provision_id=provision_id,
            verification_state=req.verification_state.value,
            verified_by=req.verified_by,
            verification_notes=req.verification_notes,
        )
        return updated


# ---------------------------------------------------------------------------
# CORPUS INITIALIZATION
# ---------------------------------------------------------------------------

@router.post("/corpus/seed-initial-codes", status_code=status.HTTP_200_OK)
async def seed_corpus() -> Dict[str, Any]:
    """Initialize structured records for the 4 central Labour Codes (Code on Wages, IR, Social Security, OSHWC)."""
    return seed_initial_indian_legal_corpus()

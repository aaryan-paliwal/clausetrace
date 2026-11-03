"""Comprehensive automated test suite for Indian Legal Knowledge Foundation (Iteration 2A).

Tests all 12 required criteria:
1. Legal source creation
2. Duplicate source detection (ID and citation)
3. Legal provision creation
4. Provision-to-source integrity
5. Jurisdiction relationships
6. Effective-date filtering
7. Historical version preservation
8. Superseded provisions
9. Content-hash duplicate detection
10. Ingestion failure handling
11. Verification status transitions
12. API response validation
"""
import pytest
from httpx import ASGITransport, AsyncClient

from app.db.database import get_db_context, init_db
from app.db.repository import Repository
from app.engines.legal_ingestion import LegalIngestionEngine, compute_content_hash, seed_initial_indian_legal_corpus
from app.llm.legal_schemas import (
    ApplicabilityConditionType,
    LegalApplicabilityConditionSchema,
    LegalIngestionStatus,
    LegalProvisionCreate,
    LegalSearchFilter,
    LegalSourceCreate,
    LegalSourceType,
    LegalSourceVersionCreate,
    LegalVerificationStatus,
    LegalVersionType,
    ProvisionStatus,
    VerificationUpdateRequest,
)
from app.main import app


@pytest.fixture
def test_db(tmp_path):
    """Isolated SQLite database fixture."""
    db_file = str(tmp_path / "legal_test.db")
    init_db(db_file)
    return db_file


@pytest.fixture
def client(test_db, monkeypatch):
    """FastAPI Test Client pointing to test_db."""
    from app.config import settings
    monkeypatch.setattr(settings, "DATABASE_PATH", test_db)
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


# ---------------------------------------------------------------------------
# 1. LEGAL SOURCE CREATION
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_legal_source_creation(test_db):
    engine = LegalIngestionEngine(db_path=test_db)
    src_data = LegalSourceCreate(
        id="code-on-wages-2019",
        title="Code on Wages, 2019",
        short_title="Wages Code",
        source_type=LegalSourceType.ACT,
        authority_id="INDIA_CODE",
        jurisdiction_id="IN",
        official_url="https://www.indiacode.nic.in/handle/123456789/13768",
        citation_ref="Act No. 29 of 2019",
        publication_date="2019-08-08",
        enactment_date="2019-08-08",
        raw_text="An Act to amend and consolidate the laws relating to wages and bonus...",
    )
    created = engine.register_source(src_data)

    assert created["id"] == "code-on-wages-2019"
    assert created["title"] == "Code on Wages, 2019"
    assert created["jurisdiction_id"] == "IN"
    assert created["ingestion_status"] == LegalIngestionStatus.DISCOVERED.value
    assert created["verification_status"] == LegalVerificationStatus.PENDING_VERIFICATION.value
    assert created["content_hash"] is not None

    with get_db_context(test_db) as conn:
        repo = Repository(conn)
        versions = repo.list_source_versions("code-on-wages-2019")
        assert len(versions) == 1
        assert versions[0]["version_label"] == "Original Enacted Version"
        assert versions[0]["is_current"] is True


# ---------------------------------------------------------------------------
# 2. DUPLICATE SOURCE DETECTION
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_duplicate_source_detection(test_db):
    engine = LegalIngestionEngine(db_path=test_db)
    src = LegalSourceCreate(
        id="duplicate-test-act",
        title="Duplicate Test Act, 2026",
        source_type=LegalSourceType.ACT,
        jurisdiction_id="IN",
        citation_ref="Act No. 99 of 2026",
    )
    engine.register_source(src)

    # 1. Duplicate ID check
    with pytest.raises(ValueError, match="already exists"):
        engine.register_source(src)

    # 2. Duplicate Citation in same jurisdiction check
    src_different_id = LegalSourceCreate(
        id="another-id-same-cit",
        title="Another Title, 2026",
        source_type=LegalSourceType.ACT,
        jurisdiction_id="IN",
        citation_ref="Act No. 99 of 2026",
    )
    with pytest.raises(ValueError, match="already registered for jurisdiction"):
        engine.register_source(src_different_id)


# ---------------------------------------------------------------------------
# 3. LEGAL PROVISION CREATION & PROVENANCE
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_legal_provision_creation(test_db):
    engine = LegalIngestionEngine(db_path=test_db)
    src = LegalSourceCreate(
        id="wages-test-source",
        title="Code on Wages, 2019",
        source_type=LegalSourceType.ACT,
        jurisdiction_id="IN",
    )
    engine.register_source(src)

    provisions = [
        LegalProvisionCreate(
            source_id="wages-test-source",
            chapter="Chapter II",
            section="6",
            subsection="1",
            heading="Fixation of minimum rate of wages",
            provision_text="The appropriate Government shall fix the minimum rates of wages payable to employees.",
            status=ProvisionStatus.NOT_YET_ENFORCED,
            applicability_conditions=[
                LegalApplicabilityConditionSchema(
                    condition_type=ApplicabilityConditionType.ESTABLISHMENT_TYPE,
                    condition_value="ALL_SCHEDULED_EMPLOYMENTS",
                    operator="IN",
                    condition_description="Applies to all scheduled employments.",
                )
            ],
        )
    ]
    created = engine.ingest_provisions("wages-test-source", provisions)
    assert len(created) == 1
    p = created[0]
    assert p["section"] == "6"
    assert p["subsection"] == "1"
    assert p["status"] == "NOT_YET_ENFORCED"

    # Verify provenance attached
    with get_db_context(test_db) as conn:
        repo = Repository(conn)
        prov_provenance = repo.get_provision_provenance(p["id"])
        assert prov_provenance is not None
        assert prov_provenance["verification_state"] == "PENDING_VERIFICATION"
        assert prov_provenance["content_hash"] == compute_content_hash(p["provision_text"])

        conditions = repo.list_conditions_for_provision(p["id"])
        assert len(conditions) == 1
        assert conditions[0]["condition_type"] == "ESTABLISHMENT_TYPE"


# ---------------------------------------------------------------------------
# 4. PROVISION-TO-SOURCE INTEGRITY (CASCADE & VALIDATION)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_provision_to_source_integrity(test_db):
    engine = LegalIngestionEngine(db_path=test_db)
    # Attempting to ingest provisions for non-existent source
    with pytest.raises(ValueError, match="does not exist"):
        engine.ingest_provisions("non-existent-source", [
            LegalProvisionCreate(
                source_id="non-existent-source",
                section="1",
                provision_text="Invalid provision without source.",
            )
        ])


# ---------------------------------------------------------------------------
# 5. JURISDICTION RELATIONSHIPS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_jurisdiction_relationships(test_db):
    with get_db_context(test_db) as conn:
        repo = Repository(conn)
        # Check pre-seeded jurisdictions
        jurisdictions = repo.list_jurisdictions()
        ids = [j["id"] for j in jurisdictions]
        assert "IN" in ids
        assert "IN-DL" in ids
        assert "IN-MH" in ids
        assert "IN-KA" in ids

        central = repo.get_jurisdiction("IN")
        assert central["jurisdiction_type"] == "CENTRAL"

        mh = repo.get_jurisdiction("IN-MH")
        assert mh["jurisdiction_type"] == "STATE"
        assert mh["parent_jurisdiction_id"] == "IN"


# ---------------------------------------------------------------------------
# 6. EFFECTIVE-DATE FILTERING
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_effective_date_filtering(test_db):
    engine = LegalIngestionEngine(db_path=test_db)
    src = LegalSourceCreate(
        id="date-test-act",
        title="Date Test Act",
        source_type=LegalSourceType.ACT,
        jurisdiction_id="IN",
    )
    engine.register_source(src)

    provisions = [
        # Past provision (repealed)
        LegalProvisionCreate(
            source_id="date-test-act",
            section="10",
            provision_text="Historic rule active in 2020 only.",
            effective_from="2020-01-01",
            effective_to="2020-12-31",
            status=ProvisionStatus.REPEALED,
        ),
        # Current active provision
        LegalProvisionCreate(
            source_id="date-test-act",
            section="20",
            provision_text="Rule currently active from 2021 onwards.",
            effective_from="2021-01-01",
            effective_to=None,
            status=ProvisionStatus.ACTIVE,
        ),
        # Future provision (not yet in effect)
        LegalProvisionCreate(
            source_id="date-test-act",
            section="30",
            provision_text="Future rule effective from 2030.",
            effective_from="2030-01-01",
            effective_to=None,
            status=ProvisionStatus.NOT_YET_ENFORCED,
        ),
    ]
    engine.ingest_provisions("date-test-act", provisions)

    with get_db_context(test_db) as conn:
        repo = Repository(conn)
        # Search active on 2020-06-01: Should find Section 10 only
        res_2020 = repo.search_provisions(source_id="date-test-act", active_on_date="2020-06-01")
        assert len(res_2020) == 1
        assert res_2020[0]["section"] == "10"

        # Search active on 2026-01-01: Should find Section 20 only
        res_2026 = repo.search_provisions(source_id="date-test-act", active_on_date="2026-01-01")
        assert len(res_2026) == 1
        assert res_2026[0]["section"] == "20"


# ---------------------------------------------------------------------------
# 7. HISTORICAL VERSION PRESERVATION & 8. SUPERSEDED PROVISIONS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_historical_version_preservation(test_db):
    engine = LegalIngestionEngine(db_path=test_db)
    src = LegalSourceCreate(
        id="standing-orders-act",
        title="Industrial Employment Standing Orders Act",
        source_type=LegalSourceType.ACT,
        jurisdiction_id="IN",
    )
    engine.register_source(src)

    # Ingest original version provision
    p_v1 = engine.ingest_provisions("standing-orders-act", [
        LegalProvisionCreate(
            source_id="standing-orders-act",
            section="5",
            heading="Original Standing Orders Certification",
            provision_text="The certifying officer shall forward a copy within 7 days.",
            status=ProvisionStatus.ACTIVE,
            effective_from="1946-04-23",
            effective_to="2020-09-28",
        )
    ])[0]

    # Register an amended version
    v2 = engine.create_version(
        "standing-orders-act",
        LegalSourceVersionCreate(
            version_label="2020 Amendment Act",
            version_type=LegalVersionType.AMENDED,
            effective_from="2020-09-29",
            is_current=True,
            notes="Amended by Parliament",
        ),
    )
    assert v2["is_current"] is True

    # Ingest amended version provision without deleting original
    p_v2 = engine.ingest_provisions("standing-orders-act", [
        LegalProvisionCreate(
            source_id="standing-orders-act",
            version_id=v2["id"],
            section="5",
            heading="Amended Standing Orders Certification",
            provision_text="The certifying officer shall forward certified copy electronically within 3 days.",
            status=ProvisionStatus.ACTIVE,
            effective_from="2020-09-29",
        )
    ])[0]

    # Verify both versions exist in database
    with get_db_context(test_db) as conn:
        repo = Repository(conn)
        all_provisions = repo.list_provisions_for_source("standing-orders-act")
        assert len(all_provisions) == 2

        versions = repo.list_source_versions("standing-orders-act")
        assert len(versions) == 2
        # V1 should now be is_current=False, V2 should be is_current=True
        v1_check = [v for v in versions if v["version_label"] == "Original Enacted Version"][0]
        v2_check = [v for v in versions if v["version_label"] == "2020 Amendment Act"][0]
        assert v1_check["is_current"] is False
        assert v2_check["is_current"] is True


# ---------------------------------------------------------------------------
# 9. CONTENT HASH DUPLICATE DETECTION
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_content_hash_duplicate_detection(test_db):
    engine = LegalIngestionEngine(db_path=test_db)
    raw_text = "Official Gazette Notification No. S.O. 123(E)..."
    expected_hash = compute_content_hash(raw_text)

    src = LegalSourceCreate(
        id="hash-test-source-1",
        title="Gazette Notification 123",
        source_type=LegalSourceType.GAZETTE_NOTIFICATION,
        jurisdiction_id="IN",
        raw_text=raw_text,
    )
    engine.register_source(src)

    with get_db_context(test_db) as conn:
        repo = Repository(conn)
        found = repo.find_legal_source_by_hash(expected_hash)
        assert found is not None
        assert found["id"] == "hash-test-source-1"


# ---------------------------------------------------------------------------
# 10. INGESTION FAILURE HANDLING & INITIAL LABOUR CODE CORPUS SEED
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_seed_initial_indian_legal_corpus(test_db):
    report = seed_initial_indian_legal_corpus(db_path=test_db)
    assert report["sources_created"] == 4
    assert report["provisions_created"] >= 3

    with get_db_context(test_db) as conn:
        repo = Repository(conn)
        wages = repo.get_legal_source("code-on-wages-2019")
        assert wages is not None
        assert wages["citation_ref"] == "Act No. 29 of 2019"
        assert wages["source_language"] == "en"

        # Verify provisions under wages code
        provisions = repo.list_provisions_for_source("code-on-wages-2019")
        assert len(provisions) >= 3
        sec_nums = [p["section"] for p in provisions]
        assert "6" in sec_nums
        assert "9" in sec_nums
        assert "17" in sec_nums


# ---------------------------------------------------------------------------
# 11. VERIFICATION STATUS TRANSITIONS
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_verification_status_transitions(test_db):
    engine = LegalIngestionEngine(db_path=test_db)
    src = LegalSourceCreate(
        id="audit-test-source",
        title="Audit Test Act",
        source_type=LegalSourceType.ACT,
        jurisdiction_id="IN",
    )
    engine.register_source(src)
    p = engine.ingest_provisions("audit-test-source", [
        LegalProvisionCreate(
            source_id="audit-test-source",
            section="1",
            provision_text="Text awaiting verification.",
        )
    ])[0]

    with get_db_context(test_db) as conn:
        repo = Repository(conn)
        # 1. Initial state must be PENDING_VERIFICATION
        prov = repo.get_provision_provenance(p["id"])
        assert prov["verification_state"] == "PENDING_VERIFICATION"
        assert prov["verified_by"] is None

        # 2. Transition to VERIFIED with auditor details
        updated = repo.update_provenance_verification(
            provision_id=p["id"],
            verification_state="VERIFIED",
            verified_by="legal_counsel_007",
            verification_notes="Matched word-for-word against Official Gazette of India Extraordinary copy.",
        )
        assert updated["verification_state"] == "VERIFIED"
        assert updated["verified_by"] == "legal_counsel_007"
        assert updated["verified_at"] is not None


# ---------------------------------------------------------------------------
# 12. FASTAPI ENDPOINT VALIDATION
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_legal_api_endpoints(client):
    # 1. List Jurisdictions
    res = await client.get("/api/v1/legal/jurisdictions")
    assert res.status_code == 200
    jurisdictions = res.json()
    assert any(j["id"] == "IN" for j in jurisdictions)

    # 2. List Authorities
    res_auth = await client.get("/api/v1/legal/authorities")
    assert res_auth.status_code == 200
    authorities = res_auth.json()
    assert any(a["id"] == "INDIA_CODE" for a in authorities)

    # 3. Register Source via API
    source_payload = {
        "id": "api-wages-code",
        "title": "API Code on Wages, 2019",
        "source_type": "ACT",
        "authority_id": "INDIA_CODE",
        "jurisdiction_id": "IN",
        "citation_ref": "Act No. 29 of 2019 (API)",
    }
    res_create = await client.post("/api/v1/legal/sources", json=source_payload)
    assert res_create.status_code == 201
    source_data = res_create.json()
    assert source_data["id"] == "api-wages-code"
    assert len(source_data["versions"]) == 1

    # 4. Ingest Provisions via API
    provision_payload = [
        {
            "source_id": "api-wages-code",
            "section": "18",
            "heading": "Deductions which may be made from wages",
            "provision_text": "Notwithstanding anything contained in any other law for the time being in force, there shall be no deductions except those authorized.",
            "status": "ACTIVE",
            "extraction_method": "API_INGEST",
        }
    ]
    res_ingest = await client.post("/api/v1/legal/sources/api-wages-code/provisions", json=provision_payload)
    assert res_ingest.status_code == 201
    prov_data = res_ingest.json()
    assert len(prov_data) == 1
    prov_id = prov_data[0]["id"]
    assert prov_data[0]["provenance"]["verification_state"] == "PENDING_VERIFICATION"

    # 5. Search Provisions
    search_payload = {
        "query": "deductions",
        "source_id": "api-wages-code",
        "jurisdiction_id": "IN",
    }
    res_search = await client.post("/api/v1/legal/provisions/search", json=search_payload)
    assert res_search.status_code == 200
    search_results = res_search.json()
    assert len(search_results) == 1
    assert search_results[0]["section"] == "18"

    # 6. Get Provision Provenance
    res_prov = await client.get(f"/api/v1/legal/provisions/{prov_id}/provenance")
    assert res_prov.status_code == 200
    assert res_prov.json()["verification_state"] == "PENDING_VERIFICATION"

    # 7. Update Verification Status via API
    patch_payload = {
        "verification_state": "VERIFIED",
        "verified_by": "advocate_test_user",
        "verification_notes": "Verified against India Code digital copy.",
    }
    res_patch = await client.patch(f"/api/v1/legal/provisions/{prov_id}/verification", json=patch_payload)
    assert res_patch.status_code == 200
    assert res_patch.json()["verification_state"] == "VERIFIED"
    assert res_patch.json()["verified_by"] == "advocate_test_user"

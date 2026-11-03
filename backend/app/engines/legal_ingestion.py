"""Legal Knowledge Ingestion Engine.

Handles:
1. Source registration and content hashing.
2. Version preservation without overwriting historical text.
3. Structured provision extraction and normalization.
4. Strict provenance tracking and audit states (never auto-verified).
5. Initial seed corpus preparation for Indian Labour Codes (Code on Wages, Industrial Relations, Social Security, OSHWC).
"""
import hashlib
import json
import logging
import uuid
from typing import Any, Dict, List, Optional

from app.db.database import get_db_context
from app.db.repository import Repository
from app.llm.legal_schemas import (
    LegalIngestionStatus,
    LegalProvisionCreate,
    LegalSourceCreate,
    LegalSourceVersionCreate,
    LegalVerificationStatus,
    ProvisionStatus,
)

logger = logging.getLogger(__name__)


def compute_content_hash(text: str) -> str:
    """Compute SHA-256 content hash of string text."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


class LegalIngestionEngine:
    """Manages ingestion of official Indian legal instruments and provision decomposition."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def register_source(self, source_in: LegalSourceCreate) -> Dict[str, Any]:
        """Register a new authoritative legal source instrument with duplicate detection."""
        with get_db_context(self.db_path) as conn:
            repo = Repository(conn)
            # 1. Check duplicate by ID
            existing = repo.get_legal_source(source_in.id)
            if existing:
                raise ValueError(f"Legal source with id '{source_in.id}' already exists.")

            # 2. Check duplicate citation in same jurisdiction
            if source_in.citation_ref:
                existing_cit = repo.find_legal_source_by_citation(source_in.citation_ref, source_in.jurisdiction_id)
                if existing_cit:
                    raise ValueError(
                        f"Legal source with citation '{source_in.citation_ref}' already registered for jurisdiction '{source_in.jurisdiction_id}'."
                    )

            # Compute hash if raw_text provided
            content_hash = source_in.content_hash
            if not content_hash and source_in.raw_text:
                content_hash = compute_content_hash(source_in.raw_text)

            meta_str = json.dumps(source_in.metadata_json) if source_in.metadata_json else None

            created = repo.create_legal_source(
                source_id=source_in.id,
                title=source_in.title,
                short_title=source_in.short_title,
                source_type=source_in.source_type.value,
                authority_id=source_in.authority_id,
                jurisdiction_id=source_in.jurisdiction_id,
                official_url=source_in.official_url,
                citation_ref=source_in.citation_ref,
                publication_date=source_in.publication_date,
                enactment_date=source_in.enactment_date,
                effective_from=source_in.effective_from,
                effective_to=source_in.effective_to,
                content_hash=content_hash,
                source_language=source_in.source_language,
                ingestion_status=LegalIngestionStatus.DISCOVERED.value,
                verification_status=LegalVerificationStatus.PENDING_VERIFICATION.value,
                raw_text=source_in.raw_text,
                metadata_json=meta_str,
            )

            # Automatically create original version entry
            v_id = f"{source_in.id}-v1"
            repo.create_source_version(
                version_id=v_id,
                source_id=source_in.id,
                version_label="Original Enacted Version",
                version_type="ORIGINAL",
                effective_from=source_in.effective_from,
                effective_to=source_in.effective_to,
                gazette_ref=source_in.citation_ref,
                content_hash=content_hash,
                is_current=True,
                notes="Initial registration of authoritative legal instrument.",
            )

            return created

    def create_version(self, source_id: str, version_in: LegalSourceVersionCreate) -> Dict[str, Any]:
        """Register a new historical or amended version of an existing legal source."""
        with get_db_context(self.db_path) as conn:
            repo = Repository(conn)
            source = repo.get_legal_source(source_id)
            if not source:
                raise ValueError(f"Legal source '{source_id}' does not exist.")

            version_id = f"{source_id}-{uuid.uuid4().hex[:8]}"
            return repo.create_source_version(
                version_id=version_id,
                source_id=source_id,
                version_label=version_in.version_label,
                version_type=version_in.version_type.value,
                effective_from=version_in.effective_from,
                effective_to=version_in.effective_to,
                amendment_act_id=version_in.amendment_act_id,
                gazette_ref=version_in.gazette_ref,
                content_hash=version_in.content_hash,
                is_current=version_in.is_current,
                notes=version_in.notes,
            )

    def ingest_provisions(self, source_id: str, provisions: List[LegalProvisionCreate]) -> List[Dict[str, Any]]:
        """
        Ingest a list of structured legal provisions under a source.
        Strict verification safety: Ingested provisions are always stamped PENDING_VERIFICATION.
        """
        results = []
        with get_db_context(self.db_path) as conn:
            repo = Repository(conn)
            source = repo.get_legal_source(source_id)
            if not source:
                raise ValueError(f"Legal source '{source_id}' does not exist.")

            # Update source ingestion status to PARSED
            repo.update_legal_source_status(source_id, ingestion_status=LegalIngestionStatus.PARSED.value)

            for p in provisions:
                p_id = f"{source_id}-sec-{p.section or p.rule_number or uuid.uuid4().hex[:6]}"
                if p.subsection:
                    p_id += f"-{p.subsection}"
                if p.clause_letter:
                    p_id += f"-{p.clause_letter}"

                # Ensure unique id
                idx = 1
                base_pid = p_id
                while repo.get_legal_provision(p_id) is not None:
                    p_id = f"{base_pid}-{idx}"
                    idx += 1

                # Provision-level commencement: NOT_YET_ENFORCED provisions should not inherit Act effective_from
                prov_effective_from = p.effective_from
                if prov_effective_from is None and p.status != ProvisionStatus.NOT_YET_ENFORCED:
                    prov_effective_from = source.get("effective_from")

                prov_effective_to = p.effective_to or source.get("effective_to")

                created_prov = repo.create_legal_provision(
                    provision_id=p_id,
                    source_id=source_id,
                    version_id=p.version_id,
                    jurisdiction_id=p.jurisdiction_id or source["jurisdiction_id"],
                    parent_provision_id=p.parent_provision_id,
                    part=p.part,
                    chapter=p.chapter,
                    section=p.section,
                    subsection=p.subsection,
                    clause_letter=p.clause_letter,
                    subclause=p.subclause,
                    rule_number=p.rule_number,
                    schedule_number=p.schedule_number,
                    paragraph=p.paragraph,
                    heading=p.heading,
                    provision_text=p.provision_text,
                    citation_key=p.citation_key or f"{source['title']} § {p.section or p.rule_number or ''}".strip(),
                    effective_from=prov_effective_from,
                    effective_to=prov_effective_to,
                    status=p.status.value,
                )

                # Attach provenance
                prov_id = f"prov-{p_id}"
                repo.create_provision_provenance(
                    provenance_id=prov_id,
                    provision_id=p_id,
                    source_id=source_id,
                    official_uri=p.official_uri or source.get("official_url") or "https://www.indiacode.nic.in",
                    source_title=p.source_title or source["title"],
                    issuing_authority=p.issuing_authority or source.get("authority_id") or "INDIA_CODE",
                    document_identifier=p.document_identifier or source.get("citation_ref"),
                    publication_date=source.get("publication_date"),
                    effective_date=prov_effective_from,
                    version_label="Original Publication",
                    content_hash=compute_content_hash(p.provision_text),
                    extraction_method=p.extraction_method,
                    source_location_page=p.source_location_page,
                    verification_state=LegalVerificationStatus.PENDING_VERIFICATION.value,
                )

                # Store applicability conditions if present
                for cond in p.applicability_conditions:
                    c_id = f"cond-{uuid.uuid4().hex[:8]}"
                    repo.create_applicability_condition(
                        condition_id=c_id,
                        provision_id=p_id,
                        condition_type=cond.condition_type.value,
                        condition_value=cond.condition_value,
                        operator=cond.operator,
                        condition_description=cond.condition_description,
                    )

                results.append(created_prov)

        return results


def seed_initial_indian_legal_corpus(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Seed structured definitions for the 4 central Indian Labour Codes:
    1. Code on Wages, 2019 (Act No. 29 of 2019)
    2. Industrial Relations Code, 2020 (Act No. 35 of 2020)
    3. Code on Social Security, 2020 (Act No. 36 of 2020)
    4. Occupational Safety, Health and Working Conditions Code, 2020 (Act No. 37 of 2020)

    Commencement Status (Gazette Ground Truth):
    Pursuant to Central Government notifications dated 21 November 2025 (PIB PRID 2192463):
    - Code on Wages, 2019: Commenced via S.O. 5322(E) dated 21-11-2025 (Sections 1-41, 42(4)-(9), 43-66, 67(1),(2)(a)-(r),(u)-(zc),(3)-(5), 68, 69).
    - Industrial Relations Code, 2020: Commenced via S.O. 5320(E) dated 21-11-2025.
    - Code on Social Security, 2020: Commenced via S.O. 5319(E) dated 21-11-2025.
    - Occupational Safety, Health and Working Conditions Code, 2020: Commenced via S.O. 5321(E) dated 21-11-2025.

    Distinct Statutory Layers:
    - Act Commencement: Appointed date is 2025-11-21 across all four codes.
    - Rules Notification: Subordinate Central and State Rules are notified separately and track distinct progress.
    - Provision-Level Exceptions: Specific sections withheld from enforcement (e.g. Wages Code Section 42(1)-(3)) remain NOT_YET_ENFORCED.
    """
    engine = LegalIngestionEngine(db_path=db_path)
    report = {"sources_created": 0, "provisions_created": 0}

    corpus_sources = [
        LegalSourceCreate(
            id="code-on-wages-2019",
            title="Code on Wages, 2019",
            short_title="Wages Code",
            source_type="ACT",
            authority_id="INDIA_CODE",
            jurisdiction_id="IN",
            official_url="https://www.indiacode.nic.in/handle/123456789/13768",
            citation_ref="Act No. 29 of 2019",
            publication_date="2019-08-08",
            enactment_date="2019-08-08",
            effective_from="2025-11-21",
            source_language="en",
            metadata_json={
                "commencement_notification_ref": "S.O. 5322(E) dated 21-11-2025",
                "commencement_date": "2025-11-21",
                "pib_press_release_ref": "PIB PRID 2192463",
                "gazette_url": "https://egazette.gov.in",
                "rules_notification_status": "CENTRAL_RULES_PENDING",
                "state_rules_status": "DRAFT_PUBLISHED_IN_MAJOR_STATES",
                "commenced_sections_scope": "Sections 1 to 41, 42(4) to 42(9), 43 to 66, 67(1), 67(2)(a)-(r), (u)-(zc), 67(3)-(5), 68, 69",
                "withheld_sections_scope": "Section 42(1) to 42(3) (Central/State Advisory Board constitution withheld)",
                "repealed_acts": [
                    "Payment of Wages Act, 1936",
                    "Minimum Wages Act, 1948",
                    "Payment of Bonus Act, 1965",
                    "Equal Remuneration Act, 1976",
                ],
            },
        ),
        LegalSourceCreate(
            id="industrial-relations-code-2020",
            title="Industrial Relations Code, 2020",
            short_title="IR Code",
            source_type="ACT",
            authority_id="INDIA_CODE",
            jurisdiction_id="IN",
            official_url="https://www.indiacode.nic.in/handle/123456789/15729",
            citation_ref="Act No. 35 of 2020",
            publication_date="2020-09-29",
            enactment_date="2020-09-28",
            effective_from="2025-11-21",
            source_language="en",
            metadata_json={
                "commencement_notification_ref": "S.O. 5320(E) dated 21-11-2025",
                "commencement_date": "2025-11-21",
                "pib_press_release_ref": "PIB PRID 2192463",
                "gazette_url": "https://egazette.gov.in",
                "rules_notification_status": "CENTRAL_RULES_PENDING",
                "state_rules_status": "DRAFT_PUBLISHED_IN_MAJOR_STATES",
                "repealed_acts": [
                    "Trade Unions Act, 1926",
                    "Industrial Employment (Standing Orders) Act, 1946",
                    "Industrial Disputes Act, 1947",
                ],
            },
        ),
        LegalSourceCreate(
            id="code-on-social-security-2020",
            title="Code on Social Security, 2020",
            short_title="Social Security Code",
            source_type="ACT",
            authority_id="INDIA_CODE",
            jurisdiction_id="IN",
            official_url="https://www.indiacode.nic.in/handle/123456789/15730",
            citation_ref="Act No. 36 of 2020",
            publication_date="2020-09-29",
            enactment_date="2020-09-28",
            effective_from="2025-11-21",
            source_language="en",
            metadata_json={
                "commencement_notification_ref": "S.O. 5319(E) dated 21-11-2025",
                "commencement_date": "2025-11-21",
                "pib_press_release_ref": "PIB PRID 2192463",
                "gazette_url": "https://egazette.gov.in",
                "rules_notification_status": "CENTRAL_RULES_PENDING",
                "state_rules_status": "DRAFT_PUBLISHED_IN_MAJOR_STATES",
                "repealed_acts": [
                    "Employees' Provident Funds and Miscellaneous Provisions Act, 1952",
                    "Employees' State Insurance Act, 1948",
                    "Payment of Gratuity Act, 1972",
                    "Maternity Benefit Act, 1961",
                ],
            },
        ),
        LegalSourceCreate(
            id="oshwc-code-2020",
            title="Occupational Safety, Health and Working Conditions Code, 2020",
            short_title="OSHWC Code",
            source_type="ACT",
            authority_id="INDIA_CODE",
            jurisdiction_id="IN",
            official_url="https://www.indiacode.nic.in/handle/123456789/15731",
            citation_ref="Act No. 37 of 2020",
            publication_date="2020-09-29",
            enactment_date="2020-09-28",
            effective_from="2025-11-21",
            source_language="en",
            metadata_json={
                "commencement_notification_ref": "S.O. 5321(E) dated 21-11-2025",
                "commencement_date": "2025-11-21",
                "pib_press_release_ref": "PIB PRID 2192463",
                "gazette_url": "https://egazette.gov.in",
                "rules_notification_status": "CENTRAL_RULES_PENDING",
                "state_rules_status": "DRAFT_PUBLISHED_IN_MAJOR_STATES",
                "repealed_acts": [
                    "Factories Act, 1948",
                    "Contract Labour (Regulation and Abolition) Act, 1970",
                    "Mines Act, 1952",
                ],
            },
        ),
    ]

    for src in corpus_sources:
        try:
            engine.register_source(src)
            report["sources_created"] += 1
        except ValueError:
            pass  # Source already registered

    # Key provisions for Code on Wages 2019
    # Illustrates provision-level commencement:
    # - Commenced sections (Sec 6, 9, 17) marked ACTIVE effective 2025-11-21
    # - Withheld sections (Sec 42(1)-(3)) marked NOT_YET_ENFORCED as an explicit exception
    wages_provisions = [
        LegalProvisionCreate(
            source_id="code-on-wages-2019",
            chapter="Chapter II - Minimum Wages",
            section="6",
            subsection="1",
            heading="Fixation of minimum rate of wages",
            provision_text=(
                "Subject to the provisions of this Code, the appropriate Government shall fix the minimum rates of wages "
                "payable to employees in accordance with the provisions of section 8."
            ),
            citation_key="Code on Wages, 2019 § 6(1)",
            effective_from="2025-11-21",
            status=ProvisionStatus.ACTIVE,
            extraction_method="OFFICIAL_STATUTE_TEXT",
            official_uri="https://egazette.gov.in",
            document_identifier="S.O. 5322(E)",
            source_location_page="S.O. 5322(E), Gazette of India, Extraordinary, Part II-Sec 3(ii)",
            applicability_conditions=[
                {
                    "condition_type": "ESTABLISHMENT_TYPE",
                    "operator": "IN",
                    "condition_value": "ALL_SCHEDULED_EMPLOYMENTS",
                    "condition_description": "Applies to all establishments employing one or more persons.",
                }
            ],
        ),
        LegalProvisionCreate(
            source_id="code-on-wages-2019",
            chapter="Chapter II - Minimum Wages",
            section="9",
            subsection="1",
            heading="Power of Central Government to fix floor wage",
            provision_text=(
                "The Central Government shall fix floor wage taking into account minimum living standards of a worker "
                "in such manner as may be prescribed: Provided that different floor wage may be fixed for different geographical areas."
            ),
            citation_key="Code on Wages, 2019 § 9(1)",
            effective_from="2025-11-21",
            status=ProvisionStatus.ACTIVE,
            extraction_method="OFFICIAL_STATUTE_TEXT",
            official_uri="https://egazette.gov.in",
            document_identifier="S.O. 5322(E)",
            source_location_page="S.O. 5322(E), Gazette of India, Extraordinary, Part II-Sec 3(ii)",
            applicability_conditions=[
                {
                    "condition_type": "JURISDICTION",
                    "operator": "EQUALS",
                    "condition_value": "IN",
                    "condition_description": "Central Government jurisdiction across India with geographical differentials.",
                }
            ],
        ),
        LegalProvisionCreate(
            source_id="code-on-wages-2019",
            chapter="Chapter III - Payment of Wages",
            section="17",
            subsection="1",
            heading="Time limit for payment of wages",
            provision_text=(
                "The employer shall pay or cause to be paid wages to the employees, engaged on daily basis, at the end of the shift; "
                "on weekly basis, on the last working day of the week; on fortnightly basis, before the end of the second day after the end of the fortnight; "
                "and on monthly basis, before the expiry of the seventh day of the succeeding month."
            ),
            citation_key="Code on Wages, 2019 § 17(1)",
            effective_from="2025-11-21",
            status=ProvisionStatus.ACTIVE,
            extraction_method="OFFICIAL_STATUTE_TEXT",
            official_uri="https://egazette.gov.in",
            document_identifier="S.O. 5322(E)",
            source_location_page="S.O. 5322(E), Gazette of India, Extraordinary, Part II-Sec 3(ii)",
        ),
        # Provision-level exception: Section 42(1)-(3) withheld from enforcement by S.O. 5322(E)
        LegalProvisionCreate(
            source_id="code-on-wages-2019",
            chapter="Chapter V - Advisory Board",
            section="42",
            subsection="1",
            heading="Central Advisory Board constitution (Excluded from S.O. 5322(E) commencement)",
            provision_text=(
                "The Central Government shall constitute the Central Advisory Board which shall consist of persons to be nominated "
                "by the Central Government representing employers and employees in equal number, and independent persons not exceeding "
                "one-third of the total members."
            ),
            citation_key="Code on Wages, 2019 § 42(1)",
            effective_from=None,
            status=ProvisionStatus.NOT_YET_ENFORCED,
            extraction_method="OFFICIAL_STATUTE_TEXT",
            official_uri="https://egazette.gov.in",
            document_identifier="S.O. 5322(E) (Withheld)",
            source_location_page="Section 42(1)-(3) excluded from commencement under S.O. 5322(E)",
        ),
    ]

    try:
        created_p = engine.ingest_provisions("code-on-wages-2019", wages_provisions)
        report["provisions_created"] += len(created_p)
    except Exception as e:
        logger.warning("Corpus provisions already present or error: %s", e)

    return report

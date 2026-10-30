"""Deontic logic and LLM reasoning schemas."""
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DeonticModality(str, Enum):
    """Modal operator governing a contractual or policy rule."""
    MUST = "MUST"
    MAY = "MAY"
    MUST_NOT = "MUST_NOT"
    CONDITIONAL = "CONDITIONAL"


class ActionCategory(str, Enum):
    """Substantive legal or policy category of the governed action."""
    TERMINATION = "TERMINATION"
    IP_OWNERSHIP = "IP_OWNERSHIP"
    COMPENSATION_FEES = "COMPENSATION_FEES"
    CONFIDENTIALITY = "CONFIDENTIALITY"
    ATTENDANCE_LEAVE = "ATTENDANCE_LEAVE"
    GRADING_CREDITS = "GRADING_CREDITS"
    REGISTRATION_ELIGIBILITY = "REGISTRATION_ELIGIBILITY"
    LIABILITY_INDEMNITY = "LIABILITY_INDEMNITY"
    GENERAL_GOVERNANCE = "GENERAL_GOVERNANCE"


class ExtractedDeonticRule(BaseModel):
    """Structured extraction of a single deontic rule from a clause."""
    subject: str = Field(description="Actor or entity bound by the rule")
    modality: DeonticModality = Field(description="Deontic modal operator")
    action_category: ActionCategory = Field(description="Domain category")
    action_summary: str = Field(description="Concise description of the governed action")
    conditions: List[str] = Field(default_factory=list, description="Preconditions or trigger events")
    exceptions: List[str] = Field(default_factory=list, description="Explicit safe harbors or carve-outs")
    is_override: bool = Field(default=False, description="True if marked with 'notwithstanding' or similar supremacy clause")
    temporal_scope: Optional[str] = Field(default=None, description="Timeframes, cure periods, or deadlines")
    numeric_constraint: Optional[str] = Field(default=None, description="Quantitative limits, percentages, or financial amounts")
    exact_quote: str = Field(description="Exact verbatim substring from the clause")


class ExtractedRuleList(BaseModel):
    """Collection of extracted deontic rules."""
    rules: List[ExtractedDeonticRule] = Field(default_factory=list)


class ConflictType(str, Enum):
    """Taxonomy of contractual and deontic conflicts."""
    DIRECT_MODALITY_CLASH = "DIRECT_MODALITY_CLASH"
    TEMPORAL_NUMERIC_MISMATCH = "TEMPORAL_NUMERIC_MISMATCH"
    UNRESOLVED_OVERRIDE_COLLISION = "UNRESOLVED_OVERRIDE_COLLISION"
    LOOPHOLE_EXCEPTION_GAP = "LOOPHOLE_EXCEPTION_GAP"
    NO_CONFLICT = "NO_CONFLICT"


class PairwiseConflictAudit(BaseModel):
    """Audit result of evaluating two rules for cross-clause collision."""
    has_conflict: bool
    conflict_type: ConflictType
    severity: str = Field(description="HIGH, MEDIUM, or LOW")
    collision_axis: str = Field(description="Substantive dimension of conflict (e.g., notice_period, ownership_scope)")
    reasoning: str
    winning_rule_id: Optional[str] = Field(default=None, description="ID of prevailing rule if hierarchy or override resolves it")


class VerdictState(str, Enum):
    """Primary system verification states."""
    ANSWERABLE = "ANSWERABLE"
    CONTRADICTION = "CONTRADICTION"
    EXPLOITABLE_LOOPHOLE = "EXPLOITABLE_LOOPHOLE"
    NOT_COVERED = "NOT_COVERED"


class CitationSpan(BaseModel):
    """Verbatim citation with exact character indices."""
    clause_id: str
    doc_id: str
    doc_title: str
    section_number: str
    verbatim_quote: str
    char_start: int
    char_end: int


class AgentBrief(BaseModel):
    """Argumentation brief submitted by an adversarial agent."""
    agent_role: str
    thesis: str
    arguments: List[str] = Field(default_factory=list)
    cited_clause_ids: List[str] = Field(default_factory=list)
    flagged_gaps_or_undefined_terms: List[str] = Field(default_factory=list)


class CourtroomVerdict(BaseModel):
    """Final adjudicated verdict from the courtroom pipeline."""
    verdict_state: VerdictState
    benchmark_compat_state: str = Field(
        description="Compatibility mapping to 3-state benchmark (ANSWERABLE, CONTRADICTION, NOT_COVERED)"
    )
    confidence_score: float = Field(ge=0.0, le=1.0)
    executive_ruling: str
    advocate_brief: AgentBrief
    skeptic_brief: AgentBrief
    missing_prerequisites: List[str] = Field(default_factory=list)
    verified_citations: List[CitationSpan] = Field(default_factory=list)


class CounterfactualPatchResult(BaseModel):
    """Generated counterfactual amendment resolving a detected conflict."""
    conflict_id: str
    target_clause_id: str
    exploit_actor: str
    exploit_scenario: str
    financial_or_legal_impact: str
    original_text: str
    patched_text: str
    rationale: str
    verification_passed: bool
    initial_conflicts: int
    remaining_conflicts: int
    patch_id: Optional[str] = None

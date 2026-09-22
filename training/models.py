from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Origin(str, Enum):
    HUMAN_SEED = "human_seed"
    SYNTHETIC = "synthetic_from_seed"
    PRODUCTION = "production_log_reviewed"
    ADVERSARIAL = "adversarial"
    REGRESSION = "regression"


class ReviewStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class SlotSource(str, Enum):
    USER_EXPLICIT = "user_explicit"
    CONVERSATION_CONTEXT = "conversation_context"
    INFERRED_FROM_POLICY = "inferred_from_policy"
    RESOLVED_FROM_REGISTRY = "resolved_from_registry"
    NOT_PROVIDED = "not_provided"


class Lineage(StrictModel):
    parent_seed_id: str | None = None
    generation_kind: str = "human"
    generation_batch_id: str
    generator: str
    prompt_version: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class RegistrySnapshot(StrictModel):
    agent_registry: str
    capability_registry: str = "0.1"
    tool_registry: str
    data_registry: str
    spatial_layer_registry: str
    query_template_registry: str
    derived_concept_registry: str
    ontology_registry: str
    snapshot_hash: str


class ConversationTurn(StrictModel):
    role: Literal["user", "assistant"]
    content: str


class InputContext(StrictModel):
    user_query: str = Field(min_length=1)
    conversation_context: list[ConversationTurn] = Field(default_factory=list)
    available_context: dict[str, Any] = Field(default_factory=dict)

    @field_validator("user_query")
    @classmethod
    def reject_broken_text(cls, value: str) -> str:
        if "\ufffd" in value:
            raise ValueError("replacement character indicates broken encoding")
        return value.strip()


class CanonicalTerm(StrictModel):
    surface_term: str
    canonical_term: str


class ExpectedSemantics(StrictModel):
    normalized_query: str
    intent: str
    canonical_terms: list[CanonicalTerm] = Field(default_factory=list)
    derived_concepts: list[str] = Field(default_factory=list)
    target_feature_classes: list[str] = Field(default_factory=list)
    spatial_relation: str | None = None
    temporal_relation: str | None = None
    execution_requested: bool = False
    dynamic_data_required: bool = False


class SlotValue(StrictModel):
    value: Any = None
    source: SlotSource
    required: bool = False


class ExpectedRouting(StrictModel):
    fast_path: str
    required_capabilities: list[str] = Field(default_factory=list)
    resolver_chain: list[str] = Field(default_factory=list)
    primary_agent: str
    secondary_agents: list[str] = Field(default_factory=list)
    tools: list[str] = Field(default_factory=list)
    query_template: str | None = None


class ExpectedDataBindings(StrictModel):
    datasets: list[str] = Field(default_factory=list)
    layers: list[str] = Field(default_factory=list)
    required_versions: dict[str, str] = Field(default_factory=dict)


class ExpectedExecution(StrictModel):
    execution_ready: bool
    orchestration_status: list[Literal["COMPLETED", "BLOCKED", "NEEDS_CLARIFICATION", "FAILED"]]
    execution_outcomes: list[Literal["SUCCESS_WITH_RESULTS", "SUCCESS_EMPTY", "PARTIAL", "TOOL_ERROR", "NOT_EXECUTED"]]
    blockers: list[str] = Field(default_factory=list)
    forbidden_behaviors: list[str] = Field(default_factory=list)


class ExpectedKnowledge(StrictModel):
    ontology_classes: list[str] = Field(default_factory=list)
    allowed_relation_types: list[str] = Field(default_factory=list)
    forbidden_relation_types: list[str] = Field(default_factory=list)
    kg_paths_required: bool = False


class ExpectedEvidence(StrictModel):
    required_bundle_fields: list[Literal[
        "spatial_feature_evidence", "spatial_layer_evidence",
        "accident_relation_evidence", "regulatory_evidence",
        "rag_evidence", "kg_provenance",
    ]] = Field(default_factory=list)
    execution_trace_required: bool = False
    citation_required: bool = False


class ExecutionFixture(StrictModel):
    fixture_id: str | None = None
    frozen_at: datetime | None = None
    route_plan: dict[str, Any] = Field(default_factory=dict)
    execution_result: dict[str, Any] = Field(default_factory=dict)
    evidence_bundle: dict[str, list[dict[str, Any]]] = Field(default_factory=dict)


class ExpectedAnswer(StrictModel):
    mode: Literal["reference", "behavioral", "clarification"]
    reference_answer: str | None = None
    required_points: list[str] = Field(default_factory=list)
    forbidden_claims: list[str] = Field(default_factory=list)


class Ambiguity(StrictModel):
    is_ambiguous: bool = False
    candidate_interpretations: list[str] = Field(default_factory=list)
    clarification_question: str | None = None


class NegativeConstraints(StrictModel):
    forbidden_agents: list[str] = Field(default_factory=list)
    forbidden_capabilities: list[str] = Field(default_factory=list)
    forbidden_tools: list[str] = Field(default_factory=list)


class Quality(StrictModel):
    human_verified: bool = False
    reviewer: str | None = None
    review_notes: list[str] = Field(default_factory=list)
    validation_checks: list[str] = Field(default_factory=list)


class TrainingCase(StrictModel):
    schema_version: Literal["1.0.0"] = "1.0.0"
    case_id: str = Field(pattern=r"^MGEO-[A-Z0-9_-]+$")
    origin: Origin
    split: Literal["seed", "train", "validation", "test", "benchmark"]
    review_status: ReviewStatus
    language: Literal["ko", "en", "mixed"]
    domain_labels: list[str] = Field(min_length=1)
    lineage: Lineage
    registry_snapshot: RegistrySnapshot
    input: InputContext
    expected_semantics: ExpectedSemantics
    expected_slots: dict[str, SlotValue] = Field(default_factory=dict)
    expected_routing: ExpectedRouting
    expected_data_bindings: ExpectedDataBindings
    expected_execution: ExpectedExecution
    expected_knowledge: ExpectedKnowledge = Field(default_factory=ExpectedKnowledge)
    expected_evidence: ExpectedEvidence = Field(default_factory=ExpectedEvidence)
    execution_fixture: ExecutionFixture = Field(default_factory=ExecutionFixture)
    expected_answer: ExpectedAnswer
    ambiguity: Ambiguity = Field(default_factory=Ambiguity)
    negative_constraints: NegativeConstraints = Field(default_factory=NegativeConstraints)
    quality: Quality = Field(default_factory=Quality)

    @model_validator(mode="after")
    def enforce_contract(self) -> "TrainingCase":
        missing = [name for name, slot in self.expected_slots.items() if slot.required and slot.value is None]
        if missing and self.expected_execution.execution_ready:
            raise ValueError(f"required slots are missing while execution_ready=true: {missing}")
        if self.origin == Origin.SYNTHETIC and not self.lineage.parent_seed_id:
            raise ValueError("synthetic cases require lineage.parent_seed_id")
        if self.expected_semantics.dynamic_data_required:
            fixture = self.execution_fixture
            if self.expected_answer.reference_answer and not fixture.fixture_id:
                raise ValueError("dynamic reference answers require a frozen execution fixture")
        if self.expected_execution.execution_ready and not self.expected_routing.tools:
            raise ValueError("execution-ready cases require at least one tool")
        return self

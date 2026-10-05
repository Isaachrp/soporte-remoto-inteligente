from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from shared.contracts import Request as SupportRequest, Result as ActionResult, Strict


class AIModel(Strict):
    model_config = ConfigDict(extra='forbid', strict=True, revalidate_instances='always')


class ProblemClassification(AIModel):
    procedure: Literal['ECMP', 'OUT_OF_SCOPE']


class ActionParameters(AIModel):
    """No model-owned execution arguments. The server binds the validated request."""


class PlannedAction(AIModel):
    action_id: str = Field(min_length=1, max_length=80)
    parameters: ActionParameters
    reason: str = Field(min_length=1, max_length=240)
    risk_level: Literal['READ_ONLY', 'REQUIRES_APPROVAL']
    requires_approval: bool


class SupportPlan(AIModel):
    category: Literal['ECMP', 'OUT_OF_SCOPE']
    explanation: str = Field(min_length=1, max_length=400)
    actions: list[PlannedAction] = Field(max_length=3)
    missing_information: list[Literal['ecmp_parameters']] = Field(max_length=1)
    status: Literal['ready', 'needs_information', 'out_of_scope']


class ActionObservation(AIModel):
    task_id: str
    action_id: Literal['get_ecmp_precheck', 'apply_approved_ecmp', 'verify_ecmp']
    status: Literal['ok', 'failed', 'uncertain']
    completed: int = Field(ge=0)
    error: Literal['tls', 'timeout', 'connection', 'validation', 'router_error'] | None


class ResultAnalysis(AIModel):
    assessment: Literal['configuration_checked', 'verification_failed', 'needs_human_review', 'not_executed']
    problem_resolved: bool
    requires_human_intervention: bool
    next_step: Literal['test_wan_lan', 'review_manually', 'submit_new_request']


class FinalSupportResponse(AIModel):
    request_id: str
    status: str
    summary: str
    analysis: ResultAnalysis
    analysis_source: Literal['ai', 'deterministic', 'deterministic_fallback']
    successful_actions: list[str]
    failed_actions: list[str]
    unverified_checks: list[str]
    error_codes: list[str]


class WorkflowRecord(BaseModel):
    """Typed AI state plus the existing versioned artifact/task fields.

    Extra fields belong to the legacy workflow, never to a model response.
    Keeping them preserves SQLite checkpoints and the agent wire contract.
    """
    model_config = ConfigDict(extra='allow', strict=True)
    id: str
    status: str
    text: str | None = None  # Input only; consumed before the first checkpoint.
    original_request: Literal['ECMP', 'OUT_OF_SCOPE'] | None = None
    classification: ProblemClassification | None = None
    plan: SupportPlan | None = None
    plan_hash: str | None = None
    ai_schema: Literal[1] | None = None
    approved_actions: list[str] = Field(default_factory=list)
    pending_actions: list[str] = Field(default_factory=list)
    action_results: list[ActionObservation] = Field(default_factory=list)
    requires_approval: bool = False
    errors: list[str] = Field(default_factory=list)
    current_node: str | None = None
    current_status: str | None = None
    result_analysis: ResultAnalysis | None = None
    final_response: FinalSupportResponse | None = None


class WorkflowState(BaseModel):
    record: WorkflowRecord

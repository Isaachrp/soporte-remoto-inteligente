"""Deterministic policy, independent of model instructions and provider."""
from shared.contracts import ACTIONS, Parameters, digest
from server.app.ai.models import ProblemClassification, SupportPlan

SEQUENCE = ('get_ecmp_precheck', 'apply_approved_ecmp', 'verify_ecmp')


class PlanRejected(ValueError):
    def __init__(self, code):
        self.code = code
        super().__init__(code)


class PlanValidator:
    def validate(self, proposal, classification, parameters):
        plan = SupportPlan.model_validate(proposal)
        classification = ProblemClassification.model_validate(classification)
        if plan.category != classification.procedure:
            raise PlanRejected('plan_category_mismatch')
        expected_status = ('out_of_scope' if classification.procedure == 'OUT_OF_SCOPE'
                           else 'ready' if parameters is not None else 'needs_information')
        if parameters is not None:
            Parameters.model_validate(parameters)
        if plan.status != expected_status:
            raise PlanRejected('plan_status_mismatch')
        expected_missing = ['ecmp_parameters'] if expected_status == 'needs_information' else []
        if plan.missing_information != expected_missing:
            raise PlanRejected('plan_missing_information_mismatch')
        for action in plan.actions:
            if action.action_id not in ACTIONS:
                raise PlanRejected('unknown_action')
            rule = ACTIONS[action.action_id]
            approval = rule['risk'] == 'write'
            risk = 'REQUIRES_APPROVAL' if approval else 'READ_ONLY'
            if action.risk_level != risk or action.requires_approval != approval:
                raise PlanRejected('action_policy_mismatch')
        expected = list(SEQUENCE) if expected_status == 'ready' else []
        if [a.action_id for a in plan.actions] != expected:
            raise PlanRejected('unsafe_action_sequence')
        return plan

    def authorize_dispatch(self, record, action_id):
        # Pre-upgrade checkpoints retain their existing deterministic controls.
        if record.get('ai_schema') != 1:
            return
        plan = self.validate(record['plan'], record['classification'], record['parameters'])
        if digest(plan.model_dump()) != record.get('plan_hash'):
            raise PlanRejected('plan_integrity_failed')
        if action_id not in [a.action_id for a in plan.actions]:
            raise PlanRejected('action_not_planned')

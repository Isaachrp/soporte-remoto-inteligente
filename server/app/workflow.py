"""Event-driven LangGraph. Each wait returns to polling; SQLite persists the
state and outbox atomically. Resume reloads that state on the next external event.
No background synchronous pretend-agent and no volatile approval state.
"""
import logging
from pydantic import ValidationError
from langgraph.graph import StateGraph, START, END
from shared.contracts import ACTIONS, digest, variant
from shared.ecmp import precheck, validate_artifact, verify
from server.app.ai.models import WorkflowState, ProblemClassification, SupportPlan
from server.app.ai.policy import PlanValidator, PlanRejected
from server.app.ai.results import FINAL_STATUSES, add_error, analyze, final_response
from server.app.services.ai import AIError, AIService, request_projection

logger = logging.getLogger('ecmp.workflow')

def approval_binding(r):
    binding = {key:r[key] for key in ('id','technician','session_id','target','parameters','variant','mode','precheck_hash')}
    binding.update(generation_id=r['artifact']['generation_id'],generator_version=r['artifact']['generator_version'],
                   script_hash=r['artifact']['script_hash'],adapter_version=r['executable']['adapter_version'],
                   operations_hash=r['executable']['operations_hash'])
    if r.get('ai_schema') == 1:
        binding['plan_hash'] = digest(r['plan'])
    return binding

def build_workflow(interpreter: AIService, generator):
    validator = PlanValidator()
    def node(fn):
        def run(state):
            r = state.record.model_dump(exclude_unset=True)
            previous = r['status']
            r['current_node'] = fn.__name__
            proposed = r.get('proposed_plan', {}).get('actions', [])
            try:
                fn(r)
            except (AIError, PlanRejected, ValidationError) as exc:
                code = exc.code if isinstance(exc, (AIError, PlanRejected)) else 'invalid_structured_output'
                add_error(r, code)
                status = 'ai_error' if isinstance(exc, AIError) else 'invalid_plan'
                if r.get('action_results'):
                    status = 'intervention_required'
                r.update(status=status, reason=code)
                # Do not retain an untrusted rejected plan or its free-form content.
                r.pop('proposed_plan', None)
            except Exception:
                add_error(r, 'validation_or_integration_failed')
                r.update(status='intervention_required', reason='validation_or_integration_failed')
            event = {'node': fn.__name__, 'from_status': previous, 'status': r['status'],
                     'classification': r.get('classification', {}).get('procedure'),
                     'actions': [a['action_id'] if a['action_id'] in ACTIONS else 'unknown'
                                 for a in r.get('plan', {}).get('actions', [])],
                     'error': r.get('reason') if r['status'] in ('invalid_plan', 'ai_error', 'intervention_required') else None}
            event['error_codes'] = list(r.get('errors', []))
            proposed = proposed or r.get('proposed_plan', {}).get('actions', [])
            event['proposed_actions'] = [a['action_id'] if a['action_id'] in ACTIONS else 'unknown' for a in proposed]
            event['rejected_actions'] = event['proposed_actions'] if r['status'] == 'invalid_plan' else []
            r.setdefault('workflow_events', []).append(event)
            logger.info('workflow_event request_id=%s node=%s from=%s status=%s classification=%s actions=%s proposed=%s rejected=%s errors=%s',
                        r['id'], event['node'], previous, r['status'], event['classification'], event['actions'],
                        event['proposed_actions'], event['rejected_actions'], event['error_codes'])
            return {'record': r}
        return run

    def classify(r):
        r['original_request'] = request_projection(r.pop('text'))
        r['ai_schema'] = 1
        classification = ProblemClassification.model_validate(interpreter.classify_problem(r['original_request']))
        if classification.procedure != r['original_request']:
            raise PlanRejected('classification_scope_mismatch')
        r['classification'] = classification.model_dump()
        r['status'] = 'classified'

    def generate_plan(r):
        classification = ProblemClassification.model_validate(r['classification'])
        proposal = interpreter.generate_plan(classification, r.get('parameters') is not None)
        r['proposed_plan'] = SupportPlan.model_validate(proposal).model_dump()
        r['status'] = 'plan_proposed'

    def validate_plan(r):
        plan = validator.validate(r['proposed_plan'], r['classification'], r.get('parameters'))
        r.pop('proposed_plan')
        r['plan'] = plan.model_dump()
        r['plan_hash'] = digest(r['plan'])
        r['status'] = {'ready': 'parameters_ready', 'needs_information': 'await_parameters',
                       'out_of_scope': 'out_of_scope'}[plan.status]

    def parameters(r):
        r['status'] = 'await_precheck' if r.get('parameters') else 'await_parameters'

    def compatibility(r):
        r['variant'] = variant(r['precheck']['version'], r['mode'])
        r['precheck_hash'] = precheck(r['precheck'], r['target'], r['parameters'])
        r['status'] = 'compatible'

    def artifact(r):
        r['artifact'] = generator.generate(r['parameters'])
        r['status'] = 'artifact_received'

    def validate(r):
        r['executable'] = validate_artifact(r['artifact'], r['parameters'])
        r['binding'] = approval_binding(r)
        r['binding_hash'] = digest(r['binding'])
        r['status'] = 'await_approval'

    def execution(r):
        result = r['execution_result']
        if result['status'] != 'ok' or result['completed'] != len(r['executable']['operations']):
            r.update(status='intervention_required', reason='execution_partial_or_uncertain', reconciliation_required=True)
        else:
            r['status'] = 'await_verification'

    def verification(r):
        result = r['verification_result']
        if result['status'] != 'ok' or not result.get('snapshot') or result['snapshot']['identity'] != r['target']['identity'] or result['snapshot']['version'] != r['precheck']['version']:
            r.update(status='intervention_required', reason='verification_not_completed')
        else:
            r['verification'] = verify(result['snapshot'], r['executable']['operations'])
            r['status'] = r['verification']['outcome']
        if r.get('reconciliation_observed'):
            r.update(status='intervention_required', reason='reconciliation_observed_manual_review_required')

    def analyze_results(r):
        analyze(r, interpreter)

    def generate_final_response(r):
        final_response(r)

    functions = {'receive_request': classify, 'generate_plan': generate_plan, 'validate_plan': validate_plan,
                 'analyze_results': analyze_results, 'generate_final_response': generate_final_response,
                 'collect_and_validate_parameters': parameters,
                 'validate_compatibility': compatibility, 'request_php_artifact': artifact,
                 'validate_artifact': validate, 'collect_execution_result': execution,
                 'verify_configuration': verification}
    route = {'received':'receive_request', 'classified':'generate_plan', 'plan_proposed':'validate_plan',
             'planning_ready':'generate_plan', 'parameters_ready':'collect_and_validate_parameters',
             'precheck_received':'validate_compatibility','compatible':'request_php_artifact',
             'artifact_received':'validate_artifact','execution_received':'collect_execution_result',
             'verification_received':'verify_configuration'}
    graph = StateGraph(WorkflowState)
    for name, fn in functions.items():
        graph.add_node(name, node(fn))
    def next_node(state):
        r = state.record.model_dump(exclude_unset=True)
        if r['status'] in FINAL_STATUSES:
            if 'result_analysis' not in r:
                return 'analyze_results'
            if 'final_response' not in r:
                return 'generate_final_response'
        return route.get(r['status'], END)
    graph.add_conditional_edges(START, next_node)
    for name in functions:
        graph.add_conditional_edges(name, next_node)
    return graph.compile()

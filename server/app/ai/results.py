"""Bounded interpretation; model output cannot change execution facts or status."""
from server.app.ai.models import ActionObservation, FinalSupportResponse, ResultAnalysis
from server.app.services.ai import AIError, expected_analysis

MESSAGES = {
    'out_of_scope': 'Solicitud fuera del alcance: solo ECMP.',
    'await_parameters': 'Complete los parametros del formulario ECMP.',
    'await_precheck': 'Esperando diagnostico del agente.',
    'await_approval': 'Revise el artefacto, operaciones y advertencias antes de aprobar.',
    'await_execution': 'Esperando ejecucion autorizada del agente.',
    'await_verification': 'Operaciones recibidas; falta verificar configuracion.',
    'configuration_with_warnings': 'Configuracion con advertencias: estructura verificada; trafico WAN y conectividad LAN no realizados.',
    'configuration_failed': 'Configuracion fallida: la verificacion encontro diferencias.',
    'intervention_required': 'Intervencion requerida. No repita escrituras; consulte evidencia y reconcilie.',
    'rejected': 'Operacion rechazada por el tecnico; sin autorizacion de escritura.',
    'invalid_plan': 'Plan de IA rechazado por validacion; no se despacharon acciones nuevas.',
    'ai_error': 'No se pudo obtener un plan de IA valido; revise el codigo de error.',
}
FINAL_STATUSES = {'out_of_scope', 'rejected', 'invalid_plan', 'ai_error',
                  'configuration_with_warnings', 'configuration_failed', 'intervention_required'}


def add_error(record, code):
    errors = record.setdefault('errors', [])
    if code not in errors:
        errors.append(code)


def evidence(record):
    observations = [ActionObservation.model_validate(item) for item in record.get('action_results', [])]
    checks = record.get('verification', {}).get('checks', [])
    # No snapshots, parameters, prose, identifiers, task/session IDs or script.
    return {'status': record['status'],
            'actions': [o.model_dump(exclude={'task_id'}) for o in observations],
            'verification': {status: sum(c['status'] == status for c in checks)
                             for status in ('passed', 'failed', 'not_performed')},
            'wan_traffic_verified': False, 'lan_connectivity_verified': False}


def analyze(record, interpreter=None):
    expected = expected_analysis(record['status'])
    source = 'deterministic'
    if interpreter is not None and record.get('action_results'):
        try:
            proposed = ResultAnalysis.model_validate(interpreter.analyze_results(evidence(record)))
            if proposed != expected:
                raise AIError('analysis_contradicts_evidence')
            expected, source = proposed, 'ai'
        except AIError as exc:
            add_error(record, exc.code)
            source = 'deterministic_fallback'
        except Exception:
            add_error(record, 'analysis_invalid_or_unavailable')
            source = 'deterministic_fallback'
    record['result_analysis'] = expected.model_dump()
    record['analysis_source'] = source


def final_response(record):
    observations = [ActionObservation.model_validate(item) for item in record.get('action_results', [])]
    summary = MESSAGES[record['status']]
    if record.get('reason') == 'openai_api_key_missing':
        summary = 'Falta OPENAI_API_KEY para ECMP_AI_MODE=openai. Configurela en el entorno del servidor.'
    if record.get('reason', '').startswith('openrouter_'):
        from server.app.services.openrouter import ERROR_MESSAGES
        summary = ERROR_MESSAGES.get(record['reason'], summary)
    if record.get('reconciliation_observed'):
        summary = 'Estado consultado. Requiere revision manual; la aprobacion anterior no autoriza mas escrituras.'
    if record.get('analysis_source') == 'deterministic_fallback':
        summary += ' Analisis de IA no disponible o rechazado; se muestra la evaluacion determinista.'
    failed = {o.action_id for o in observations if o.status != 'ok'}
    execution = record.get('execution_result')
    if execution and execution['completed'] != len(record['executable']['operations']):
        failed.add('apply_approved_ecmp')
    if (any(c['status'] == 'failed' for c in record.get('verification', {}).get('checks', []))
            or record.get('reason') == 'verification_not_completed'):
        failed.add('verify_ecmp')
    response = FinalSupportResponse(request_id=record['id'], status=record['status'], summary=summary,
        analysis=ResultAnalysis.model_validate(record['result_analysis']),
        analysis_source=record['analysis_source'],
        successful_actions=list(dict.fromkeys(o.action_id for o in observations if o.status == 'ok' and o.action_id not in failed)),
        failed_actions=sorted(failed),
        unverified_checks=['WAN traffic', 'LAN connectivity'], error_codes=record.get('errors', []))
    record['final_response'] = response.model_dump()
    record['message'] = summary


def sync_state(record):
    record['current_status'] = record['status']
    record['requires_approval'] = record['status'] == 'await_approval'
    record.setdefault('approved_actions', [])
    record.setdefault('action_results', [])
    record.setdefault('errors', [])
    completed = {o['action_id'] for o in record['action_results']}
    record['pending_actions'] = ([] if record['status'] in FINAL_STATUSES else
                                 [a['action_id'] for a in record.get('plan', {}).get('actions', [])
                                  if a['action_id'] not in completed])

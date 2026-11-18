"""Central delivery contract. No credentials and no arbitrary commands."""
import json
import time
from uuid import UUID

from shared.contracts import Parameters, Target, digest, variant
from shared.ecmp import precheck, validate_artifact
from shared.snapshot import Snapshot
from server.app.ai.policy import PlanValidator
from server.app.existing_ecmp import check_existing, remaining_executable

SCHEMA = 'ecmp-offline/1'
LIFETIME = 24 * 60 * 60


def canonical_snapshot(value):
    snapshot = Snapshot.model_validate(value).model_dump()
    for rows in snapshot['tables'].values():
        rows.sort(key=lambda row: json.dumps(row, sort_keys=True))
    return snapshot


def extract_snapshot(document):
    if not isinstance(document, dict):
        raise ValueError('El diagnóstico debe ser un objeto JSON.')
    if document.get('schema') == 'ecmp-lab-readonly/1':
        raise ValueError('Ese informe solo contiene un resumen. Cargue el análisis completo con snapshot y tablas de configuración.')
    value = document
    for key in ('snapshot', 'precheck'):
        if isinstance(document.get(key), dict):
            value = document[key]
            break
    else:
        if isinstance(document.get('inspection'), dict):
            value = document['inspection'].get('snapshot')
    return canonical_snapshot(value)


def validate_package(package, now=None):
    now = time.time() if now is None else now
    expected = {'schema', 'id', 'created', 'approved_at', 'expires_at', 'mode', 'ai_mode',
                'target', 'parameters', 'snapshot', 'snapshot_hash', 'variant', 'artifact',
                'executable', 'classification', 'plan', 'plan_hash', 'package_hash'}
    continuing = isinstance(package, dict) and package.get('schema') == 'ecmp-offline/2'
    if continuing:
        expected.add('execution_policy')
    if (not isinstance(package, dict) or set(package) != expected
            or package['schema'] not in (SCHEMA, 'ecmp-offline/2')
            or (continuing and package['execution_policy'] != 'preserve_existing')):
        raise ValueError('Formato de paquete no admitido.')
    UUID(package['id'])
    body = {k: v for k, v in package.items() if k != 'package_hash'}
    if digest(body) != package['package_hash']:
        raise ValueError('El paquete fue alterado.')
    for key in ('created', 'approved_at', 'expires_at'):
        if type(package[key]) not in (float, int):
            raise ValueError('Fecha inválida.')
    if not (package['created'] <= package['approved_at'] <= now < package['expires_at']
            and package['expires_at'] - package['approved_at'] == LIFETIME):
        raise ValueError('Paquete vencido o fecha inválida. Prepare y autorice una nueva entrega.')
    if package['mode'] not in ('real', 'simulated') or package['ai_mode'] not in ('openai', 'openrouter', 'simulated'):
        raise ValueError('Modo inválido.')
    target = Target.model_validate(package['target']).model_dump()
    parameters = Parameters.model_validate(package['parameters']).model_dump()
    snapshot = canonical_snapshot(package['snapshot'])
    selected = variant(snapshot['version'], package['mode'], package['mode'] == 'real')
    if selected != package['variant']:
        raise ValueError('Variante inválida.')
    snapshot_hash = (check_existing(snapshot, target, parameters, package['mode'], package['mode'] == 'real')
                     if continuing else precheck(snapshot, target, parameters, package['mode'] == 'real'))
    if snapshot_hash != package['snapshot_hash']:
        raise ValueError('Diagnóstico distinto del aprobado.')
    plan = PlanValidator().validate(package['plan'], package['classification'], parameters)
    if plan.status != 'ready' or digest(plan.model_dump()) != package['plan_hash']:
        raise ValueError('Plan inválido.')
    if (package['artifact'].get('routeros_family') == 'v7') != snapshot['version'].startswith('7.'):
        raise ValueError('Familia del script incorrecta.')
    executable = validate_artifact(package['artifact'], parameters)
    if continuing:
        executable = remaining_executable(executable, snapshot, target, parameters, package['mode'], package['mode'] == 'real')
    if executable != package['executable']:
        raise ValueError('Operaciones distintas de las autorizadas.')
    return package

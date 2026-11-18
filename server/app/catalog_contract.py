"""Independent package for an explicitly approved, unchanged PHP script."""
import hashlib
import time
from uuid import UUID

from shared.contracts import digest
from server.app.offline_contract import canonical_snapshot
from server.app.generator_catalog import LABELS, validate_parameters, catalog

SCHEMA = 'php-generator-offline/1'


def validate(package, now=None):
    expected = {'schema', 'id', 'procedure', 'parameters', 'snapshot', 'snapshot_hash', 'artifact',
                'created', 'approved_at', 'expires_at', 'mode', 'ai_mode', 'package_hash'}
    if not isinstance(package, dict) or set(package) != expected or package['schema'] != SCHEMA:
        raise ValueError('Paquete inválido.')
    UUID(package['id'])
    if digest({k: v for k, v in package.items() if k != 'package_hash'}) != package['package_hash']:
        raise ValueError('El paquete fue alterado.')
    now = time.time() if now is None else now
    if any(type(package[k]) not in (int, float) for k in ('created', 'approved_at', 'expires_at')):
        raise ValueError('Fechas inválidas.')
    if not (package['created'] <= package['approved_at'] <= now < package['expires_at']
            and package['expires_at'] - package['approved_at'] == 86400):
        raise ValueError('Entrega vencida. Genera una nueva.')
    if package['mode'] not in ('real', 'simulated') or package['ai_mode'] not in ('openai', 'openrouter', 'simulated'):
        raise ValueError('Modo inválido.')
    snapshot = canonical_snapshot(package['snapshot'])
    if digest(snapshot) != package['snapshot_hash']:
        raise ValueError('Diagnóstico alterado.')
    validate_parameters(package['procedure'], package['parameters'])
    option = next(o for o in catalog(snapshot) if o['id'] == package['procedure'])
    if option['note']:
        raise ValueError(option['note'])
    artifact = package['artifact']
    if set(artifact) != {'script', 'script_hash', 'attachment'}:
        raise ValueError('Artefacto inválido.')
    script = artifact['script']
    if not isinstance(script, str) or not 1 <= len(script) <= 500000 or '\x00' in script:
        raise ValueError('Script inválido.')
    if hashlib.sha256(script.encode()).hexdigest() != artifact['script_hash']:
        raise ValueError('Script alterado.')
    if not isinstance(artifact['attachment'], str) or len(artifact['attachment']) > 100000:
        raise ValueError('Adjunto inválido.')
    return package

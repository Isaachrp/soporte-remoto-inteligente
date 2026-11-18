"""Prepare and approve offline deliveries using the existing graph and PHP generator."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import threading
import uuid

from fastapi import HTTPException
from shared.contracts import digest
from server.app.offline_contract import SCHEMA, LIFETIME, extract_snapshot, validate_package
from server.app.services.discovery import recommend
from server.app.services.configuration_notice import configuration_notice
from server.app.existing_ecmp import reconcile

ROOT = Path(__file__).resolve().parents[3]
BUILD_LOCK = threading.Lock()


def runner_source_hash():
    paths = [ROOT / name for name in (
        'server/app/offline_runner.py', 'server/app/offline_contract.py',
        'server/app/existing_ecmp.py',
        'server/app/catalog_runner.py', 'server/app/catalog_contract.py', 'server/app/generator_catalog.py',
        'server/app/ai/models.py', 'server/app/ai/policy.py', 'agent/app/router.py',
        'agent/build.lock')]
    paths.extend(sorted((ROOT / 'shared').glob('*.py')))
    return digest({str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})


class CentralDelivery:
    def __init__(self, operations):
        self.ops = operations

    def annotate(self, snapshot, proposal, mode):
        notice = configuration_notice(snapshot, proposal['parameters']) if not proposal['available'] else None
        proposal['configuration_notice'] = notice
        proposal['can_continue_existing'] = False
        if notice:
            try:
                missing = reconcile(snapshot, proposal['target'], proposal['parameters'], mode, self.ops.settings.v7_lab_enabled)
                proposal['can_continue_existing'] = True
                notice['message'] = ('Puedes continuar conservando lo que coincide y agregando solo lo faltante. '
                                     f'Operaciones por agregar: {len(missing)}. Si no falta nada, solo se verificará. '
                                     'El diagnóstico no confirma conectividad WAN/LAN.')
                notice['actions'][1] = 'Pulsa Continuar de todas formas para revisar y autorizar una entrega que conserva la configuración coincidente.'
            except ValueError as exc:
                notice['message'] += ' ' + str(exc)
        return proposal

    def inspect(self, document):
        try:
            snapshot = extract_snapshot(document)
            proposal = recommend(snapshot, 'router-1', self.ops.settings.mode, self.ops.settings.v7_lab_enabled)
            self.annotate(snapshot, proposal, self.ops.settings.mode)
        except ValueError as exc:
            if document.get('schema') == 'ecmp-lab-readonly/1':
                raise HTTPException(422, str(exc)) from None
            raise HTTPException(422, 'Diagnóstico inválido: se requiere un snapshot completo con identidad, versión y tablas permitidas.') from None
        record = {'id': str(uuid.uuid4()), 'created': self.ops.clock(), 'status': 'inspected',
                  'snapshot': snapshot, 'recommendation': proposal, 'mode': self.ops.settings.mode,
                  'ai_mode': self.ops.settings.ai_mode}
        with self.ops.store.transaction() as db:
            self.ops.store.put(db, 'delivery', record['id'], record)
            self.ops.audit(db, record['id'], self.ops.settings.technician_id, 'offline_diagnostic_imported')
        return record

    def read(self, id):
        with self.ops.store.transaction() as db:
            record = self.ops.required(db, 'delivery', id)
            proposal = record['recommendation']
            self.annotate(record['snapshot'], proposal, record['mode'])
            return record

    def history(self):
        with self.ops.store.transaction() as db:
            return [{'id': r['id'], 'created': r['created'], 'status': r['status'],
                     'identity': r['snapshot']['identity']} for r in sorted(
                         self.ops.store.all(db, 'delivery'), key=lambda r: r['created'], reverse=True)[:50]]

    def prepare(self, id, confirmed, continue_existing=False):
        if confirmed is not True:
            raise HTTPException(422, 'Confirme gateways, enlaces de igual costo y DHCP antes de preparar.')
        with self.ops.store.transaction() as db:
            record = self.ops.required(db, 'delivery', id)
            if record['status'] != 'inspected':
                raise HTTPException(409, 'La entrega ya fue preparada. Importe un diagnóstico para otra propuesta.')
            proposal = recommend(record['snapshot'], 'router-1', record['mode'], self.ops.settings.v7_lab_enabled)
            self.annotate(record['snapshot'], proposal, record['mode'])
            if continue_existing and not proposal['can_continue_existing']:
                raise HTTPException(409, 'La configuración contiene diferencias que requieren revisión manual.')
            if not proposal['available'] and not continue_existing:
                raise HTTPException(409, 'Diagnóstico incompatible con el procedimiento disponible.')
            r = {'id': id, 'session_id': 'offline:' + id, 'status': 'received',
                 'text': 'Configurar balanceo ECMP', 'technician': self.ops.settings.technician_id,
                 'mode': record['mode'], 'created': record['created'],
                 'target': proposal['target'], 'parameters': proposal['parameters']}
            if continue_existing:
                r['execution_policy'] = 'preserve_existing'
                self.ops.audit(db, id, self.ops.settings.technician_id, 'offline_continue_preserve_existing')
            record['ai_mode'] = self.ops.settings.ai_mode
            r = self.ops.graph.invoke({'record': r}, config={'recursion_limit': 20})['record']
            if r['status'] == 'await_precheck':
                r.update(status='precheck_received', precheck=record['snapshot'])
                r = self.ops.graph.invoke({'record': r}, config={'recursion_limit': 20})['record']
            record.update(status=r['status'], request=r)
            self.ops.store.put(db, 'delivery', id, record)
            self.ops.audit(db, id, self.ops.settings.technician_id, 'offline_prepared:' + r['status'])
            return record

    def decide(self, id, decision, binding_hash):
        with self.ops.store.transaction() as db:
            record = self.ops.required(db, 'delivery', id)
            r = record.get('request', {})
            if record['status'] != 'await_approval' or binding_hash != r.get('binding_hash'):
                raise HTTPException(409, 'La propuesta no está pendiente o cambió. Vuelva a revisarla.')
            if decision == 'reject':
                record['status'] = 'rejected'
            else:
                now = self.ops.clock()
                package = {'schema': SCHEMA, 'id': id, 'created': record['created'],
                           'approved_at': now, 'expires_at': now + LIFETIME,
                           'mode': record['mode'], 'ai_mode': record['ai_mode'],
                           'snapshot': record['snapshot'], 'snapshot_hash': r['precheck_hash']}
                for key in ('target', 'parameters', 'variant', 'artifact', 'executable', 'classification', 'plan', 'plan_hash'):
                    package[key] = r[key]
                if r.get('execution_policy') == 'preserve_existing':
                    package.update(schema='ecmp-offline/2', execution_policy='preserve_existing')
                package['package_hash'] = digest(package)
                validate_package(package, now)
                record.update(status='approved', package=package)
            self.ops.store.put(db, 'delivery', id, record)
            self.ops.audit(db, id, self.ops.settings.technician_id, 'offline_' + record['status'])
            return record

    def package(self, id):
        record = self.read(id)
        if record['status'] != 'approved':
            raise HTTPException(409, 'Autorice la propuesta antes de descargar.')
        try:
            return validate_package(record['package'], self.ops.clock())
        except ValueError:
            raise HTTPException(409, 'Entrega vencida o inválida. Importe el diagnóstico y prepare una nueva.') from None

    def executable(self, id, runner='offline_runner.py', filename='ECMP-cliente'):
        package = self.package(id)
        # UUID comes from the database, never from an unvalidated path parameter.
        folder = ROOT / 'runtime' / 'central-deliveries' / str(uuid.UUID(package['id']))
        output = folder / 'dist' / (filename + '.exe')
        manifest = folder / 'build.json'
        source_hash = runner_source_hash()
        if not BUILD_LOCK.acquire(blocking=False):
            raise HTTPException(409, 'Ya se está preparando un ejecutable. Espere a que termine y vuelva a descargar.')
        try:
            if output.is_file() and manifest.is_file():
                saved = json.loads(manifest.read_text(encoding='utf-8'))
                if (saved.get('package_hash') != package['package_hash'] or
                        saved.get('sha256') != hashlib.sha256(output.read_bytes()).hexdigest()):
                    raise HTTPException(409, 'El ejecutable guardado cambió. Prepare una nueva entrega.')
                if saved.get('source_hash') == source_hash:
                    return output
            python = Path(os.environ.get('ECMP_BUILD_PYTHON', str(ROOT / 'agent/.venv-portable/Scripts/python.exe')))
            if not python.is_file():
                raise HTTPException(503, 'No se encontró el entorno de empaquetado. Configure ECMP_BUILD_PYTHON según server/README.md.')
            folder.mkdir(parents=True, exist_ok=True)
            data = folder / 'delivery.json'
            data.write_text(json.dumps(package, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            command = [str(python), '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile',
                       '--name', filename, '--paths', str(ROOT),
                       '--distpath', str(folder / 'dist'), '--workpath', str(folder / 'build'),
                       '--specpath', str(folder), '--add-data', str(data) + os.pathsep + '.',
                       str(ROOT / 'server/app' / runner)]
            try:
                with (folder / 'build.log').open('w', encoding='utf-8') as log:
                    subprocess.run(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                                   timeout=240, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                subprocess.run([str(output), '--validate-only'], cwd=folder, capture_output=True,
                               timeout=45, check=True, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            except (OSError, subprocess.SubprocessError):
                raise HTTPException(503, 'No se pudo construir o validar el ejecutable. Consulte el build.log de esta entrega.') from None
            # Compilation time cannot extend the approval period.
            self.package(id)
            manifest.write_text(json.dumps({'package_hash': package['package_hash'], 'source_hash': source_hash,
                'sha256': hashlib.sha256(output.read_bytes()).hexdigest()}), encoding='utf-8')
            with self.ops.store.transaction() as db:
                self.ops.audit(db, id, self.ops.settings.technician_id, 'offline_executable_built')
            return output
        finally:
            BUILD_LOCK.release()

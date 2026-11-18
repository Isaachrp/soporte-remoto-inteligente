import subprocess

from fastapi import HTTPException

from shared.contracts import digest
from server.app.generator_catalog import catalog, fields, validate_parameters
from server.app.catalog_contract import validate, SCHEMA
from server.app.services.central_delivery import CentralDelivery
from server.app.services.catalog_ai import build_recommender
from server.app.services.catalog_generator import generate
from server.app.services.ai import AIError


class CatalogDelivery(CentralDelivery):
    def options(self, record, lines=2):
        options = catalog(record['snapshot'])
        for option in options:
            option['fields'] = fields(option['id'], record['snapshot'], lines)
            if option['id'] == 'ECMP' and record['snapshot']['version'].startswith('7.'):
                proposal = record['recommendation']
                supported = proposal['available'] or proposal.get('can_continue_existing')
                option['note'] = '' if supported else 'ECMP V7 requiere la base de laboratorio compatible.'
                option['lab_ecmp'] = True
                for spec in option['fields']:
                    if spec['name'] in proposal['parameters']:
                        spec['default'] = proposal['parameters'][spec['name']]
        return options

    def inspect(self, document):
        record = super().inspect(document)
        return self.analyze(record['id'])

    def analyze(self, id):
        record = super().read(id)
        if record['status'] != 'inspected':
            raise HTTPException(409, 'Carga un nuevo diagnóstico.')
        record['options'] = self.options(record)
        try:
            result = build_recommender(self.ops.settings).invoke({'snapshot': record['snapshot'], 'options': record['options']})
            record['recommendations'] = result['recommendations']
            record.pop('analysis_error', None)
            record.pop('analysis_error_message', None)
        except AIError as exc:
            record.pop('recommendations', None)
            record['analysis_error'] = exc.code
            from server.app.services.openrouter import ERROR_MESSAGES
            record['analysis_error_message'] = ERROR_MESSAGES.get(exc.code, 'No se pudo consultar la IA. Puedes reintentar o elegir del catálogo.')
        record['ai_mode'] = self.ops.settings.ai_mode
        with self.ops.store.transaction() as db:
            latest = self.ops.required(db, 'delivery', id)
            if latest['status'] != 'inspected':
                raise HTTPException(409, 'La entrega ya fue preparada.')
            self.ops.store.put(db, 'delivery', id, record)
            self.ops.audit(db, id, self.ops.settings.technician_id, 'catalog_analyzed' if 'recommendations' in record else 'catalog_ai_error')
        return record

    def prepare_selection(self, id, procedure, parameters, confirmed):
        if not confirmed:
            raise HTTPException(422, 'Confirma los parámetros para continuar.')
        record = super().read(id)
        if record['status'] != 'inspected':
            raise HTTPException(409, 'Carga un nuevo diagnóstico.')
        try:
            parameters = validate_parameters(procedure, parameters)
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from None
        option = next(o for o in self.options(record) if o['id'] == procedure)
        if option['note']:
            raise HTTPException(409, option['note'])
        if option.get('lab_ecmp'):
            expected = {k: v for k, v in record['recommendation']['parameters'].items() if k != 'tipo'}
            if parameters != expected:
                raise HTTPException(422, 'ECMP V7 utiliza los parámetros del laboratorio mostrado. Para otra topología selecciona una variante V7.')
            return super().prepare(id, True, record['recommendation'].get('can_continue_existing', False))
        try:
            artifact = generate(procedure, parameters)
        except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
            raise HTTPException(422, str(exc) if isinstance(exc, ValueError) else 'No se pudo ejecutar el generador PHP.') from None
        request = {'procedure': procedure, 'parameters': parameters, 'artifact': artifact,
                   'snapshot_hash': digest(record['snapshot']), 'execution_policy': 'original_php'}
        request['binding_hash'] = digest({'id': id, 'request': request})
        with self.ops.store.transaction() as db:
            current = self.ops.required(db, 'delivery', id)
            if current['status'] != 'inspected':
                raise HTTPException(409, 'La entrega ya fue preparada.')
            current.update(status='await_approval', catalog_delivery=True, request=request)
            self.ops.store.put(db, 'delivery', id, current)
            self.ops.audit(db, id, self.ops.settings.technician_id, 'catalog_php_generated:' + procedure)
        return current

    def decide(self, id, decision, binding_hash):
        record = super().read(id)
        if not record.get('catalog_delivery'):
            return super().decide(id, decision, binding_hash)
        with self.ops.store.transaction() as db:
            record = self.ops.required(db, 'delivery', id)
            request = record.get('request', {})
            if record['status'] != 'await_approval' or request.get('binding_hash') != binding_hash:
                raise HTTPException(409, 'La propuesta cambió o ya fue decidida.')
            if decision == 'reject':
                record['status'] = 'rejected'
            elif decision == 'approve':
                now = self.ops.clock()
                package = dict(schema=SCHEMA, id=id, created=record['created'], approved_at=now,
                               expires_at=now + 86400, snapshot=record['snapshot'], snapshot_hash=request['snapshot_hash'],
                               procedure=request['procedure'], parameters=request['parameters'], artifact=request['artifact'],
                               mode=record['mode'], ai_mode=record['ai_mode'])
                package['package_hash'] = digest(package)
                validate(package, now)
                record.update(status='approved', package=package)
            else:
                raise HTTPException(422, 'Decisión inválida.')
            self.ops.store.put(db, 'delivery', id, record)
            self.ops.audit(db, id, self.ops.settings.technician_id, 'catalog_' + record['status'])
        return record

    def package(self, id):
        record = super().read(id)
        if not record.get('catalog_delivery'):
            return super().package(id)
        if record['status'] != 'approved':
            raise HTTPException(409, 'Autoriza la propuesta antes de descargar.')
        try:
            return validate(record['package'], self.ops.clock())
        except ValueError:
            raise HTTPException(409, 'Entrega vencida o inválida. Genera una nueva.') from None

    def executable(self, id):
        record = super().read(id)
        if not record.get('catalog_delivery'):
            return super().executable(id)
        return super().executable(id, runner='catalog_runner.py', filename='Configuracion-cliente')

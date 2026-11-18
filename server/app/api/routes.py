import secrets
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Header, HTTPException
from shared.contracts import Request, Registration, Decision, Result, Parameters, Reconciliation, ACTIONS
from shared.snapshot import Snapshot

def routes(service):
    router = APIRouter()
    def bearer(authorization: str = Header(default='')):
        if not authorization.startswith('Bearer '):
            raise HTTPException(401,'No autorizado')
        return authorization[7:]

    def technician(token=Depends(bearer)):
        if not secrets.compare_digest(token,service.settings.technician_token):
            raise HTTPException(401,'No autorizado')

    @router.get('/health')
    def health():
        return {'status':'ok','mode':service.settings.mode,'ai_mode':service.settings.ai_mode,
                'real_write_enabled':service.settings.mode == 'real' and service.settings.v7_lab_enabled,
                'v7_lab_enabled':service.settings.v7_lab_enabled, 'ecmp_certified':False}

    @router.get('/actions',dependencies=[Depends(technician)])
    def actions():
        return ACTIONS

    @router.get('/devices', dependencies=[Depends(technician)])
    def devices():
        return service.devices()

    @router.post('/devices/{session_id}/inspect', dependencies=[Depends(technician)], status_code=201)
    def inspect(session_id: str):
        return service.inspect(session_id)

    @router.get('/inspections/{id}', dependencies=[Depends(technician)])
    def inspection(id: str):
        return service.inspection(id)

    @router.post('/inspections/{id}/prepare', dependencies=[Depends(technician)], status_code=201)
    def prepare_inspection(id: str):
        return service.prepare_inspection(id)

    @router.get('/history', dependencies=[Depends(technician)])
    def history():
        service.sweep()
        with service.store.transaction() as db:
            return [{'id': r['id'], 'created': r['created'], 'identity': r['target']['identity'],
                     'status': r['status']} for r in sorted(service.store.all(db, 'request'),
                     key=lambda r: r['created'], reverse=True)[:50]]

    @router.post('/requests',dependencies=[Depends(technician)],status_code=201)
    def create(body: Request):
        return service.create(body)

    @router.get('/requests/{id}',dependencies=[Depends(technician)])
    def read(id: str):
        return service.read(id)

    @router.put('/requests/{id}/parameters',dependencies=[Depends(technician)])
    def parameters(id: str, body: Parameters):
        return service.parameters(id,body)

    @router.post('/requests/{id}/decision',dependencies=[Depends(technician)])
    def decision(id: str, body: Decision):
        return service.decision(id,body)

    @router.get('/requests/{id}/audit',dependencies=[Depends(technician)])
    def audit(id: str):
        return service.audits(id)

    @router.get('/requests/{id}/report',dependencies=[Depends(technician)])
    def report(id: str):
        record = service.read(id)
        return {'schema': 'ecmp-delivery/1', 'exported_at': datetime.now(timezone.utc).isoformat(),
                'inspection': service.inspection(record['inspection_id']) if record.get('inspection_id') else None,
                'mode': record['mode'], 'ai_mode': service.settings.ai_mode,
                'real_write_enabled': service.settings.mode == 'real' and service.settings.v7_lab_enabled,
                'v7_lab_enabled': service.settings.v7_lab_enabled, 'ecmp_certified':False,
                'request': record, 'audit': service.audits(id),
                'limitations': ['Sin certificacion ECMP en RouterOS real.',
                                'Trafico WAN y conectividad LAN no verificados.']}

    @router.post('/requests/{id}/reconcile',dependencies=[Depends(technician)])
    def reconcile(id: str, body: Reconciliation):
        return service.reconcile(id,body.session_id)

    @router.post('/agent/sessions',status_code=201)
    def register(body: Registration, token=Depends(bearer)):
        if not secrets.compare_digest(token,service.settings.agent_token):
            raise HTTPException(401,'No autorizado')
        return service.register(body)

    @router.post('/agent/sessions/{id}/heartbeat')
    def heartbeat(id: str, token=Depends(bearer)):
        return service.heartbeat(id,token)

    @router.delete('/agent/sessions/{id}')
    def close(id: str, token=Depends(bearer)):
        return service.heartbeat(id,token,close=True)

    @router.get('/agent/sessions/{id}/tasks')
    def poll(id: str, token=Depends(bearer)):
        return service.poll(id,token)

    @router.post('/agent/sessions/{id}/tasks/{task_id}/claim')
    def claim(id: str, task_id: str, body: Snapshot, token=Depends(bearer)):
        return service.claim(id,token,task_id,body.model_dump())

    @router.post('/agent/sessions/{id}/tasks/{task_id}/result')
    def result(id: str, task_id: str, body: Result, token=Depends(bearer)):
        return service.result(id,token,task_id,body)

    return router

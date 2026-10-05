import secrets
import json
import logging
import time
import uuid
from fastapi import HTTPException
from shared.contracts import ACTIONS, digest, variant
from shared.ecmp import precheck, validate_artifact
from server.app.storage import Store
from server.app.workflow import build_workflow, approval_binding
from server.app.services.ai import Interpreter
from server.app.services.generator import Generator
from server.app.ai.models import ActionObservation
from server.app.ai.policy import PlanValidator
from server.app.ai.results import MESSAGES, analyze, final_response, sync_state

logger = logging.getLogger('ecmp.workflow')

def fail(condition, code=409, detail='Estado o autorizacion invalida'):
    if condition:
        raise HTTPException(code, detail)

class Operations:
    def __init__(self, settings, generator=None, interpreter=None, clock=time.time):
        self.settings = settings
        self.clock = clock
        self.store = Store(settings.database)
        self.graph = build_workflow(interpreter or Interpreter(settings), generator or Generator(settings))

    def audit(self, db, request_id, actor, event):
        db.execute('INSERT INTO audit(request_id,at,actor,event) VALUES(?,?,?,?)', (request_id,self.clock(),actor,event))
        logger.info('audit_event request_id=%s actor=%s event=%s', request_id, actor, event)

    def required(self, db, kind, id):
        value = self.store.get(db,kind,id)
        fail(value is None,404,'No encontrado')
        return value

    def session(self, db, session_id, token=None):
        s = self.required(db,'session',session_id)
        fail(s['expires'] <= self.clock() or s['closed'],401,'Sesion vencida')
        if token is not None:
            fail(not secrets.compare_digest(s['token_hash'],digest(token)),401,'No autorizado')
        return s

    def register(self, registration):
        fail(registration.agent_id != self.settings.agent_id,403)
        fail(registration.mode != self.settings.mode,409,'Modo del agente distinto al servidor')
        with self.store.transaction() as db:
            # Re-registration cannot adopt delivered/approved work from an old session.
            id, token = str(uuid.uuid4()), secrets.token_urlsafe(32)
            s = registration.model_dump() | {'id':id,'token_hash':digest(token),'expires':self.clock()+self.settings.session_seconds,'last_seen':self.clock(),'closed':False}
            self.store.put(db,'session',id,s)
            self.audit(db,None,registration.agent_id,'session_registered')
        return {'session_id':id,'session_token':token,'expires':s['expires']}

    def advance(self, db, r):
        for key in ('final_response', 'result_analysis', 'analysis_source', 'workflow_events'):
            r.pop(key, None)
        r = self.graph.invoke({'record':r}, config={'recursion_limit': 20})['record']
        r['message'] = r.get('final_response', {}).get('summary', MESSAGES.get(r['status'], r['status']))
        phase = {'await_precheck':'get_ecmp_precheck','await_execution':'apply_approved_ecmp','await_verification':'verify_ecmp'}.get(r['status'])
        if phase:
            PlanValidator().authorize_dispatch(r, phase)
            id = r['id'] + ':' + phase
            if self.store.get(db,'task',id) is None:
                task = {'id':id,'request_id':r['id'],'session_id':r['session_id'],'action':phase,
                        'status':'pending','created':self.clock(),'deadline':self.clock()+300,
                        'payload':{'target':r['target'],'parameters':r['parameters'],'mode':r['mode']}}
                if phase != 'get_ecmp_precheck':
                    task['payload'].update(artifact=r['artifact'],executable=r['executable'],precheck_hash=r['precheck_hash'],binding_hash=r['binding_hash'],binding=r['binding'])
                self.store.put(db,'task',id,task)
                r['task_id'] = id
        if r.get('artifact'):
            generation = r['artifact']['generation_id']
            existing = self.store.get(db,'artifact',generation)
            fail(existing is not None and existing != r['artifact'])
            if existing is None:
                self.store.put(db,'artifact',generation,r['artifact'])
        sync_state(r)
        for event in r.pop('workflow_events', []):
            self.audit(db, r['id'], 'workflow', json.dumps(event, sort_keys=True))
        self.store.put(db,'request',r['id'],r)
        self.audit(db,r['id'],'workflow',r['status'])
        return r

    def create(self, request):
        with self.store.transaction() as db:
            s = self.session(db,request.session_id)
            fail(s['router_id'] != request.target.router_id)
            fail(self.clock()-s['last_seen'] > self.settings.heartbeat_seconds,409,'Agente desconectado')
            # Only one unfinished request per physical router reference.
            terminal = {'out_of_scope','rejected','expired','invalid_plan','ai_error','configuration_failed','configuration_with_warnings','configuration_successful'}
            fail(any(r['target']['router_id'] == s['router_id'] and r['status'] not in terminal for r in self.store.all(db,'request')),409,'Router tiene operacion pendiente; requiere reconciliacion')
            r = request.model_dump() | {'id':str(uuid.uuid4()),'status':'received','technician':self.settings.technician_id,'mode':s['mode'],'created':self.clock()}
            return self.advance(db,r)

    def parameters(self, id, parameters):
        with self.store.transaction() as db:
            r = self.required(db,'request',id)
            fail(r['status'] != 'await_parameters')
            self.session(db,r['session_id'])
            r.update(parameters=parameters.model_dump(),status='planning_ready' if r.get('ai_schema') == 1 else 'parameters_ready')
            return self.advance(db,r)

    def decision(self, id, decision):
        with self.store.transaction() as db:
            r = self.required(db,'request',id)
            fail(r['status'] != 'await_approval')
            fail(decision.binding_hash != r['binding_hash'])
            self.session(db,r['session_id'])
            if decision.decision == 'reject':
                r['status'] = 'rejected'
            else:
                # Bound approval is immutable and single-use. Artifact is revalidated.
                try:
                    PlanValidator().authorize_dispatch(r, 'apply_approved_ecmp')
                except (ValueError, KeyError):
                    raise HTTPException(409, 'Plan invalido o alterado') from None
                fail(validate_artifact(r['artifact'],r['parameters']) != r['executable'])
                id_approval = str(uuid.uuid4())
                approval = {'id':id_approval,'request_id':id,'binding':r['binding'],'binding_hash':r['binding_hash'],
                            'technician':self.settings.technician_id,'created':self.clock(),'expires':self.clock()+self.settings.approval_seconds,'used':False}
                self.store.put(db,'approval',id_approval,approval)
                r.update(approval_id=id_approval,status='await_execution',approved_actions=['apply_approved_ecmp'])
            self.audit(db,id,self.settings.technician_id,decision.decision)
            return self.advance(db,r)

    def heartbeat(self, id, token, close=False):
        with self.store.transaction() as db:
            s = self.session(db,id,token)
            s.update(last_seen=self.clock(),closed=close)
            self.store.put(db,'session',id,s)
        self.sweep()
        return {'status':'closed' if close else 'online'}

    def reconcile(self, id, session_id):
        with self.store.transaction() as db:
            r = self.required(db,'request',id)
            fail(r['status'] != 'intervention_required' or not r.get('artifact'))
            s = self.session(db,session_id)
            fail(s['router_id'] != r['target']['router_id'] or s['mode'] != r['mode'],403)
            fail(any(t['request_id'] == id and t['status'] in ('pending','delivered','claimed') for t in self.store.all(db,'task')))
            task_id = str(uuid.uuid4())
            task = {'id':task_id,'request_id':id,'session_id':session_id,'action':'verify_ecmp','reconciliation':True,
                    'status':'pending','created':self.clock(),'deadline':self.clock()+300,
                    'payload':{k:r[k] for k in ('target','parameters','mode','artifact','executable','precheck_hash','binding_hash','binding')}}
            self.store.put(db,'task',task_id,task)
            self.audit(db,id,self.settings.technician_id,'reconciliation_requested')
            return {'task_id':task_id,'write_authorized':False}

    def poll(self, id, token):
        self.sweep()
        with self.store.transaction() as db:
            self.session(db,id,token)
            for t in self.store.all(db,'task'):
                if t['session_id'] == id and t['status'] == 'pending':
                    t.update(status='delivered',deadline=self.clock()+ACTIONS[t['action']]['timeout'])
                    self.store.put(db,'task',t['id'],t)
                    self.audit(db,t['request_id'],'agent','task_delivered')
                    return t
        return None

    def claim(self, id, token, task_id, snapshot):
        self.sweep()
        with self.store.transaction() as db:
            s = self.session(db,id,token)
            t = self.required(db,'task',task_id)
            fail(t['session_id'] != id,403)
            fail(t['action'] != 'apply_approved_ecmp' or t['status'] != 'delivered' or t['deadline'] <= self.clock())
            r = self.required(db,'request',t['request_id'])
            try:
                PlanValidator().authorize_dispatch(r, 'apply_approved_ecmp')
            except (ValueError, KeyError):
                raise HTTPException(409, 'Plan invalido o alterado') from None
            a = self.required(db,'approval',r['approval_id'])
            fail(a['used'] or a['expires'] <= self.clock() or r['status'] != 'await_execution')
            fail(a['binding_hash'] != digest(r['binding']) or a['binding'] != r['binding'])
            fail(approval_binding(r) != a['binding'])
            fail(r['binding_hash'] != t['payload']['binding_hash'])
            fail(validate_artifact(r['artifact'],r['parameters']) != r['executable'])
            try:
                fail(variant(snapshot['version'],s['mode']) != r['variant'])
                fail(precheck(snapshot,r['target'],r['parameters']) != r['precheck_hash'])
            except (KeyError, ValueError):
                raise HTTPException(409,'Condiciones previas cambiaron')
            a.update(used=True,used_at=self.clock())
            t['status'] = 'claimed'
            self.store.put(db,'approval',a['id'],a)
            self.store.put(db,'task',t['id'],t)
            self.audit(db,r['id'],s['agent_id'],'approval_consumed')
            return {'task_id':task_id,'binding_hash':a['binding_hash'],'expires':min(a['expires'],t['deadline'])}

    def result(self, id, token, task_id, result):
        self.sweep()
        with self.store.transaction() as db:
            self.session(db,id,token)
            t = self.required(db,'task',task_id)
            fail(t['session_id'] != id,403)
            data = result.model_dump()
            if t['status'] == 'completed':
                fail(t['result_hash'] != digest(data),409,'Resultado duplicado conflictivo')
                return {'duplicate':True}
            fail(t['status'] not in ('delivered','claimed'),409,'Resultado tardio: requiere reconciliacion')
            if t['action'] == 'apply_approved_ecmp' and data['status'] == 'ok':
                fail(t['status'] != 'claimed',403)
            # Only closed, normalized snapshots are accepted; discard unexpected secrets.
            if data['snapshot'] is not None:
                from shared.snapshot import Snapshot
                data['snapshot'] = Snapshot.model_validate(data['snapshot']).model_dump()
            t.update(status='completed',result=data,result_hash=digest(data))
            self.store.put(db,'task',task_id,t)
            r = self.required(db,'request',t['request_id'])
            observation = ActionObservation(task_id=task_id, action_id=t['action'],
                status=data['status'], completed=data['completed'], error=data['error'])
            r.setdefault('action_results', []).append(observation.model_dump())
            self.audit(db, r['id'], 'agent', json.dumps({'action': t['action'], 'result': data['status'],
                                                       'error': data['error']}, sort_keys=True))
            if t.get('reconciliation'):
                r['reconciliation_observed'] = True
            if t['action'] == 'get_ecmp_precheck':
                if data['status'] == 'ok' and data['snapshot']:
                    r.update(precheck=data['snapshot'],status='precheck_received')
                else:
                    r.update(status='intervention_required',reason='precheck_failed')
            elif t['action'] == 'apply_approved_ecmp':
                r.update(execution_result=data,status='execution_received')
            else:
                r.update(verification_result=data,status='verification_received')
            r = self.advance(db,r)
            return {'duplicate':False}

    def sweep(self):
        with self.store.transaction() as db:
            now = self.clock()
            for t in self.store.all(db,'task'):
                if t['status'] not in ('pending','delivered','claimed'):
                    continue
                s = self.required(db,'session',t['session_id'])
                r = self.required(db,'request',t['request_id'])
                a = self.store.get(db,'approval',r.get('approval_id',''))
                stale = s['closed'] or s['expires'] <= now or now-s['last_seen'] > self.settings.heartbeat_seconds
                expired = t['deadline'] <= now or (a and not a['used'] and a['expires'] <= now)
                if stale or expired:
                    uncertain = t['action'] == 'apply_approved_ecmp' and t['status'] in ('delivered','claimed')
                    t['status'] = 'uncertain' if uncertain else 'expired'
                    r.update(status='intervention_required',reason='execution_uncertain' if uncertain else 'agent_offline_or_expired',reconciliation_required=True)
                    # Recovery must not depend on model availability or create retries.
                    analyze(r)
                    final_response(r)
                    sync_state(r)
                    self.store.put(db,'task',t['id'],t)
                    self.store.put(db,'request',r['id'],r)
                    self.audit(db,r['id'],'recovery',r['reason'])

    def read(self, id):
        self.sweep()
        with self.store.transaction() as db:
            return self.required(db,'request',id)

    def audits(self, id):
        with self.store.transaction() as db:
            self.required(db,'request',id)
            return [dict(row) for row in db.execute('SELECT * FROM audit WHERE request_id=? ORDER BY seq',(id,))]

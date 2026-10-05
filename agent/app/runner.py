import ssl
import time
from shared.contracts import ACTIONS, ADAPTER, VERSION, digest, variant
from shared.ecmp import precheck, validate_artifact

class Agent:
    def __init__(self, client, router, agent_id, router_id, bootstrap_token):
        self.client, self.router = client, router
        self.agent_id, self.router_id = agent_id, router_id
        self.bootstrap_token = bootstrap_token
        self.session_id = None
        self.seen = set()

    def register(self):
        response = self.client.post('/agent/sessions',headers={'Authorization':'Bearer '+self.bootstrap_token},
            json={'agent_id':self.agent_id,'router_id':self.router_id,'version':VERSION,'mode':self.router.mode})
        response.raise_for_status()
        body = response.json()
        self.session_id = body['session_id']
        self.client.headers['Authorization'] = 'Bearer '+body['session_token']
        self.bootstrap_token = None
        return self.session_id

    @property
    def base(self):
        return '/agent/sessions/'+self.session_id

    def step(self):
        self.client.post(self.base+'/heartbeat').raise_for_status()
        response = self.client.get(self.base+'/tasks')
        response.raise_for_status()
        task = response.json()
        if task is None:
            return False
        # Duplicate delivery is never a reason to repeat a write.
        if task['id'] in self.seen:
            raise ValueError('Tarea repetida')
        self.seen.add(task['id'])
        result = self.execute(task)
        # Retrying this POST is safe, but no action execution is retried.
        for attempt in range(3):
            try:
                response = self.client.post(self.base+'/tasks/'+task['id']+'/result',json=result)
                response.raise_for_status()
                return True
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(0.2)

    def execute(self, task):
        action = task['action']
        writing = False
        try:
            if action not in ACTIONS or task['session_id'] != self.session_id or task['deadline'] <= time.time():
                raise ValueError('Tarea invalida')
            payload = task['payload']
            if payload['mode'] != self.router.mode or payload['target']['router_id'] != self.router_id:
                raise ValueError('Destino invalido')
            if action == 'get_ecmp_precheck':
                return {'status':'ok','snapshot':self.router.snapshot()}
            executable = validate_artifact(payload['artifact'],payload['parameters'])
            if executable != payload['executable'] or executable['adapter_version'] != ADAPTER:
                raise ValueError('Representacion alterada')
            if action == 'verify_ecmp':
                return {'status':'ok','snapshot':self.router.snapshot()}
            binding = payload['binding']
            actual = binding | {
                'id':task['request_id'],'session_id':self.session_id,'target':payload['target'],
                'parameters':payload['parameters'],'mode':self.router.mode,'precheck_hash':payload['precheck_hash'],
                'generation_id':payload['artifact']['generation_id'],
                'generator_version':payload['artifact']['generator_version'],
                'script_hash':payload['artifact']['script_hash'],
                'adapter_version':executable['adapter_version'],'operations_hash':executable['operations_hash'],
            }
            if actual != binding or digest(actual) != payload['binding_hash']:
                raise ValueError('Artefacto distinto del aprobado')
            current = self.router.snapshot()
            if variant(current['version'], self.router.mode) != binding['variant']:
                raise ValueError('Variante distinta de la aprobada')
            if precheck(current,payload['target'],payload['parameters']) != payload['precheck_hash']:
                raise ValueError('Precondiciones alteradas')
            claim = self.client.post(self.base+'/tasks/'+task['id']+'/claim',json=current)
            claim.raise_for_status()
            permit = claim.json()
            if permit['task_id'] != task['id'] or permit['binding_hash'] != payload['binding_hash'] or permit['expires'] <= time.time():
                raise ValueError('Autorizacion invalida')
            # Same connection; validate immediately before the first operation.
            if digest(self.router.snapshot()) != payload['precheck_hash']:
                raise ValueError('Estado cambiado antes de escribir')
            writing = True
            completed = self.router.apply(executable['operations'])
            return {'status':'ok','completed':completed}
        except Exception as exc:
            code = 'tls' if isinstance(exc,ssl.SSLError) else 'timeout' if isinstance(exc,TimeoutError) else 'validation' if isinstance(exc,ValueError) else 'connection'
            return {'status':'uncertain' if writing else 'failed','error':code}

    def close(self):
        try:
            if self.session_id:
                self.client.delete(self.base)
        finally:
            self.router.close()
            self.client.headers.pop('Authorization',None)
            self.client.close()

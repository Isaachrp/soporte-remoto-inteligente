"""librouteros transport; native API TLS only. Never execute terminal text."""
import copy
import json
import ssl
import time
from functools import partial
from shared.snapshot import READ_FIELDS, Snapshot, fields_for
from shared.contracts import variant, V7_LAB_VARIANT
from shared.ecmp import FIELDS

def tls_wrapper(host, ca_file):
    context = ssl.create_default_context(cafile=ca_file)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    return partial(context.wrap_socket, server_hostname=host)

class NativeRouter:
    mode = 'real'
    def __init__(self, host, username, password, ca_file, timeout=5, lab_enabled=False):
        if type(lab_enabled) is not bool or (lab_enabled and host != '10.255.255.1'):
            raise ValueError('Ensayo v7 limitado al host de laboratorio 10.255.255.1')
        self.lab_enabled = lab_enabled
        from librouteros import connect
        self.api = connect(host=host, username=username, password=password, port=8729,
                           timeout=timeout, ssl_wrapper=tls_wrapper(host,ca_file))

    def snapshot(self):
        identity = list(self.api('/system/identity/print', **{'.proplist':'name'}))[0]['name']
        version = list(self.api('/system/resource/print', **{'.proplist':'version'}))[0]['version']
        tables = {}
        for table, fields in fields_for(version).items():
            rows = self.api(table+'/print', **{'.proplist':','.join(sorted(fields))})
            tables[table] = [{k:str(v).lower() if isinstance(v,bool) else str(v) for k,v in row.items() if k in fields} for row in rows]
            if version.startswith('7.'):
                tables[table].sort(key=lambda row: json.dumps(row, sort_keys=True))
        return Snapshot(identity=identity,version=version,tables=tables).model_dump()

    def apply(self, operations):
        # The optional exact lab gate never populates CERTIFIED.
        selected = variant(self.snapshot()['version'], 'real', getattr(self, 'lab_enabled', False))
        allowed = FIELDS
        if selected == V7_LAB_VARIANT:
            from shared.v7 import FIELDS as allowed, expected_operations
            p = {'tipo': 'ECMP', 'lineas': 2, 'lan': '172.16.0.1', 'dhcp': len(operations) == 7,
                 'vel1': '5M', 'vel2': '5M', 'gw1': '192.168.1.1', 'gw2': '192.168.2.1', 'ip1': 2, 'ip2': 2}
            if any(op['selector'] for op in operations) or [(op['command'], op['args']) for op in operations] != expected_operations(p):
                raise ValueError('Operaciones fuera del contrato de laboratorio')
        completed, started = 0, time.monotonic()
        for op in operations:
            if time.monotonic()-started > 110 or op['command'] not in allowed or set(op['args']) - allowed[op['command']]:
                raise ValueError('Operacion nativa invalida o vencida')
            args = dict(op['args'])
            if op['selector']:
                if op['command'] != '/interface/ethernet/set' or set(op['selector']) != {'default-name'}:
                    raise ValueError('Selector no permitido')
                rows = list(self.api('/interface/ethernet/print', **{'.proplist':'.id,default-name'}))
                matches = [row for row in rows if row.get('default-name') == op['selector']['default-name']]
                if len(matches) != 1 or not matches[0].get('.id'):
                    raise ValueError('Selector ambiguo')
                args['.id'] = matches[0]['.id']
            elif op['command'] == '/interface/ethernet/set':
                raise ValueError('Selector requerido')
            # Consume the iterator: !trap/errors must propagate, no retry.
            list(self.api(op['command'], **args))
            completed += 1
        return completed

    def close(self):
        self.api.close()

class SimulatedRouter:
    mode = 'simulated'
    def __init__(self, identity='lab-router', version='6.49.18', interfaces=14):
        self.data = {'identity':identity,'version':version,'tables':{table:[] for table in fields_for(version)}}
        self.data['tables']['/interface/ethernet'] = [{'.id':f'*{i}','default-name':f'ether{i}','name':f'ether{i}'} for i in range(1,interfaces+1)]
        self.data['tables']['/ip/address'] = [{'address':'10.255.255.1/24','interface':f'ether{interfaces}'}]
        self.calls = 0

    def snapshot(self):
        return copy.deepcopy(self.data)

    def apply(self, operations):
        completed = 0
        for op in operations:
            self.calls += 1
            table, action = op['command'].rsplit('/',1)
            rows = self.data['tables'][table]
            if op['selector']:
                matches = [row for row in rows if all(row.get(k) == v for k,v in op['selector'].items())]
                if len(matches) != 1:
                    raise ValueError('Selector ambiguo')
                matches[0].update(op['args'])
            elif action == 'set':
                rows[:] = [dict(op['args'])]
            else:
                rows.append(dict(op['args']))
                if table == '/ip/route':
                    rows[-1]['active'] = 'true'
            completed += 1
        return completed

    def close(self):
        pass

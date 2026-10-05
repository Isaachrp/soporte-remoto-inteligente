"""Restricted translation of the trusted PHP artifact, never a script generator."""
import re
import shlex
from shared.contracts import ADAPTER, GENERATOR, Parameters, digest, normalize

FIELDS = {
    '/interface/ethernet/set': {'comment', 'name'},
    '/ip/address/add': {'address', 'network', 'broadcast', 'interface'},
    '/ip/firewall/nat/add': {'chain', 'out-interface', 'action'},
    '/ip/firewall/mangle/add': {'chain', 'in-interface', 'action', 'new-connection-mark', 'connection-mark', 'new-routing-mark'},
    '/ip/route/add': {'dst-address', 'distance', 'gateway', 'routing-mark', 'check-gateway'},
    '/ip/dns/set': {'allow-remote-requests', 'servers'},
    '/ip/pool/add': {'name', 'ranges'},
    '/ip/dhcp-server/add': {'address-pool', 'disabled', 'interface', 'lease-time', 'name'},
    '/ip/dhcp-server/network/add': {'address', 'dns-server', 'gateway'},
}
TABLES = sorted({path.rsplit('/', 1)[0] for path in FIELDS})

def compile_script(script):
    operations, section = [], None
    for line_number, line in enumerate(script.splitlines(), 1):
        if not line.strip():
            continue
        if line.startswith('/'):
            section = '/' + '/'.join(line.lstrip('/').split())
            if section not in TABLES:
                raise ValueError('Seccion no permitida')
            continue
        selector = None
        match = re.match(r'^set \[ find default-name=(ether[1-9][0-9]*) \] ', line)
        if match:
            selector = {'default-name': match[1]}
            line = 'set ' + line[match.end():]
        if re.search(r'[;\[\]{}$\\<>\x00-\x1f]', line):
            raise ValueError('Sintaxis no soportada')
        words = shlex.split(line)
        command = f'{section}/{words[0]}'
        if command not in FIELDS:
            raise ValueError('Operacion no permitida')
        args = {}
        for word in words[1:]:
            key, sep, value = word.partition('=')
            if not sep or key not in FIELDS[command] or key in args or not value:
                raise ValueError('Argumento no permitido')
            args[key] = value
        if not args or (command == '/interface/ethernet/set') != bool(selector):
            raise ValueError('Selector invalido')
        operations.append({'command': command, 'args': args, 'selector': selector, 'line': line_number})
    if not operations or len(operations) > 150:
        raise ValueError('Artefacto vacio o excesivo')
    return operations

def validate_artifact(artifact, parameters):
    p = Parameters.model_validate(parameters).model_dump()
    if artifact['procedure'] != 'ECMP' or artifact['generator_version'] != GENERATOR or artifact['routeros_family'] != 'v6' or artifact['parameters'] != p:
        raise ValueError('Metadatos de artefacto incorrectos')
    script = artifact['script']
    if len(script) > 500000 or script != normalize(script) or digest(script) != artifact['script_hash']:
        raise ValueError('Integridad del artefacto incorrecta')
    ops = compile_script(script)
    return {'adapter_version': ADAPTER, 'operations': ops, 'operations_hash': digest(ops)}

def precheck(snapshot, target, parameters):
    if snapshot['identity'] != target['identity']:
        raise ValueError('Identidad distinta')
    interfaces = snapshot['tables']['/interface/ethernet']
    touched = {f'ether{i}' for i in range(1, parameters['lineas']+2)}
    present = [row.get('default-name') for row in interfaces]
    if not touched.issubset(present) or len(present) != len(set(present)):
        raise ValueError('Interfaces insuficientes o ambiguas')
    management = target['management_interface']
    if management in touched or management not in present:
        raise ValueError('Se requiere puerto administrativo dedicado fuera de los puertos modificados')
    if any(row.get('name') != row.get('default-name') for row in interfaces):
        raise ValueError('Interfaces ya renombradas; requiere revision manual')
    tables = snapshot['tables']
    if tables.get('/interface/bridge/port'):
        raise ValueError('Puertos en bridge requieren preparacion manual')
    if not any(row.get('interface') == management for row in tables['/ip/address']):
        raise ValueError('Sin direccion administrativa dedicada')
    if any(row.get('interface') != management for row in tables['/ip/address']):
        raise ValueError('Direcciones existentes en puertos de trabajo')
    for table in ('/ip/route','/ip/firewall/nat','/ip/firewall/mangle','/ip/pool','/ip/dhcp-server','/ip/dhcp-server/network'):
        if tables.get(table):
            raise ValueError('Configuracion previa requiere revision manual')
    return digest(snapshot)

def verify(snapshot, operations):
    checks = []
    for op in operations:
        table = op['command'].rsplit('/', 1)[0]
        expected = op['args'] | (op['selector'] or {})
        rows = snapshot['tables'].get(table, [])
        found = any(all(str(row.get(k, '')).lower() == v.lower() for k, v in expected.items()) for row in rows)
        if table == '/ip/route':
            found = found and any(row.get('active') in (True, 'true', 'yes') and all(str(row.get(k, '')) == v for k, v in expected.items()) for row in rows)
        checks.append({'line': op['line'], 'status': 'passed' if found else 'failed'})
    checks.extend([{'test': 'WAN traffic', 'status': 'not_performed'}, {'test': 'LAN connectivity', 'status': 'not_performed'}])
    return {'outcome': 'configuration_failed' if any(c['status'] == 'failed' for c in checks) else 'configuration_with_warnings', 'checks': checks}

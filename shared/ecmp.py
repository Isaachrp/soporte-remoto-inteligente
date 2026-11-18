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

def compile_script(script, family='v6'):
    if family == 'v7':
        from shared.v7 import FIELDS as allowed
    elif family == 'v6':
        allowed = FIELDS
    else:
        raise ValueError('Familia desconocida')
    sections = {path.rsplit('/', 1)[0] for path in allowed}
    operations, section = [], None
    for line_number, line in enumerate(script.splitlines(), 1):
        if not line.strip():
            continue
        if family == 'v7' and line.startswith('#'):
            continue
        if line.startswith('/'):
            section = '/' + '/'.join(line.lstrip('/').split())
            if section not in sections:
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
        if command not in allowed:
            raise ValueError('Operacion no permitida')
        args = {}
        for word in words[1:]:
            key, sep, value = word.partition('=')
            if not sep or key not in allowed[command] or key in args or not value:
                raise ValueError('Argumento no permitido')
            args[key] = value
        if not args or (command == '/interface/ethernet/set') != bool(selector):
            raise ValueError('Selector invalido')
        operations.append({'command': command, 'args': args, 'selector': selector, 'line': line_number})
    if not operations or len(operations) > 150:
        raise ValueError('Artefacto vacio o excesivo')
    return operations

def validate_artifact(artifact, parameters):
    if artifact.get('routeros_family') == 'v7':
        from shared.contracts import V7_LAB_GENERATOR, V7_LAB_ADAPTER, V7_LAB_VERSION
        from shared.v7 import parameters as validate_parameters, expected_operations
        p = validate_parameters(parameters)
        if (artifact.get('schema') != 'ecmp-v7-lab-execution/1' or artifact.get('procedure') != 'ECMP'
                or artifact.get('generator_version') != V7_LAB_GENERATOR or artifact.get('target_version') != V7_LAB_VERSION
                or artifact.get('target_identity') != 'lab-router' or artifact.get('parameters') != p
                or artifact.get('preview_only') is not False or artifact.get('certified') is not False
                or artifact.get('agent_execution_supported') is not True or artifact.get('lab_only') is not True
                or not re.fullmatch(r'[a-f0-9]{32}', artifact.get('generation_id', ''))):
            raise ValueError('Artefacto v7 fuera del contrato de laboratorio')
        script = artifact['script']
        if len(script) > 500000 or script != normalize(script) or digest(script) != artifact['script_hash']:
            raise ValueError('Integridad del artefacto incorrecta')
        ops = compile_script(script, 'v7')
        if any(op['selector'] for op in ops) or [(op['command'], op['args']) for op in ops] != expected_operations(p):
            raise ValueError('Operaciones distintas del contrato v7')
        return {'adapter_version': V7_LAB_ADAPTER, 'operations': ops, 'operations_hash': digest(ops)}
    p = Parameters.model_validate(parameters).model_dump()
    if artifact['procedure'] != 'ECMP' or artifact['generator_version'] != GENERATOR or artifact['routeros_family'] != 'v6' or artifact['parameters'] != p:
        raise ValueError('Metadatos de artefacto incorrectos')
    script = artifact['script']
    if len(script) > 500000 or script != normalize(script) or digest(script) != artifact['script_hash']:
        raise ValueError('Integridad del artefacto incorrecta')
    ops = compile_script(script)
    return {'adapter_version': ADAPTER, 'operations': ops, 'operations_hash': digest(ops)}

def precheck(snapshot, target, parameters, lab_enabled=False):
    if snapshot['version'].startswith('7.'):
        if lab_enabled is not True:
            raise ValueError('Ensayo v7 deshabilitado')
        from shared.v7 import precheck as lab_precheck
        return lab_precheck(snapshot, target, parameters)
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
    if snapshot['version'].startswith('7.'):
        from shared.v7 import verify as lab_verify
        return lab_verify(snapshot, operations)
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

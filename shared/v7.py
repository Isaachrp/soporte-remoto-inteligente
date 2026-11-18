"""Exact, prepared-lab contract. Experimental authorization is not certification."""
from shared.contracts import Parameters, V7_LAB_VERSION, digest

ADDRESSES = {
    'ether1': '192.168.1.2/24', 'ether2': '192.168.2.2/24',
    'ether3': '172.16.0.1/24', 'ether4': '10.255.255.1/24',
}
FIELDS = {
    '/ip/firewall/nat/add': {'chain', 'src-address', 'out-interface', 'action', 'comment'},
    '/ip/route/add': {'dst-address', 'gateway', 'routing-table', 'distance', 'check-gateway', 'comment'},
    '/ip/pool/add': {'name', 'ranges'},
    '/ip/dhcp-server/network/add': {'address', 'gateway', 'dns-server', 'comment'},
    '/ip/dhcp-server/add': {'name', 'interface', 'address-pool', 'lease-time', 'disabled'},
}


def parameters(value):
    p = Parameters.model_validate(value).model_dump()
    if (p['lineas'] != 2 or p['lan'] != '172.16.0.1' or p['gw1'] != '192.168.1.1'
            or p['gw2'] != '192.168.2.1' or p['ip1'] != 2 or p['ip2'] != 2
            or p['vel1'] != p['vel2']):
        raise ValueError('Solo laboratorio preparado de dos WAN de igual costo')
    return p


def expected_operations(value):
    p = parameters(value)
    rows = []
    for i in (1, 2):
        rows.append(('/ip/firewall/nat/add', {
            'chain': 'srcnat', 'src-address': '172.16.0.0/24', 'out-interface': f'ether{i}',
            'action': 'masquerade', 'comment': f'ECMP7-LAB-NAT{i}',
        }))
    for i in (1, 2):
        rows.append(('/ip/route/add', {
            'dst-address': '0.0.0.0/0', 'gateway': f'192.168.{i}.1', 'routing-table': 'main',
            'distance': '1', 'check-gateway': 'ping', 'comment': f'ECMP7-LAB-WAN{i}',
        }))
    if p['dhcp']:
        rows.extend([
            ('/ip/pool/add', {'name': 'ecmp7_lab_pool', 'ranges': '172.16.0.50-172.16.0.250'}),
            ('/ip/dhcp-server/network/add', {'address': '172.16.0.0/24', 'gateway': '172.16.0.1',
                'dns-server': '1.1.1.1,8.8.8.8', 'comment': 'ECMP7-LAB-DHCP'}),
            ('/ip/dhcp-server/add', {'name': 'ecmp7_lab_dhcp', 'interface': 'ether3',
                'address-pool': 'ecmp7_lab_pool', 'lease-time': '8h', 'disabled': 'no'}),
        ])
    return rows


def addresses_valid(tables):
    rows = tables['/ip/address']
    return (len(rows) == 4 and {row.get('interface'): row.get('address') for row in rows} == ADDRESSES
            and all(row.get('disabled', 'false') in ('false', 'no')
                    and row.get('dynamic', 'false') in ('false', 'no') for row in rows))


def connected_routes_valid(rows):
    expected = {(address.rsplit('.', 1)[0] + '.0/24', interface) for interface, address in ADDRESSES.items()}
    return (len(rows) == 4 and {(r.get('dst-address'), r.get('gateway')) for r in rows} == expected
            and all(r.get('dynamic') == 'true' and r.get('active') == 'true'
                    and r.get('distance') == '0' and r.get('routing-table') == 'main' for r in rows))


def precheck(snapshot, target, value):
    from shared.snapshot import Snapshot
    snapshot = Snapshot.model_validate(snapshot).model_dump()
    parameters(value)
    tables = snapshot['tables']
    if (snapshot['version'] != V7_LAB_VERSION or snapshot['identity'] != 'lab-router'
            or target['identity'] != 'lab-router' or target['management_interface'] != 'ether4'):
        raise ValueError('Destino fuera del laboratorio v7')
    interfaces = tables['/interface/ethernet']
    if (len(interfaces) != 4 or {r.get('default-name') for r in interfaces} != set(ADDRESSES)
            or any(r.get('name') != r.get('default-name') or r.get('disabled', 'false') not in ('false', 'no')
                   for r in interfaces)):
        raise ValueError('Interfaces distintas del laboratorio preparado')
    if not addresses_valid(tables) or not connected_routes_valid(tables['/ip/route']):
        raise ValueError('Se requieren cuatro direcciones y solo sus rutas conectadas')
    for table in ('/ip/firewall/nat', '/ip/firewall/mangle', '/ip/firewall/filter', '/ip/pool',
                  '/ip/dhcp-server', '/ip/dhcp-server/network', '/interface/bridge/port', '/routing/rule'):
        if tables[table]:
            raise ValueError('Configuracion existente; restaurar base preparada y revisar')
    if any(r.get('disabled') != 'true' for r in tables['/ip/dhcp-client']):
        raise ValueError('Deshabilitar clientes DHCP antes del ensayo')
    route_tables = tables['/routing/table']
    # In RouterOS 7.24.5, /routing/table/print can return the present FIB
    # switch as fib="" rather than a boolean. Accept that exact representation
    # only for the sole main table; an absent key or explicit false still fails.
    if (len(route_tables) != 1 or route_tables[0].get('name') != 'main'
            or route_tables[0].get('fib') not in ('true', '')):
        raise ValueError('Tabla main FIB esperada sin tablas adicionales')
    return digest(snapshot)


def equivalent(key, actual, expected):
    if key == 'disabled':
        return actual in ({'false', 'no'} if expected == 'no' else {'true', 'yes'})
    if key == 'lease-time' and expected == '8h':
        return actual in ('8h', '08:00:00', '8:00:00')
    return actual == expected


def verify(snapshot, operations):
    tables = snapshot['tables']
    checks = []
    for op in operations:
        table = op['command'].rsplit('/', 1)[0]
        matches = [r for r in tables[table] if all(equivalent(k, r.get(k, ''), v) for k, v in op['args'].items())]
        passed = len(matches) == 1 and matches[0].get('disabled', 'false') not in ('true', 'yes')
        if table == '/ip/route':
            passed = passed and matches[0].get('active') == 'true'
        checks.append({'line': op['line'], 'status': 'passed' if passed else 'failed'})
    def check(name, passed):
        checks.append({'test': name, 'status': 'passed' if passed else 'failed'})
    check('Management and lab addresses preserved', addresses_valid(tables))
    check('Interface names preserved', len(tables['/interface/ethernet']) == 4 and
          {r.get('name') for r in tables['/interface/ethernet']} == set(ADDRESSES) and
          all(r.get('name') == r.get('default-name') for r in tables['/interface/ethernet']))
    connected = [r for r in tables['/ip/route'] if r.get('dynamic') == 'true']
    check('Connected routes preserved', connected_routes_valid(connected))
    for table in {op['command'].rsplit('/', 1)[0] for op in operations}:
        expected_count = sum(op['command'].rsplit('/', 1)[0] == table for op in operations)
        check('Exact table count ' + table, len(tables[table]) == expected_count + (4 if table == '/ip/route' else 0))
    routes = [r for r in tables['/ip/route'] if r.get('dst-address') == '0.0.0.0/0']
    if len(routes) == 2 and all('ecmp' in r for r in routes):
        check('RouterOS ECMP flag', all(r['ecmp'] == 'true' for r in routes))
    else:
        checks.append({'test': 'RouterOS ECMP flag', 'status': 'not_performed'})
    checks.extend([{'test': 'WAN traffic', 'status': 'not_performed'}, {'test': 'LAN connectivity', 'status': 'not_performed'}])
    return {'outcome': 'configuration_failed' if any(c['status'] == 'failed' for c in checks)
            else 'configuration_with_warnings', 'checks': checks}

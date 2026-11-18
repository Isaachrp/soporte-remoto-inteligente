"""Read-only observations and deterministic recommendations from supported templates."""
from ipaddress import ip_interface
from shared.contracts import variant
from shared.ecmp import precheck


def recommend(snapshot, router_id, mode, lab_enabled):
    tables = snapshot['tables']
    addresses = tables['/ip/address']
    management = [r['interface'] for r in addresses
                  if r.get('address') == '10.255.255.1/24' and r.get('interface')]
    target = {'router_id': router_id, 'identity': snapshot['identity'],
              'management_interface': management[0] if len(management) == 1 else 'ether14'}
    p = {'tipo': 'ECMP', 'lineas': 2, 'lan': '172.16.0.1', 'dhcp': True,
         'vel1': '5M', 'vel2': '5M', 'gw1': '192.168.1.1', 'gw2': '192.168.2.1',
         'ip1': 2, 'ip2': 2}
    blockers = []
    # Reuse observed addresses on the prepared v7 topology. Never infer a gateway
    # from a local address: gateway values remain explicitly labelled assumptions.
    if snapshot['version'].startswith('7.'):
        for row in addresses:
            try:
                address = str(ip_interface(row['address']).ip)
            except (ValueError, KeyError):
                continue
            if row.get('interface') == 'ether3':
                p['lan'] = address
            for index in (1, 2):
                if row.get('interface') == f'ether{index}':
                    p[f'ip{index}'] = int(address.split('.')[-1]) if '.' in address else 0
    if len(management) != 1:
        blockers.append('No se identifica de forma única el puerto administrativo del laboratorio (10.255.255.1/24).')
    try:
        selected = variant(snapshot['version'], mode, lab_enabled)
        precheck(snapshot, target, p, lab_enabled)
    except ValueError as exc:
        selected = None
        blockers.append(str(exc))
    return {'available': not blockers, 'procedure': 'Balanceo ECMP de dos enlaces de igual costo',
            'variant': selected, 'target': target, 'parameters': p, 'blockers': blockers,
            'observed': {'identity': snapshot['identity'], 'version': snapshot['version'],
                         'interfaces': tables['/interface/ethernet'], 'addresses': addresses,
                         'routes': tables['/ip/route'],
                         'counts': {name: len(rows) for name, rows in tables.items()}},
            'assumptions': ['Gateways propuestos por la plantilla de laboratorio: 192.168.1.1 y 192.168.2.1. No se deducen de las rutas conectadas.',
                            'Dos enlaces de igual costo; 5M es un parámetro de la plantilla, no una velocidad medida.',
                            'Se propone habilitar DHCP para clientes en 172.16.0.0/24.'],
            'limitations': ['La lectura de configuración no comprueba Internet, tráfico WAN ni conectividad del cliente.',
                            'Solo ECMP está integrado. PCC, Hotspot y otras topologías requieren nuevas variantes validadas.']}

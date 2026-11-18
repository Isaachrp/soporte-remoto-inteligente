"""Forms for the unchanged PHP generators. No RouterOS commands are authored here."""
import re
from ipaddress import IPv4Address, IPv4Network, IPv4Interface

LABELS = {
    'ECMP': 'Balanceo ECMP', 'ECMPr': 'ECMP recursivo', 'PCC': 'Balanceo PCC',
    'PCCr': 'PCC recursivo V6', 'PCCrV7': 'PCC recursivo V7',
    'PCC-DYNAMIC': 'PCC dinámico', 'PBr': 'PBR recursivo V6',
    'PBrV7': 'PBR recursivo V7', 'NTH': 'Balanceo NTH', 'NTHr': 'NTH recursivo',
    'Hotspot': 'Hotspot', 'Tickets': 'Tickets Hotspot', 'Firewall': 'Firewall',
    'Residenciales': 'Clientes residenciales', 'OpenVPN': 'Cliente OpenVPN',
}
BALANCE = set(list(LABELS)[:10])
V7_ONLY = {'PCCrV7', 'PBrV7', 'PCC-DYNAMIC'}
V6_ONLY = BALANCE - V7_ONLY
PLANS = ['Plan1Hora', 'Plan2Horas', 'Plan4Horas', 'Plan1Dia', 'Plan1Semana', 'Plan15Dias', 'Plan30Dias']


def field(name, label, kind='text', default='', **extra):
    return dict(name=name, label=label, kind=kind, default=default, **extra)


def fields(procedure, snapshot=None, lines=2):
    if procedure not in LABELS:
        raise ValueError('Configuración desconocida.')
    tables = (snapshot or {}).get('tables', {})
    addresses = {}
    for row in tables.get('/ip/address', []):
        try:
            addresses[row.get('interface')] = str(IPv4Interface(row.get('address', '')).ip)
        except ValueError:
            continue
    lan = addresses.get(f'ether{lines + 1}', '')
    if procedure in BALANCE:
        result = [field('lineas', 'Enlaces WAN', 'number', lines, minimum=2, maximum=12),
                  field('lan', 'IP de la LAN', 'ipv4', lan), field('dhcp', 'Habilitar DHCP', 'checkbox', False)]
        gateways = {r['gateway'] for r in tables.get('/ip/route', [])
                    if r.get('dst-address') == '0.0.0.0/0' and r.get('gateway')}
        for i in range(1, lines + 1):
            ip = addresses.get(f'ether{i}', '')
            gateway = next((g for g in sorted(gateways) if g and ip and g.rsplit('.', 1)[0] == ip.rsplit('.', 1)[0]), '')
            result += [field(f'gw{i}', f'WAN {i} · gateway', 'ipv4', gateway),
                       field(f'ip{i}', f'WAN {i} · último octeto IP', 'number', int(ip.split('.')[-1]) if ip else 2, minimum=2, maximum=253),
                       field(f'vel{i}', f'WAN {i} · velocidad', 'speed', '5M')]
        return result
    if procedure == 'Firewall':
        return [field('wan', 'Interfaz WAN'), field('lan', 'Redes LAN autorizadas (una por línea)', 'networks'),
                field('puertos_tcp', 'Puertos TCP permitidos', 'ports', '8291,8728'),
                field('puertos_udp', 'Puertos UDP permitidos', 'ports', '', optional=True)]
    if procedure == 'Residenciales':
        return [field('ip_cliente', 'IP del cliente', 'ipv4'), field('vel_subida', 'Subida', 'speed', '1M'),
                field('vel_bajada', 'Bajada', 'speed', '5M'), field('fecha_inicio', 'Inicio', 'date'),
                field('fecha_vencimiento', 'Vencimiento', 'date'), field('perfil', 'Perfil'),
                field('contacto', 'Contacto', optional=True)]
    if procedure == 'Tickets':
        return [field('numero', 'Cantidad', 'number', 20, minimum=1, maximum=500),
                field('prefijo', 'Prefijo', optional=True),
                field('long_usuario', 'Longitud de usuario', 'number', 6, minimum=4, maximum=16),
                field('long_password', 'Longitud de contraseña', 'number', 8, minimum=4, maximum=24),
                field('perfil', 'Perfil existente', 'text', 'default'), field('titulo', 'Título', 'text', 'Wifi'),
                field('contacto', 'Contacto', optional=True), field('igual', 'Usuario y contraseña iguales', 'checkbox', False)]
    if procedure == 'Hotspot':
        result = [field('lan', 'IP de la LAN (ether2)', 'ipv4', addresses.get('ether2', '')),
                  field('dhcp', 'Habilitar DHCP', 'checkbox', True)]
        for plan in PLANS:
            result += [field(plan, plan.replace('Plan', 'Plan '), 'checkbox', False),
                       field('v' + plan, 'Velocidad ' + plan, 'speed', '1M')]
        return result
    return [field('client', 'Nombre del cliente'), field('password', 'Contraseña OVPN', 'password'),
            field('ip', 'IP pública del servidor', 'ipv4'), field('export_pass', 'Contraseña del certificado', 'password')]


def validate_parameters(procedure, values):
    if not isinstance(values, dict):
        raise ValueError('Parámetros inválidos.')
    lines = values.get('lineas', 2)
    if type(lines) is not int or not 2 <= lines <= 12:
        raise ValueError('Selecciona entre 2 y 12 enlaces.')
    specs = fields(procedure, lines=lines)
    if set(values) != {f['name'] for f in specs}:
        raise ValueError('Completa los parámetros de la configuración seleccionada.')
    for spec in specs:
        value, kind = values[spec['name']], spec['kind']
        valid = True
        if kind == 'checkbox':
            valid = type(value) is bool
        elif kind == 'number':
            valid = type(value) is int and spec['minimum'] <= value <= spec['maximum']
        else:
            valid = isinstance(value, str) and len(value) <= 500
            if valid and value == '' and spec.get('optional'):
                continue
            if valid:
                try:
                    if kind == 'ipv4':
                        IPv4Address(value)
                    elif kind == 'networks':
                        valid = bool(value.strip()) and len(value.splitlines()) <= 20
                        for item in value.splitlines():
                            IPv4Network(item, strict=False)
                    elif kind == 'ports':
                        valid = bool(re.fullmatch(r'\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*', value))
                        valid = valid and all(1 <= int(n) <= 65535 for n in re.split('[,-]', value))
                    elif kind == 'speed':
                        valid = bool(re.fullmatch(r'[1-9]\d{0,3}[kM]', value))
                    elif kind == 'date':
                        from datetime import date
                        date.fromisoformat(value)
                    else:
                        # PHP concatenates these values into RouterOS source. Reject syntax injection.
                        valid = bool(re.fullmatch(r'[\w .@+!%=-]{1,100}', value, re.ASCII))
                        if spec['name'] in ('perfil', 'prefijo', 'wan', 'client', 'password', 'export_pass'):
                            valid = valid and ' ' not in value
                except ValueError:
                    valid = False
        if not valid:
            raise ValueError('Revisa el campo: ' + spec['label'])
    if procedure in BALANCE or procedure == 'Hotspot':
        if not re.fullmatch(r'172\.16\.\d{1,3}\.1', values['lan']):
            raise ValueError('La plantilla PHP requiere LAN 172.16.x.1.')
    if procedure in BALANCE:
        for i in range(1, lines + 1):
            if not re.fullmatch(r'192\.168\.\d{1,3}\.(1|254)', values[f'gw{i}']):
                raise ValueError('La plantilla PHP requiere gateways 192.168.x.1 o 192.168.x.254.')
    return dict(values)


def catalog(snapshot):
    major = snapshot['version'].split('.')[0]
    rows = []
    for id, label in LABELS.items():
        note = ''
        if major not in ('6', '7'):
            note = 'Se requiere un diagnóstico RouterOS 6 o 7.'
        elif id in V7_ONLY and major != '7':
            note = 'La plantilla requiere RouterOS 7.'
        elif id in V6_ONLY and major != '6':
            note = 'Plantilla original V6; usa una variante V7 para este router.'
        rows.append({'id': id, 'label': label, 'note': note, 'fields': fields(id, snapshot)})
    return rows

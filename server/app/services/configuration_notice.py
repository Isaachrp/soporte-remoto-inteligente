"""Explain existing ECMP configuration without changing compatibility rules."""
from shared.v7 import equivalent, expected_operations


def configuration_notice(snapshot, parameters):
    if not snapshot['version'].startswith('7.'):
        return None
    try:
        operations = expected_operations(parameters)
    except ValueError:
        return None
    tables = snapshot['tables']
    present = []
    related = False
    for command, args in operations:
        rows = tables[command.rsplit('/', 1)[0]]
        matches = [row for row in rows if all(
            equivalent(key, row.get(key, ''), value)
            for key, value in args.items() if key != 'comment')
            and row.get('disabled', 'false') not in ('true', 'yes')]
        present.append(len(matches) == 1)
        related |= bool(matches) or any(
            (args.get('comment') and row.get('comment') == args['comment'])
            or (args.get('name') and row.get('name') == args['name']) for row in rows)
    if not related:
        return None
    complete = all(present)
    return {
        'title': ('La configuración ECMP que se quiere aplicar ya está hecha.' if complete else
                  'Ya existe parte de la configuración ECMP que se quiere aplicar.'),
        'message': ('El diagnóstico contiene las rutas, NAT y DHCP previstos por la plantilla.' if complete else
                    'Se encontraron elementos previos de ECMP, pero no todos coinciden con la plantilla.')
                   + ' Preparar propuesta permanece deshabilitado para evitar duplicar o mezclar configuraciones. '
                     'El diagnóstico no confirma que Internet ni el balanceo funcionen.',
        'actions': [
            'Si deseas conservar la configuración, revisa las rutas, NAT y DHCP en WinBox y comprueba la conectividad de la LAN y de ambos enlaces WAN.',
            'Si la configuración está incompleta o falla, revisa sus diferencias con un técnico antes de modificarla; este procedimiento solo prepara ECMP desde la base del laboratorio.',
            'Para repetir el ensayo, guarda un respaldo y restaura la base preparada del laboratorio conservando el acceso administrativo. Después genera y carga un diagnóstico nuevo.',
        ],
    }

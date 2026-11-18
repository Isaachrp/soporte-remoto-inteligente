"""Central-only continuation: preserve matching v7 entries, never replace rules."""
from copy import deepcopy

from shared.contracts import digest, variant, V7_LAB_VARIANT
from shared.v7 import equivalent, expected_operations, precheck


def reconcile(snapshot, target, parameters, mode, lab_enabled):
    if variant(snapshot['version'], mode, lab_enabled) != V7_LAB_VARIANT:
        raise ValueError('Continuar con configuración existente solo admite el laboratorio v7.')
    base = deepcopy(snapshot)
    missing = []
    for index, (command, args) in enumerate(expected_operations(parameters)):
        rows = base['tables'][command.rsplit('/', 1)[0]]
        matches = [row for row in rows if all(
            equivalent(key, row.get(key, ''), value)
            for key, value in args.items() if key != 'comment')
            and row.get('disabled', 'false') not in ('true', 'yes')]
        if len(matches) > 1:
            raise ValueError('Hay elementos ECMP duplicados. Revise el router antes de continuar.')
        if matches:
            rows.remove(matches[0])
        else:
            missing.append(index)
    # Any conflicting/unknown entry remains and fails the original strict gate.
    try:
        precheck(base, target, parameters)
    except ValueError as exc:
        raise ValueError('No se puede conservar y completar esta configuración: ' + str(exc)) from None
    return missing


def check_existing(snapshot, target, parameters, mode, lab_enabled):
    reconcile(snapshot, target, parameters, mode, lab_enabled)
    return digest(snapshot)


def remaining_executable(full, snapshot, target, parameters, mode, lab_enabled):
    indexes = reconcile(snapshot, target, parameters, mode, lab_enabled)
    operations = [deepcopy(full['operations'][i]) for i in indexes]
    return {**full, 'operations': operations, 'operations_hash': digest(operations)}


def verification_operations(full):
    operations = deepcopy(full['operations'])
    for op in operations:
        op['args'].pop('comment', None)
    return operations

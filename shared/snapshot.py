from pydantic import Field, model_validator
from shared.contracts import Strict
from shared.ecmp import FIELDS, TABLES

READ_FIELDS = {table: set().union(*(fields for path, fields in FIELDS.items() if path.rsplit('/',1)[0] == table)) for table in TABLES}
READ_FIELDS['/interface/ethernet'] |= {'.id','default-name'}
READ_FIELDS['/ip/route'] |= {'active'}
READ_FIELDS['/interface/bridge/port'] = {'interface','bridge'}
V7_READ_FIELDS = {table: fields.copy() for table, fields in READ_FIELDS.items()}
from shared.v7 import FIELDS as V7_FIELDS
for path, fields in V7_FIELDS.items():
    V7_READ_FIELDS.setdefault(path.rsplit('/', 1)[0], set()).update(fields)
V7_READ_FIELDS['/interface/ethernet'] |= {'disabled'}
V7_READ_FIELDS['/ip/address'] |= {'disabled', 'dynamic'}
V7_READ_FIELDS['/ip/route'] |= {'dynamic', 'ecmp'}
for table in ('/ip/firewall/nat', '/ip/pool', '/ip/dhcp-server/network', '/ip/route'):
    V7_READ_FIELDS[table].add('disabled')
V7_READ_FIELDS['/ip/firewall/filter'] = {'chain', 'action', 'disabled', 'comment'}
V7_READ_FIELDS['/ip/dhcp-client'] = {'name', 'interface', 'disabled', 'add-default-route'}
V7_READ_FIELDS['/routing/rule'] = {'action', 'table', 'src-address', 'dst-address', 'disabled'}
V7_READ_FIELDS['/routing/table'] = {'name', 'fib'}


def fields_for(version):
    return V7_READ_FIELDS if version.startswith('7.') else READ_FIELDS

class Snapshot(Strict):
    identity: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,64}$')
    version: str = Field(pattern=r'^[0-9][0-9.a-zA-Z ()_-]{0,63}$')
    tables: dict[str, list[dict[str,str]]]

    @model_validator(mode='after')
    def closed_tables(self):
        allowed = fields_for(self.version)
        if set(self.tables) != set(allowed):
            raise ValueError('Snapshot incompleto o no permitido')
        for table, rows in self.tables.items():
            if len(rows) > 512:
                raise ValueError('Demasiadas filas')
            for row in rows:
                if set(row) - allowed[table] or any(len(v)>100000 for v in row.values()):
                    raise ValueError('Campos no permitidos')
        return self

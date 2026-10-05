from pydantic import Field, model_validator
from shared.contracts import Strict
from shared.ecmp import FIELDS, TABLES

READ_FIELDS = {table: set().union(*(fields for path, fields in FIELDS.items() if path.rsplit('/',1)[0] == table)) for table in TABLES}
READ_FIELDS['/interface/ethernet'] |= {'.id','default-name'}
READ_FIELDS['/ip/route'] |= {'active'}
READ_FIELDS['/interface/bridge/port'] = {'interface','bridge'}

class Snapshot(Strict):
    identity: str = Field(pattern=r'^[a-zA-Z0-9_-]{1,64}$')
    version: str = Field(pattern=r'^[0-9][0-9.a-zA-Z ()_-]{0,63}$')
    tables: dict[str, list[dict[str,str]]]

    @model_validator(mode='after')
    def closed_tables(self):
        if set(self.tables) != set(READ_FIELDS):
            raise ValueError('Snapshot incompleto o no permitido')
        for table, rows in self.tables.items():
            if len(rows) > 512:
                raise ValueError('Demasiadas filas')
            for row in rows:
                if set(row) - READ_FIELDS[table] or any(len(v)>100000 for v in row.values()):
                    raise ValueError('Campos no permitidos')
        return self

import json
import sqlite3
import threading
from contextlib import contextmanager

class Store:
    """One transaction commits workflow snapshot, tasks and audit together."""
    def __init__(self, path):
        self.path = path
        self.lock = threading.RLock()
        with self.transaction() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS objects(kind TEXT, id TEXT, body TEXT NOT NULL, PRIMARY KEY(kind,id));
                CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY, request_id TEXT, at REAL, actor TEXT, event TEXT);
            ''')

    @contextmanager
    def transaction(self):
        with self.lock:
            db = sqlite3.connect(self.path, timeout=30)
            db.row_factory = sqlite3.Row
            try:
                db.execute('BEGIN IMMEDIATE')
                yield db
                db.commit()
            except BaseException:
                db.rollback()
                raise
            finally:
                db.close()

    @staticmethod
    def get(db, kind, id):
        row = db.execute('SELECT body FROM objects WHERE kind=? AND id=?', (kind,id)).fetchone()
        return json.loads(row['body']) if row else None

    @staticmethod
    def put(db, kind, id, body):
        db.execute('INSERT INTO objects VALUES(?,?,?) ON CONFLICT(kind,id) DO UPDATE SET body=excluded.body',
                   (kind,id,json.dumps(body)))

    @staticmethod
    def all(db, kind):
        return [json.loads(r['body']) for r in db.execute('SELECT body FROM objects WHERE kind=?',(kind,))]

"""infrastructure / database.py: extracted from the real v0.3 pilot."""
from __future__ import annotations
from contextlib import contextmanager
from pathlib import Path
import sqlite3


class Database:
    """Owns SQLite lifecycle and transactions; modules never commit independently."""

    def __init__(self, data_dir):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.chmod(0o700)
        self.db_path = self.data_dir / 'school.sqlite3'
        with self.connection() as db:
            version = db.execute('PRAGMA user_version').fetchone()[0]
            if version == 0:
                schema = Path(__file__).with_name('migrations') / '003_pilot_baseline.sql'
                db.executescript(schema.read_text('utf-8'))
                version = 3
            if version == 3:
                if db.execute('SELECT COUNT(*) FROM workspaces').fetchone()[0] > 1:
                    raise RuntimeError('This edition requires one isolated school per database.')
                # A v3 installation is backed up before any additive migration.
                import secrets
                backup_path = self.data_dir / ('school.pre-v4.' + secrets.token_hex(6) + '.sqlite3')
                backup_db = sqlite3.connect(backup_path)
                try:
                    db.backup(backup_db)
                finally:
                    backup_db.close()
                backup_path.chmod(0o600)
                migration = Path(__file__).with_name('migrations') / '004_foundation.sql'
                db.executescript(migration.read_text('utf-8'))
            elif version != 4:
                raise RuntimeError('Unsupported database version. Never overwrite an existing database.')
            db.execute('PRAGMA journal_mode=WAL')
        self.db_path.chmod(0o600)

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.db_path, timeout=15, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute('PRAGMA foreign_keys=ON')
        db.execute('PRAGMA busy_timeout=15000')
        db.execute('PRAGMA synchronous=FULL')
        try:
            yield db
        finally:
            db.close()

    @contextmanager
    def snapshot(self):
        with self.connection() as db:
            db.execute('BEGIN')
            try:
                yield db
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK')
                raise

    @contextmanager
    def transaction(self):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            try:
                yield db
                db.execute('COMMIT')
            except BaseException:
                db.execute('ROLLBACK')
                raise

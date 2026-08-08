"""SQLite database connection and schema management.

Each project owns an isolated SQLite database (WAL enabled). The schema is
created via a migration runner so structure changes are explicit and
reversible. Migrations are plain SQL files applied in version order.
"""
from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from backend.logging import get_logger

log = get_logger("database")

SCHEMA_VERSION_TABLE = "schema_migrations"
MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def get_project_db_path(project_dir: str | Path) -> Path:
    """Return the SQLite database path for a project directory."""
    return Path(project_dir) / "database.sqlite"


class Database:
    """Thin wrapper around a per-project SQLite connection.

    Connections are thread-local because SQLite objects must not be shared
    across threads. WAL mode improves concurrent read performance.
    """

    def __init__(self, db_path: str | Path, wal_mode: bool = True) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.wal_mode = wal_mode
        self._local = threading.local()
        self._apply_pragmas()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(
            self.db_path,
            timeout=30.0,
            isolation_level=None,  # autocommit; we manage transactions explicitly
            check_same_thread=False,
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        if self.wal_mode:
            conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.execute("PRAGMA temp_store = MEMORY;")
        return conn

    @property
    def connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._local.conn = self._connect()
        return self._local.conn

    def _apply_pragmas(self) -> None:
        # Ensure DB file exists with WAL before thread-local connections.
        conn = self._connect()
        try:
            conn.close()
        except Exception:
            pass

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Context manager yielding a connection inside a transaction."""
        conn = self.connection
        conn.execute("BEGIN;")
        try:
            yield conn
            conn.execute("COMMIT;")
        except Exception:
            try:
                conn.execute("ROLLBACK;")
            except sqlite3.OperationalError:
                # Transaction may already have been ended (e.g. by executescript).
                pass
            raise

    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return self.connection.execute(sql, params)

    def executemany(self, sql: str, params_seq) -> sqlite3.Cursor:
        return self.connection.executemany(sql, params_seq)

    def query_all(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return self.execute(sql, params).fetchall()

    def query_one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        return self.execute(sql, params).fetchone()

    def close(self) -> None:
        if hasattr(self._local, "conn") and self._local.conn is not None:
            self._local.conn.close()
            self._local.conn = None

    # ---- Migrations -----------------------------------------------------
    def run_migrations(self) -> int:
        """Apply pending SQL migrations. Returns the count applied."""
        self.execute(
            f"""CREATE TABLE IF NOT EXISTS {SCHEMA_VERSION_TABLE} (
                version TEXT PRIMARY KEY,
                applied_at TEXT NOT NULL
            );"""
        )
        applied = {
            row["version"]
            for row in self.query_all(f"SELECT version FROM {SCHEMA_VERSION_TABLE};")
        }
        migrations = sorted(
            p for p in MIGRATIONS_DIR.glob("*.sql") if p.stem not in applied
        )
        count = 0
        for path in migrations:
            version = path.stem
            sql = path.read_text(encoding="utf-8")
            log.info("applying migration", extra={"action": "migrate", "status": "start", "version": version})
            conn = self.connection
            # executescript() implicitly commits any active transaction, so we
            # run it directly then insert the version record in the same
            # connection (autocommit mode handles persistence).
            conn.executescript(sql)
            conn.execute(
                f"INSERT INTO {SCHEMA_VERSION_TABLE} (version, applied_at) VALUES (?, ?);",
                (version, _utcnow_iso()),
            )
            conn.commit()
            count += 1
            log.info("migration applied", extra={"action": "migrate", "status": "done", "version": version})
        if count == 0:
            log.info("migrations up to date", extra={"action": "migrate", "status": "noop"})
        return count


def _utcnow_iso() -> str:
    from datetime import datetime, timezone
    return datetime.now(timezone.utc).isoformat()

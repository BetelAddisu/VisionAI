"""Database layer: SQLite connection, schema, migrations and repositories.

Only this package writes to SQLite. All other modules use repository APIs.
"""
from backend.database.connection import Database, get_project_db_path
from backend.database.repository import Repository

__all__ = ["Database", "Repository", "get_project_db_path"]

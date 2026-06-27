"""
SQLite bağlantı yönetimi.

- Row factory: sqlite3.Row (dict-like erişim)
- PRAGMA foreign_keys = ON her bağlantıda
- init_db() → schema.sql'i çalıştırır
- get_db() → FastAPI Depends uyumlu dependency
"""

import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator

from app.config import settings

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema.sql"


def _connect() -> sqlite3.Connection:
    """Yeni bir SQLite bağlantısı oluşturur."""
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def get_db_context() -> Generator[sqlite3.Connection, None, None]:
    """Context manager: bağlantıyı açar, işlem bitince kapatır."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db() -> Generator[sqlite3.Connection, None, None]:
    """FastAPI Depends uyumlu dependency."""
    conn = _connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """schema.sql dosyasını çalıştırarak tabloları oluşturur."""
    if not SCHEMA_PATH.exists():
        raise FileNotFoundError(f"Schema dosyası bulunamadı: {SCHEMA_PATH}")

    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = _connect()
    try:
        conn.executescript(schema_sql)
        conn.commit()
    finally:
        conn.close()

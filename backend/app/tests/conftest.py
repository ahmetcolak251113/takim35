"""
Test fixture'ları — Dijital Gardrop Gizlilik / AI Export Testleri
=================================================================
Her test fonksiyonu için temiz bir in-memory SQLite veritabanı oluşturur,
schema.sql ile tabloları kurar ve test verisini yükler.
"""

import sqlite3
from pathlib import Path

import pytest

# ── Yol sabitleri ───────────────────────────────────────────────────────
_BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
SCHEMA_PATH = _BACKEND_DIR / "schema.sql"
MOCK_DATA_PATH = _BACKEND_DIR / "mock_data.sql"

# ── Test kullanıcıları ──────────────────────────────────────────────────
USER_A = "user-a-0001"  # Post sahibi (elif_style)
USER_B = "user-b-0002"  # A'yı takip eden (ahmet_trendy)
USER_C = "user-c-0003"  # A'yı takip etmeyen (zeynep_chic)


def _init_db() -> sqlite3.Connection:
    """
    In-memory SQLite DB oluştur → schema + mock data yükle.
    SQLite'ın PRAGMA komutları executescript içinde sorun çıkartabilir,
    bu yüzden PRAGMA'ları ayrıca çalıştırıyoruz.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row

    # Schema
    schema_sql = SCHEMA_PATH.read_text(encoding="utf-8")
    conn.executescript(schema_sql)

    # Mock data
    mock_sql = MOCK_DATA_PATH.read_text(encoding="utf-8")
    conn.executescript(mock_sql)

    # foreign_keys tekrar aç (executescript sonrası sıfırlanabilir)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ── Pytest fixture'ları ─────────────────────────────────────────────────

@pytest.fixture()
def db():
    """Her test için temiz bir in-memory SQLite bağlantısı."""
    conn = _init_db()
    yield conn
    conn.close()


@pytest.fixture()
def test_users():
    """Test kullanıcı ID'leri."""
    return {
        "A": USER_A,
        "B": USER_B,
        "C": USER_C,
    }


@pytest.fixture()
def test_posts():
    """
    Mock data'daki 6 post'un beklenen özellikleri.
    Her senaryoda doğrudan kullanılabilir.
    """
    return {
        "post-0001": {"visibility": "public",    "consent": 1, "owner": USER_A},
        "post-0002": {"visibility": "followers",  "consent": 1, "owner": USER_A},
        "post-0003": {"visibility": "private",    "consent": 0, "owner": USER_A},
        "post-0004": {"visibility": "public",     "consent": 0, "owner": USER_A},
        "post-0005": {"visibility": "public",     "consent": 1, "owner": USER_B},
        "post-0006": {"visibility": "followers",  "consent": 0, "owner": USER_A},
    }

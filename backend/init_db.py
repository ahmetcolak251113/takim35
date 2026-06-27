"""
Dijital Gardrop — Veritabanı başlatma scripti.

Kullanım:
  python init_db.py          # Sadece schema oluştur
  python init_db.py --mock   # Schema + mock data yükle
"""

import argparse
import sqlite3
import sys
from pathlib import Path

# Proje kök dizini
BASE_DIR = Path(__file__).resolve().parent
SCHEMA_PATH = BASE_DIR / "schema.sql"
MOCK_DATA_PATH = BASE_DIR / "mock_data.sql"

# .env dosyasından DATABASE_PATH oku (varsa)
DB_PATH = BASE_DIR / "dijital_gardrop.db"

try:
    from dotenv import load_dotenv
    import os

    load_dotenv(BASE_DIR / ".env")
    env_db = os.getenv("DATABASE_PATH")
    if env_db:
        DB_PATH = Path(env_db)
except ImportError:
    pass


def run_sql_file(conn: sqlite3.Connection, filepath: Path, label: str) -> None:
    """Bir SQL dosyasını okuyup çalıştırır."""
    if not filepath.exists():
        print(f"  ✗ {label} dosyası bulunamadı: {filepath}")
        sys.exit(1)

    sql = filepath.read_text(encoding="utf-8")
    conn.executescript(sql)
    print(f"  ✓ {label} başarıyla çalıştırıldı")


def main():
    parser = argparse.ArgumentParser(description="Dijital Gardrop veritabanı başlatma")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Mock data'yı da yükle",
    )
    args = parser.parse_args()

    print(f"Veritabanı yolu: {DB_PATH}")
    print("─" * 40)

    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA foreign_keys = ON")

    try:
        # Schema oluştur
        print("Schema oluşturuluyor...")
        run_sql_file(conn, SCHEMA_PATH, "schema.sql")

        # Mock data (opsiyonel)
        if args.mock:
            print("\nMock data yükleniyor...")
            run_sql_file(conn, MOCK_DATA_PATH, "mock_data.sql")

        conn.commit()
        print("\n" + "─" * 40)
        print("✓ Veritabanı başarıyla oluşturuldu!")

        # Tablo kontrolü
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
        print(f"\nOluşturulan tablolar ({len(tables)}):")
        for t in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM [{t[0]}]").fetchone()[0]
            print(f"  • {t[0]}: {count} kayıt")

    except Exception as e:
        print(f"\n✗ Hata: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()

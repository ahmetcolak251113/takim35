"""
AI Eğitim Verisi Export Batch Job
=================================
Günde 1 kez çalışan batch/cron job.
Standalone: python -m app.services.ai_export
"""

import json
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Proje kök dizini (backend/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "dijital_gardrop.db"
SCHEMA_PATH = BASE_DIR / "schema.sql"
EXPORTS_DIR = BASE_DIR / "exports"

# ── SQL: Tüm filtreleme veritabanı seviyesinde ──────────────────────────
EXPORT_QUERY = """\
SELECT p.post_id,
       p.image_url,
       p.created_at,
       poi.item_id,
       poi.category,
       poi.image_url AS item_image_url
FROM   posts p
LEFT JOIN post_outfit_items poi ON p.post_id = poi.post_id
WHERE  p.ai_training_consent = 1
  AND  p.visibility != 'private'
  AND  p.post_id NOT IN (SELECT post_id FROM training_data_export)
ORDER BY p.created_at ASC
"""

INSERT_EXPORT = """\
INSERT INTO training_data_export (export_id, post_id, export_data, exported_at)
VALUES (?, ?, ?, ?)
"""


def _get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Veritabanı bağlantısı oluşturur."""
    path = str(db_path or DB_PATH)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def _build_post_records(rows: list[sqlite3.Row]) -> list[dict]:
    """
    Ham SQL satırlarını post bazında gruplayarak JSON sözleşmesine
    uygun kayıtlara dönüştürür.
    """
    posts: dict[str, dict] = {}

    for row in rows:
        pid = row["post_id"]
        if pid not in posts:
            posts[pid] = {
                "post_id": pid,
                "image_url": row["image_url"],
                "outfit_items": [],
                "created_at": row["created_at"],
            }
        # LEFT JOIN sonucu item_id NULL olabilir
        if row["item_id"] is not None:
            posts[pid]["outfit_items"].append(
                {
                    "item_id": row["item_id"],
                    "category": row["category"],
                    "image_url": row["item_image_url"],
                }
            )

    return list(posts.values())


def run_export(
    conn: Optional[sqlite3.Connection] = None,
    exports_dir: Optional[Path] = None,
) -> list[dict]:
    """
    Ana export fonksiyonu.

    1. SQL ile consent=true & visibility!=private & henüz export edilmemiş
       postları çeker.
    2. Her postu JSON sözleşmesine dönüştürür.
    3. training_data_export tablosuna kaydeder.
    4. exports/ dizinine JSON dosyası yazar.

    Returns:
        Export edilen post kayıtlarının listesi.
    """
    own_conn = conn is None
    if own_conn:
        conn = _get_connection()

    target_dir = exports_dir or EXPORTS_DIR

    try:
        cursor = conn.execute(EXPORT_QUERY)
        rows = cursor.fetchall()

        if not rows:
            logger.info("Export edilecek yeni post bulunamadı.")
            return []

        records = _build_post_records(rows)
        now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")

        # ── training_data_export tablosuna yaz ──────────────────────
        for rec in records:
            export_id = str(uuid.uuid4())
            conn.execute(
                INSERT_EXPORT,
                (export_id, rec["post_id"], json.dumps(rec, ensure_ascii=False), now_iso),
            )
        conn.commit()

        # ── JSON dosyasına yaz ──────────────────────────────────────
        target_dir.mkdir(parents=True, exist_ok=True)
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        file_path = target_dir / f"training_export_{today_str}.json"
        with open(file_path, "w", encoding="utf-8") as fp:
            json.dump(records, fp, ensure_ascii=False, indent=2)

        logger.info(
            "Export tamamlandı: %d post işlendi → %s", len(records), file_path
        )
        return records

    except Exception:
        logger.exception("Export sırasında hata oluştu.")
        raise
    finally:
        if own_conn:
            conn.close()


# ── Standalone çalıştırma ───────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    result = run_export()
    print(f"Toplam {len(result)} post export edildi.")

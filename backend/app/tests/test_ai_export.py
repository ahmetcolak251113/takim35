"""
AI Export Testleri
==================
ai_export.run_export() fonksiyonunun doğruluğunu test eder.

- consent=false → export'a GİRMEZ
- visibility=private (consent=true bile olsa) → export'a GİRMEZ
- consent=true + visibility=public → export'a GİRER
- consent=true + visibility=followers → export'a GİRER
- İdempotency: aynı post ikinci kez export EDİLMEZ
- JSON format sözleşmesi doğrulaması
"""

import json
from pathlib import Path

from .conftest import USER_A, USER_B

# ai_export modülünü import et
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from app.services.ai_export import run_export


class TestAIExportFiltering:
    """Export filtreleme testleri: consent + visibility kontrolleri."""

    def test_consent_false_not_exported(self, db, tmp_path):
        """consent=false olan post (post-0004) export'a GİRMEMELİ."""
        records = run_export(conn=db, exports_dir=tmp_path)
        exported_ids = {r["post_id"] for r in records}
        # post-0004: public, consent=0
        assert "post-0004" not in exported_ids
        # post-0003: private, consent=0
        assert "post-0003" not in exported_ids
        # post-0006: followers, consent=0
        assert "post-0006" not in exported_ids

    def test_private_visibility_not_exported(self, db, tmp_path):
        """
        visibility=private post, consent=true olsa bile export'a GİRMEMELİ.
        Test içinde private+consent=true post oluşturup kontrol ediyoruz.
        """
        db.execute(
            "INSERT INTO posts (post_id, user_id, image_url, visibility, ai_training_consent) "
            "VALUES (?, ?, ?, 'private', 1)",
            ("post-priv-ai", USER_A, "https://example.com/posts/priv.jpg"),
        )
        db.commit()

        records = run_export(conn=db, exports_dir=tmp_path)
        exported_ids = {r["post_id"] for r in records}
        assert "post-priv-ai" not in exported_ids

    def test_public_consent_true_exported(self, db, tmp_path):
        """consent=true + visibility=public (post-0001) export'a GİRMELİ."""
        records = run_export(conn=db, exports_dir=tmp_path)
        exported_ids = {r["post_id"] for r in records}
        assert "post-0001" in exported_ids

    def test_followers_consent_true_exported(self, db, tmp_path):
        """consent=true + visibility=followers (post-0002) export'a GİRMELİ."""
        records = run_export(conn=db, exports_dir=tmp_path)
        exported_ids = {r["post_id"] for r in records}
        assert "post-0002" in exported_ids


class TestAIExportIdempotency:
    """Aynı post'un ikinci kez export EDİLMEMESİ."""

    def test_double_export_no_duplicates(self, db, tmp_path):
        """run_export iki kez çağrılınca aynı postlar tekrar export edilmemeli."""
        first_run = run_export(conn=db, exports_dir=tmp_path)
        assert len(first_run) > 0, "İlk çalıştırmada en az 1 post export edilmeli"

        first_ids = {r["post_id"] for r in first_run}

        second_run = run_export(conn=db, exports_dir=tmp_path)
        second_ids = {r["post_id"] for r in second_run}

        # İkinci çalıştırmada ilk çalıştırmadaki postlar tekrar gelmemeli
        assert first_ids.isdisjoint(second_ids), (
            f"İkinci export'ta tekrar eden postlar var: {first_ids & second_ids}"
        )

    def test_second_run_returns_empty(self, db, tmp_path):
        """
        Tüm uygun postlar ilk seferde export edildiyse
        ikinci çalıştırma boş dönmeli.
        """
        run_export(conn=db, exports_dir=tmp_path)
        second_run = run_export(conn=db, exports_dir=tmp_path)
        assert len(second_run) == 0, "İkinci çalıştırma boş dönmeliydi"


class TestAIExportJSONContract:
    """Export JSON formatının sözleşmeye uyduğunu doğrular."""

    def test_json_structure(self, db, tmp_path):
        """Her export kaydı sözleşmedeki alanlara sahip olmalı."""
        records = run_export(conn=db, exports_dir=tmp_path)
        assert len(records) > 0

        for rec in records:
            # Zorunlu üst düzey alanlar
            assert "post_id" in rec
            assert "image_url" in rec
            assert "outfit_items" in rec
            assert "created_at" in rec
            assert isinstance(rec["outfit_items"], list)

            # outfit_items'deki her öğe
            for item in rec["outfit_items"]:
                assert "item_id" in item
                assert "category" in item
                assert "image_url" in item

    def test_export_file_written(self, db, tmp_path):
        """exports/ dizinine JSON dosyası yazılmalı."""
        run_export(conn=db, exports_dir=tmp_path)
        json_files = list(tmp_path.glob("training_export_*.json"))
        assert len(json_files) >= 1, "Export JSON dosyası oluşturulmalıydı"

        # Dosya geçerli JSON olmalı
        with open(json_files[0], "r", encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0

    def test_training_data_export_table_populated(self, db, tmp_path):
        """training_data_export tablosuna kayıt yazılmalı."""
        records = run_export(conn=db, exports_dir=tmp_path)
        rows = db.execute("SELECT * FROM training_data_export").fetchall()
        assert len(rows) == len(records)

        for row in rows:
            # export_data geçerli JSON olmalı
            data = json.loads(row["export_data"])
            assert "post_id" in data
            assert "image_url" in data
            assert "outfit_items" in data

    def test_outfit_items_grouped_correctly(self, db, tmp_path):
        """
        post-0001'in 3 outfit item'ı var (blazer, pantolon, stiletto).
        Export'ta doğru gruplanmalı.
        """
        records = run_export(conn=db, exports_dir=tmp_path)
        post_0001 = next(r for r in records if r["post_id"] == "post-0001")
        assert len(post_0001["outfit_items"]) == 3

        item_ids = {i["item_id"] for i in post_0001["outfit_items"]}
        assert "item-blazer-001" in item_ids
        assert "item-pantolon-001" in item_ids
        assert "item-stiletto-001" in item_ids

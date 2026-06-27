"""
Gizlilik Kontrol Listesi Testleri
==================================
6 senaryo tablosu — Profil görünürlük + AI Export doğrulaması.

| # | Visibility | consent | A (profil) | B (profil) | C (profil) | AI Export |
|---|------------|---------|------------|------------|------------|-----------|
| 1 | public     | true    | ✅          | ✅          | ✅          | ✅         |
| 2 | public     | false   | ✅          | ✅          | ✅          | ❌         |
| 3 | followers  | true    | ✅          | ✅          | ❌          | ✅         |
| 4 | followers  | false   | ✅          | ✅          | ❌          | ❌         |
| 5 | private    | true    | ✅          | ❌          | ❌          | ❌         |
| 6 | private    | false   | ✅          | ❌          | ❌          | ❌         |

Profil sorgusu: Belirli bir kullanıcının profilindeki postları, viewer_id'ye
göre SQL seviyesinde filtreler.
AI Export sorgusu: consent=1 AND visibility!='private' AND henüz export
edilmemiş postları döndürür.
"""

import sqlite3

from .conftest import USER_A, USER_B, USER_C

# ── Profil görünürlük sorgusu (SQL seviyesinde filtreleme) ──────────────
PROFILE_QUERY = """\
SELECT p.post_id
FROM   posts p
WHERE  p.user_id = ?
  AND  (
        p.user_id = ?                               -- sahibi her zaman görür
        OR p.visibility = 'public'                   -- public herkes görür
        OR (p.visibility = 'followers'
            AND EXISTS (
                SELECT 1 FROM follows f
                WHERE f.follower_id = ? AND f.following_id = p.user_id
            ))
       )
ORDER BY p.created_at DESC
"""

# ── AI Export sorgusu (ai_export.py ile aynı) ──────────────────────────
AI_EXPORT_QUERY = """\
SELECT p.post_id
FROM   posts p
WHERE  p.ai_training_consent = 1
  AND  p.visibility != 'private'
  AND  p.post_id NOT IN (SELECT post_id FROM training_data_export)
"""


def _get_profile_post_ids(
    db: sqlite3.Connection, profile_owner_id: str, viewer_id: str
) -> set[str]:
    """Bir kullanıcının profilinde viewer'ın görebildiği post_id'leri döndürür."""
    rows = db.execute(
        PROFILE_QUERY, (profile_owner_id, viewer_id, viewer_id)
    ).fetchall()
    return {row["post_id"] for row in rows}


def _get_ai_exportable_post_ids(db: sqlite3.Connection) -> set[str]:
    """AI export'a girecek post_id'leri döndürür."""
    rows = db.execute(AI_EXPORT_QUERY).fetchall()
    return {row["post_id"] for row in rows}


# ════════════════════════════════════════════════════════════════════════
#  Senaryo 1: public + consent=true (post-0001)
# ════════════════════════════════════════════════════════════════════════

class TestScenario1PublicConsentTrue:
    """Post-0001: public, consent=1 → herkes profilde görür, AI export'a girer."""
    POST = "post-0001"

    def test_a_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_A)

    def test_b_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_B)

    def test_c_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_C)

    def test_ai_export_includes(self, db):
        assert self.POST in _get_ai_exportable_post_ids(db)


# ════════════════════════════════════════════════════════════════════════
#  Senaryo 2: public + consent=false (post-0004)
# ════════════════════════════════════════════════════════════════════════

class TestScenario2PublicConsentFalse:
    """Post-0004: public, consent=0 → herkes profilde görür, AI export'a GİRMEZ."""
    POST = "post-0004"

    def test_a_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_A)

    def test_b_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_B)

    def test_c_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_C)

    def test_ai_export_excludes(self, db):
        assert self.POST not in _get_ai_exportable_post_ids(db)


# ════════════════════════════════════════════════════════════════════════
#  Senaryo 3: followers + consent=true (post-0002)
# ════════════════════════════════════════════════════════════════════════

class TestScenario3FollowersConsentTrue:
    """Post-0002: followers, consent=1 → A ve B görür, C görmez, AI export'a girer."""
    POST = "post-0002"

    def test_a_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_A)

    def test_b_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_B)

    def test_c_does_not_see_on_profile(self, db):
        assert self.POST not in _get_profile_post_ids(db, USER_A, USER_C)

    def test_ai_export_includes(self, db):
        assert self.POST in _get_ai_exportable_post_ids(db)


# ════════════════════════════════════════════════════════════════════════
#  Senaryo 4: followers + consent=false (post-0006)
# ════════════════════════════════════════════════════════════════════════

class TestScenario4FollowersConsentFalse:
    """Post-0006: followers, consent=0 → A ve B görür, C görmez, AI export'a GİRMEZ."""
    POST = "post-0006"

    def test_a_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_A)

    def test_b_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_B)

    def test_c_does_not_see_on_profile(self, db):
        assert self.POST not in _get_profile_post_ids(db, USER_A, USER_C)

    def test_ai_export_excludes(self, db):
        assert self.POST not in _get_ai_exportable_post_ids(db)


# ════════════════════════════════════════════════════════════════════════
#  Senaryo 5: private + consent=true (ek test verisi gerekir)
# ════════════════════════════════════════════════════════════════════════

class TestScenario5PrivateConsentTrue:
    """
    private + consent=true → sadece A profilde görür, AI export'a GİRMEZ.
    Mock data'da bu kombinasyon yok — test içinde INSERT ediyoruz.
    """

    def _insert_private_consent_post(self, db: sqlite3.Connection) -> str:
        post_id = "post-priv-consent"
        db.execute(
            "INSERT INTO posts (post_id, user_id, image_url, visibility, ai_training_consent) "
            "VALUES (?, ?, ?, 'private', 1)",
            (post_id, USER_A, "https://example.com/posts/private_consent.jpg"),
        )
        db.commit()
        return post_id

    def test_a_sees_on_profile(self, db):
        pid = self._insert_private_consent_post(db)
        assert pid in _get_profile_post_ids(db, USER_A, USER_A)

    def test_b_does_not_see_on_profile(self, db):
        pid = self._insert_private_consent_post(db)
        assert pid not in _get_profile_post_ids(db, USER_A, USER_B)

    def test_c_does_not_see_on_profile(self, db):
        pid = self._insert_private_consent_post(db)
        assert pid not in _get_profile_post_ids(db, USER_A, USER_C)

    def test_ai_export_excludes(self, db):
        pid = self._insert_private_consent_post(db)
        assert pid not in _get_ai_exportable_post_ids(db)


# ════════════════════════════════════════════════════════════════════════
#  Senaryo 6: private + consent=false (post-0003)
# ════════════════════════════════════════════════════════════════════════

class TestScenario6PrivateConsentFalse:
    """Post-0003: private, consent=0 → sadece A profilde görür, AI export'a GİRMEZ."""
    POST = "post-0003"

    def test_a_sees_on_profile(self, db):
        assert self.POST in _get_profile_post_ids(db, USER_A, USER_A)

    def test_b_does_not_see_on_profile(self, db):
        assert self.POST not in _get_profile_post_ids(db, USER_A, USER_B)

    def test_c_does_not_see_on_profile(self, db):
        assert self.POST not in _get_profile_post_ids(db, USER_A, USER_C)

    def test_ai_export_excludes(self, db):
        assert self.POST not in _get_ai_exportable_post_ids(db)

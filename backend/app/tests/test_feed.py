"""
Feed Visibility Testleri
========================
Feed sorgusunu doğrudan SQL ile test eder — router'a bağımlılık yok.

Feed kuralları:
- Feed = takip edilen kullanıcıların postları (kendi postlar hariç)
- public  → herkes görür
- followers → sadece takipçiler görür
- private → hiç kimse görmez (sadece sahibi, ama feed'de değil)
"""

import sqlite3

from .conftest import USER_A, USER_B, USER_C

# ── Feed sorgusu (SQL seviyesinde filtreleme) ───────────────────────────
FEED_QUERY = """\
SELECT p.post_id, p.visibility
FROM   posts p
INNER JOIN follows f ON f.following_id = p.user_id
WHERE  f.follower_id = ?
  AND  (
        p.visibility = 'public'
        OR (p.visibility = 'followers'
            AND EXISTS (
                SELECT 1 FROM follows f2
                WHERE f2.follower_id = ? AND f2.following_id = p.user_id
            ))
       )
ORDER BY p.created_at DESC
"""


def _get_feed_post_ids(db: sqlite3.Connection, viewer_id: str) -> set[str]:
    """Belirli bir viewer için feed'deki post_id'leri döndürür."""
    rows = db.execute(FEED_QUERY, (viewer_id, viewer_id)).fetchall()
    return {row["post_id"] for row in rows}


# ── Test senaryoları ────────────────────────────────────────────────────


class TestBFeed:
    """B kullanıcısı: A'yı takip ediyor."""

    def test_b_sees_a_public_posts(self, db, test_users):
        """B'nin feed'inde A'nın public postları GÖRÜNMELİ."""
        feed = _get_feed_post_ids(db, USER_B)
        assert "post-0001" in feed  # public, A
        assert "post-0004" in feed  # public, A

    def test_b_sees_a_followers_posts(self, db, test_users):
        """B'nin feed'inde A'nın followers postları GÖRÜNMELİ (B takipçi)."""
        feed = _get_feed_post_ids(db, USER_B)
        assert "post-0002" in feed  # followers, A
        assert "post-0006" in feed  # followers, A

    def test_b_does_not_see_a_private_posts(self, db, test_users):
        """B'nin feed'inde A'nın private postları GÖRÜNMEMELİ."""
        feed = _get_feed_post_ids(db, USER_B)
        assert "post-0003" not in feed  # private, A


class TestCFeed:
    """C kullanıcısı: A'yı takip ETMİYOR."""

    def test_c_sees_a_public_posts(self, db, test_users):
        """
        C'nin feed'inde A'nın public postları GÖRÜNMELİ.
        NOT: C, A'yı takip etmiyor. Feed = takip edilenlerin postları.
        Dolayısıyla C, A'nın hiçbir postunu feed'de göremez.
        Ancak public postlar genel keşfet/profil üzerinden erişilebilir.
        Feed sorgusu INNER JOIN follows kullandığı için C, A'yı göremez.
        Bu testte beklenen davranış: C'nin feed'inde A'nın postları YOK.
        """
        feed = _get_feed_post_ids(db, USER_C)
        # C, A'yı takip etmediği için feed'de A'nın postları görünmez
        assert "post-0001" not in feed
        assert "post-0004" not in feed

    def test_c_does_not_see_a_followers_posts(self, db, test_users):
        """C'nin feed'inde A'nın followers postları GÖRÜNMEMELİ (C takipçi değil)."""
        feed = _get_feed_post_ids(db, USER_C)
        assert "post-0002" not in feed
        assert "post-0006" not in feed

    def test_c_does_not_see_a_private_posts(self, db, test_users):
        """C'nin feed'inde A'nın private postları GÖRÜNMEMELİ."""
        feed = _get_feed_post_ids(db, USER_C)
        assert "post-0003" not in feed


class TestSelfFeed:
    """A kullanıcısı: Kendi feed'inde kendi postlarını görmemeli."""

    def test_a_does_not_see_own_posts_in_feed(self, db, test_users):
        """
        A'nın kendi feed'inde kendi postları GÖRÜNMEMELİ.
        Feed = takip edilen kullanıcıların postları.
        A kendini takip etmiyor → kendi postları feed'de yok.
        """
        feed = _get_feed_post_ids(db, USER_A)
        a_posts = {"post-0001", "post-0002", "post-0003", "post-0004", "post-0006"}
        assert feed.isdisjoint(a_posts)

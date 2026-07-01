-- ============================================================
-- Dijital Gardrop — Sosyal Medya Modülü
-- Veritabanı: SQLite
-- ============================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. USERS
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id       TEXT PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    display_name  TEXT NOT NULL DEFAULT '',
    avatar_url    TEXT DEFAULT NULL,
    bio           TEXT DEFAULT NULL,
    followers_count INTEGER NOT NULL DEFAULT 0,
    following_count INTEGER NOT NULL DEFAULT 0,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_users_username
    ON users(username);

-- ============================================================
-- 2. POSTS
-- ============================================================
CREATE TABLE IF NOT EXISTS posts (
    post_id              TEXT PRIMARY KEY,
    user_id              TEXT NOT NULL,
    image_url            TEXT NOT NULL,
    caption              TEXT DEFAULT NULL,
    visibility           TEXT NOT NULL DEFAULT 'public'
        CHECK (visibility IN ('public', 'followers', 'private')),
    ai_training_consent  INTEGER NOT NULL DEFAULT 0
        CHECK (ai_training_consent IN (0, 1)),
    likes_count          INTEGER NOT NULL DEFAULT 0,
    created_at           TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Feed + profil sorgusu: kullanıcıya göre filtrele, zamana göre sırala
CREATE INDEX IF NOT EXISTS idx_posts_user_created
    ON posts(user_id, created_at DESC);

-- Genel sıralama
CREATE INDEX IF NOT EXISTS idx_posts_created
    ON posts(created_at DESC);

-- AI export batch job filtresi (partial index)
CREATE INDEX IF NOT EXISTS idx_posts_ai_export
    ON posts(ai_training_consent, visibility)
    WHERE ai_training_consent = 1;

-- ============================================================
-- 3. FOLLOWS  (Many-to-Many, normalised)
-- ============================================================
CREATE TABLE IF NOT EXISTS follows (
    follower_id   TEXT NOT NULL,
    following_id  TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (follower_id, following_id),
    FOREIGN KEY (follower_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (following_id) REFERENCES users(user_id) ON DELETE CASCADE,
    CHECK (follower_id != following_id)
);

-- "Kimi takip ediyorum?"
CREATE INDEX IF NOT EXISTS idx_follows_follower
    ON follows(follower_id);

-- "Beni kim takip ediyor?"
CREATE INDEX IF NOT EXISTS idx_follows_following
    ON follows(following_id);

-- ============================================================
-- 4. LIKES  (Many-to-Many, normalised)
-- ============================================================
CREATE TABLE IF NOT EXISTS likes (
    post_id    TEXT NOT NULL,
    user_id    TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    PRIMARY KEY (post_id, user_id),
    FOREIGN KEY (post_id)  REFERENCES posts(post_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id)  REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_likes_post
    ON likes(post_id);

CREATE INDEX IF NOT EXISTS idx_likes_user_post
    ON likes(user_id, post_id);

-- ============================================================
-- 5. POST_OUTFIT_ITEMS  (Post ↔ AI-module item join table)
-- ============================================================
CREATE TABLE IF NOT EXISTS post_outfit_items (
    post_id   TEXT NOT NULL,
    item_id   TEXT NOT NULL,
    category  TEXT NOT NULL DEFAULT 'diğer'
        CHECK (category IN (
            'üst giyim', 'alt giyim', 'ayakkabı',
            'aksesuar', 'dış giyim', 'diğer'
        )),
    image_url TEXT DEFAULT NULL,
    PRIMARY KEY (post_id, item_id),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_outfit_items_post
    ON post_outfit_items(post_id);

CREATE INDEX IF NOT EXISTS idx_outfit_items_item
    ON post_outfit_items(item_id);

-- ============================================================
-- 6. TRAINING_DATA_EXPORT  (AI export job output — ayrı tablo)
-- ============================================================
CREATE TABLE IF NOT EXISTS training_data_export (
    export_id   TEXT PRIMARY KEY,
    post_id     TEXT NOT NULL,
    export_data TEXT NOT NULL,          -- JSON string
    exported_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (post_id) REFERENCES posts(post_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_export_post
    ON training_data_export(post_id);

-- ============================================================
-- 7. KIYAFETLEr  (Dolap modülü)
-- ============================================================
CREATE TABLE IF NOT EXISTS kiyafetler (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id           TEXT NOT NULL,
    tur               TEXT NOT NULL,
    renk              TEXT NOT NULL,
    marka             TEXT DEFAULT NULL,
    beden             TEXT DEFAULT NULL,
    kumas             TEXT DEFAULT NULL,
    kesim             TEXT DEFAULT NULL,
    yaka_tipi         TEXT DEFAULT NULL,
    kol_tipi          TEXT DEFAULT NULL,
    desen             TEXT DEFAULT NULL,
    mevsim            TEXT DEFAULT NULL,
    stil_etiketi      TEXT DEFAULT NULL,
    kullanim_sikligi  TEXT DEFAULT NULL,
    kombin_notu       TEXT DEFAULT NULL,
    foto_url          TEXT DEFAULT NULL,
    temiz             INTEGER NOT NULL DEFAULT 1 CHECK (temiz IN (0,1)),
    created_at        TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE INDEX IF NOT EXISTS idx_kiyafetler_user
    ON kiyafetler(user_id);

-- ============================================================
-- 8. KATEGORİ_DEGERLERİ  (Dolap formu açılır menü seçenekleri)
-- ============================================================
CREATE TABLE IF NOT EXISTS kategori_degerleri (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    tip        TEXT NOT NULL,
    deger      TEXT NOT NULL,
    UNIQUE(tip, deger)
);

-- Başlangıç verileri
INSERT OR IGNORE INTO kategori_degerleri (tip, deger) VALUES
  ('tur','tişört'),('tur','gömlek'),('tur','kazak'),('tur','pantolon'),
  ('tur','etek'),('tur','elbise'),('tur','ceket'),('tur','mont'),
  ('tur','ayakkabı'),('tur','çanta'),('tur','aksesuar'),
  ('kumas','pamuk'),('kumas','polyester'),('kumas','keten'),('kumas','yün'),('kumas','denim'),
  ('kesim','slim fit'),('kesim','regular fit'),('kesim','oversize'),('kesim','skinny'),
  ('yaka_tipi','bisiklet'),('yaka_tipi','v yaka'),('yaka_tipi','polo'),('yaka_tipi','kapüşon'),
  ('kol_tipi','kısa kol'),('kol_tipi','uzun kol'),('kol_tipi','kolsuz'),
  ('desen','düz'),('desen','çizgili'),('desen','ekoseli'),('desen','çiçekli'),('desen','baskılı'),
  ('mevsim','ilkbahar'),('mevsim','yaz'),('mevsim','sonbahar'),('mevsim','kış'),('mevsim','her mevsim'),
  ('stil_etiketi','casual'),('stil_etiketi','business'),('stil_etiketi','sport'),('stil_etiketi','elegant'),
  ('kullanim_sikligi','her gün'),('kullanim_sikligi','sık sık'),('kullanim_sikligi','ara sıra'),('kullanim_sikligi','nadiren');

-- ============================================================
-- 9. KOMBİN_ÖNERİLERİ
-- ============================================================
CREATE TABLE IF NOT EXISTS kombin_onerileri (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       TEXT NOT NULL,
    etkinlik      TEXT NOT NULL,
    hava_durumu   TEXT NOT NULL,
    stil_tercihi  TEXT DEFAULT NULL,
    aciklama      TEXT NOT NULL,
    kiyafet_idler TEXT NOT NULL,  -- JSON array
    begenildi     INTEGER DEFAULT NULL CHECK (begenildi IN (0,1,NULL)),
    created_at    TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

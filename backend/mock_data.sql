-- ============================================================
-- Dijital Gardrop — Mock Data
-- ============================================================
-- Kullanıcılar:
--   A (elif_style)   → post sahibi
--   B (ahmet_trendy) → A'yı takip ediyor
--   C (zeynep_chic)  → A'yı takip ETMİYOR
-- ============================================================

-- 1. Kullanıcılar
INSERT INTO users (user_id, username, display_name, avatar_url, bio, followers_count, following_count) VALUES
    ('user-a-0001', 'elif_style',    'Elif Yılmaz',  'https://example.com/avatars/elif.jpg',   'Moda tutkunu 👗 | İstanbul', 1, 0),
    ('user-b-0002', 'ahmet_trendy',  'Ahmet Demir',  'https://example.com/avatars/ahmet.jpg',  'Streetwear & sneakers 👟',    0, 1),
    ('user-c-0003', 'zeynep_chic',   'Zeynep Kaya',  'https://example.com/avatars/zeynep.jpg', 'Minimalist stil ✨',          0, 0);

-- 2. Takip ilişkileri: B → A
INSERT INTO follows (follower_id, following_id) VALUES
    ('user-b-0002', 'user-a-0001');

-- 3. Postlar (farklı visibility + consent kombinasyonları)
INSERT INTO posts (post_id, user_id, image_url, caption, visibility, ai_training_consent, likes_count) VALUES
    -- Post 1: public + consent=true  → herkes görür, AI export'a GİRER
    ('post-0001', 'user-a-0001', 'https://example.com/posts/outfit1.jpg',
     'Bugünkü iş kombinom 💼', 'public', 1, 2),

    -- Post 2: followers + consent=true  → sadece A ve B görür, AI export'a GİRER
    ('post-0002', 'user-a-0001', 'https://example.com/posts/outfit2.jpg',
     'Hafta sonu rahatlığı 🌿', 'followers', 1, 1),

    -- Post 3: private + consent=false  → sadece A görür, AI export'a GİRMEZ
    ('post-0003', 'user-a-0001', 'https://example.com/posts/outfit3.jpg',
     'Deneme kombini - henüz paylaşmak istemiyorum', 'private', 0, 0),

    -- Post 4: public + consent=false  → herkes görür, AI export'a GİRMEZ
    ('post-0004', 'user-a-0001', 'https://example.com/posts/outfit4.jpg',
     'Yeni sezon alışverişim 🛍️', 'public', 0, 3),

    -- Post 5: B'nin public postu + consent=true
    ('post-0005', 'user-b-0002', 'https://example.com/posts/sneakers1.jpg',
     'Yeni sneaker''larım 🔥', 'public', 1, 1),

    -- Post 6: followers + consent=false  → sadece A ve B görür, AI export'a GİRMEZ
    ('post-0006', 'user-a-0001', 'https://example.com/posts/outfit5.jpg',
     'Sadece takipçilerime özel kombin', 'followers', 0, 0);

-- 4. Beğeniler
INSERT INTO likes (post_id, user_id) VALUES
    ('post-0001', 'user-b-0002'),
    ('post-0001', 'user-c-0003'),
    ('post-0002', 'user-b-0002'),
    ('post-0004', 'user-a-0001'),
    ('post-0004', 'user-b-0002'),
    ('post-0004', 'user-c-0003'),
    ('post-0005', 'user-a-0001');

-- 5. Outfit item referansları (AI modülünden gelen kombin parçaları)
INSERT INTO post_outfit_items (post_id, item_id, category, image_url) VALUES
    ('post-0001', 'item-blazer-001',   'üst giyim', 'https://example.com/items/blazer.jpg'),
    ('post-0001', 'item-pantolon-001', 'alt giyim', 'https://example.com/items/pantolon.jpg'),
    ('post-0001', 'item-stiletto-001', 'ayakkabı',  'https://example.com/items/stiletto.jpg'),
    ('post-0002', 'item-tshirt-001',   'üst giyim', 'https://example.com/items/tshirt.jpg'),
    ('post-0002', 'item-jean-001',     'alt giyim', 'https://example.com/items/jean.jpg'),
    ('post-0005', 'item-hoodie-001',   'üst giyim', 'https://example.com/items/hoodie.jpg'),
    ('post-0005', 'item-sneaker-001',  'ayakkabı',  'https://example.com/items/sneaker.jpg');

# Gizlilik Doğrulama Kontrol Listesi — Dijital Gardrop

> Sosyal Medya Modülü için gizlilik ve veri koruma doğrulama dokümanı.

---

## 1. Test Senaryoları Özet Tablosu

| # | Post | Visibility | AI Consent | A (sahibi) profilde görür? | B (takipçi) profilde görür? | C (takipçi değil) profilde görür? | AI Export'a girer? |
|---|------|-----------|------------|---------------------------|----------------------------|----------------------------------|-------------------|
| 1 | post-0001 | `public` | ✅ `true` | ✅ Evet | ✅ Evet | ✅ Evet | ✅ Evet |
| 2 | post-0004 | `public` | ❌ `false` | ✅ Evet | ✅ Evet | ✅ Evet | ❌ Hayır |
| 3 | post-0002 | `followers` | ✅ `true` | ✅ Evet | ✅ Evet | ❌ Hayır | ✅ Evet |
| 4 | post-0006 | `followers` | ❌ `false` | ✅ Evet | ✅ Evet | ❌ Hayır | ❌ Hayır |
| 5 | *(ek veri)* | `private` | ✅ `true` | ✅ Evet | ❌ Hayır | ❌ Hayır | ❌ Hayır |
| 6 | post-0003 | `private` | ❌ `false` | ✅ Evet | ❌ Hayır | ❌ Hayır | ❌ Hayır |

### Kurallar

- **public**: Herkes profilde görebilir.
- **followers**: Yalnızca takipçiler ve sahibi görebilir.
- **private**: Yalnızca sahibi görebilir.
- **AI Export**: `ai_training_consent = 1` **VE** `visibility != 'private'` olan postlar export edilir.
- **Feed**: Takip edilen kullanıcıların postları gösterilir. Kendi postlar feed'de görünmez.

---

## 2. KVKK Uyumluluk Notları

### 2.1 Veri Silme / Unutulma Hakkı (Madde 7)

- Veritabanı şemasında tüm ilişkili tablolar `ON DELETE CASCADE` ile bağlanmıştır:
  - `posts` → `post_outfit_items`, `likes`, `training_data_export`
  - `users` → `posts`, `follows`, `likes`
- Kullanıcı veya post silindiğinde **tüm ilişkili veri otomatik olarak temizlenir**.
- `training_data_export` tablosu da `ON DELETE CASCADE` ile bağlıdır → post silindiğinde export kaydı da silinir.

> [!IMPORTANT]
> `exports/` dizinine yazılan JSON dosyaları veritabanı CASCADE ile SİLİNMEZ.
> Periyodik temizlik mekanizması gereklidir (bkz. Eksik Noktalar).

### 2.2 Consent Geri Çekme Akışı

1. Kullanıcı `ai_training_consent = 0` yapar (UPDATE sorgusu).
2. Bir sonraki export batch job'unda:
   - `WHERE ai_training_consent = 1` filtresi sayesinde bu post **artık export'a dahil edilmez**.
   - Ancak daha önce export edilmiş veri `training_data_export` tablosunda kalır.
3. **Gerekli ek aksiyon**: Consent geri çekildiğinde `training_data_export` tablosundan ilgili kaydın silinmesi için ayrı bir mekanizma gereklidir.

> [!WARNING]
> Mevcut implementasyonda consent geri çekme sonrası eski export kayıtları otomatik silinmiyor.
> Bu, KVKK Madde 7 kapsamında bir risk oluşturur ve MVP sonrası ele alınmalıdır.

### 2.3 Veri Taşınabilirlik Hakkı (Madde 10)

- Kullanıcının tüm verilerini JSON/CSV formatında indirmesine olanak tanıyan bir endpoint gereklidir.
- Kapsam: profil bilgileri, postlar, beğeniler, takip listesi, outfit item'ları.
- Export formatı: AI export JSON sözleşmesiyle uyumlu olabilir.

### 2.4 Aydınlatma Metni

- Kullanıcıya kayıt sırasında ve AI consent toggle'ı aktif edilirken aydınlatma metni gösterilmelidir.
- İçerik:
  - Hangi verilerin toplandığı
  - Verilerin hangi amaçla kullanılacağı (AI model eğitimi)
  - Verilerin ne kadar süre saklanacağı
  - Kullanıcının hakları (silme, taşınabilirlik, consent geri çekme)
  - Veri sorumlusunun iletişim bilgileri

---

## 3. Filtreleme Prensipleri

> [!CAUTION]
> Tüm filtreleme **SQL seviyesinde** yapılmalıdır. Python'da post-filtering **ASLA** kabul edilemez.
> Bu kural hem güvenlik hem performans açısından kritiktir.

### Neden SQL seviyesinde?

1. **Güvenlik**: Yetkisiz veri asla uygulama katmanına ulaşmaz.
2. **Performans**: Gereksiz veri transferi önlenir.
3. **Tutarlılık**: Filtreleme mantığı tek bir yerde tanımlanır.
4. **Denetlenebilirlik**: SQL sorguları kolayca incelenebilir.

### Kullanılan SQL Filtreleri

| Bağlam | Filtre |
|--------|--------|
| Profil görüntüleme | `visibility` + `follows` tablosu JOIN |
| Feed | `INNER JOIN follows` + `visibility` kontrolü |
| AI Export | `ai_training_consent = 1 AND visibility != 'private'` |
| İdempotency | `NOT IN (SELECT post_id FROM training_data_export)` |

---

## 4. Eksik Noktalar (MVP Sonrası)

> [!NOTE]
> Aşağıdaki maddeler mevcut MVP kapsamında değildir ancak prodüksiyona geçmeden önce ele alınmalıdır.

### 4.1 Kullanıcı Hesap Silme Endpoint'i

- `DELETE /api/users/{user_id}` endpoint'i gerekli.
- `ON DELETE CASCADE` sayesinde veritabanı temizliği otomatik.
- Ek olarak: `exports/` dizinindeki JSON dosyalarından ilgili kullanıcı verisi temizlenmeli.

### 4.2 Export Edilen Verinin Periyodik Temizliği

- `exports/` dizinindeki eski JSON dosyaları belirli bir süre sonra silinmeli.
- Önerilen retention süresi: 90 gün.
- Cron job ile otomatik temizlik mekanizması kurulmalı.

### 4.3 Audit Log

- Veri erişim ve export işlemleri loglanmalı:
  - Kim ne zaman hangi veriye erişti?
  - AI export job'u ne zaman çalıştı, kaç kayıt işledi?
  - Consent değişiklikleri (true → false, false → true)
- Loglama formatı: yapılandırılmış JSON.
- Saklama süresi: en az 1 yıl.

### 4.4 Consent Geri Çekme Otomasyonu

- Kullanıcı `ai_training_consent = 0` yaptığında:
  1. `training_data_export` tablosundan ilgili kayıt silinmeli.
  2. `exports/` dizinindeki JSON dosyalarından ilgili post çıkarılmalı.
  3. Eğer veri harici bir sisteme aktarıldıysa, silme talebi iletilmeli.

### 4.5 Rate Limiting ve Abuse Prevention

- Profil görüntüleme ve feed endpoint'lerine rate limiting uygulanmalı.
- Toplu veri çekme (scraping) girişimleri tespit edilmeli.

---

## 5. Test Dosyaları

| Dosya | Kapsam | Test Sayısı |
|-------|--------|-------------|
| `test_feed.py` | Feed visibility kuralları | 7 |
| `test_privacy.py` | 6 senaryoluk profil + AI export matrisi | 24 |
| `test_ai_export.py` | AI export fonksiyon testleri | 10 |
| **Toplam** | | **41** |

---

## 6. Doğrulama Kontrol Listesi

- [x] Tüm filtreleme SQL seviyesinde yapılıyor
- [x] `ON DELETE CASCADE` tüm ilişkili tablolarda aktif
- [x] AI export sadece consent=true VE visibility!=private postları alıyor
- [x] İdempotency: aynı post tekrar export edilmiyor
- [x] Feed'de kendi postlar görünmüyor
- [x] Private postlar sadece sahipleri tarafından görülebiliyor
- [x] Followers postlar sadece takipçiler tarafından görülebiliyor
- [ ] Consent geri çekme sonrası eski export kayıtları siliniyor *(MVP sonrası)*
- [ ] Export JSON dosyaları periyodik olarak temizleniyor *(MVP sonrası)*
- [ ] Kullanıcı hesap silme endpoint'i mevcut *(MVP sonrası)*
- [ ] Audit log mekanizması aktif *(MVP sonrası)*
- [ ] Aydınlatma metni UI'da gösteriliyor *(MVP sonrası)*

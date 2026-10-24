# Veri Tabanı Şeması (PostgreSQL 16 + pgvector)

> Kaynak: `docs/plan/CareerAI_Proje_ve_GoLive_Plani.xlsx` (24.10.2026). Bu dosya ile Excel çelişirse bu dosya geçerlidir; değişiklikler PR ile buraya işlenir.

**KVKK kuralı:** CV dosyası ve ham CV metni hiçbir tabloda saklanmaz. Sadece SHA-256 hash, sayfa sayısı ve çıkarılan yetkinlikler (kullanıcı rızasıyla) tutulur.

**Genel kurallar:** Tüm tablolarda `created_at` / `updated_at` (timestamptz, varsayılan `now()`). Kullanıcıya bağlı tablolarda `ON DELETE CASCADE`. Şema değişiklikleri sadece Alembic migration ile yapılır (sahibi: Ataberk).

## İlişkiler (özet)

```
users ─┬─< refresh_tokens
       ├─< consents
       ├─< analyses ─┬─< analysis_skills >── skills
       │             ├─< analysis_recommendations >── resources >── skills
       │             └─< feedback
       └── target_role_id >── roles

job_sources ─< job_postings ─< job_posting_skills >── skills
job_sources ─< scrape_runs
roles × skills ─── role_skill_stats (talep oranları, gece yenilenir)
audit_logs (bağımsız denetim kaydı)
```

## Tablolar

### `users`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | uuid | PK | Kullanıcı kimliği |
| email | citext | UNIQUE, NOT NULL | Giriş e-postası (büyük/küçük harf duyarsız) |
| password_hash | text | NOT NULL | argon2 hash |
| full_name | varchar(120) |  | Görünen ad (opsiyonel) |
| role | enum(user, admin) | DEFAULT user | Yetki rolü |
| target_role_id | int | FK → roles.id | Hedef pozisyon |
| is_verified | boolean | DEFAULT false | E-posta doğrulandı mı |
| deleted_at | timestamptz | NULL | Soft delete; 30 gün sonra kalıcı silme işi |

### `refresh_tokens`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | uuid | PK |  |
| user_id | uuid | FK → users.id ON DELETE CASCADE, INDEX |  |
| token_hash | text | UNIQUE | Refresh token'ın SHA-256 hash'i (token kendisi saklanmaz) |
| expires_at | timestamptz | NOT NULL | 7 gün |
| revoked_at | timestamptz | NULL | Rotasyon/çıkışta doldurulur |
| user_agent | text |  | Oturum yönetimi için |

### `consents`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | uuid | PK |  |
| user_id | uuid | FK → users.id, INDEX |  |
| consent_type | enum(kvkk_aydinlatma, acik_riza, kullanim_kosullari) | NOT NULL | Rıza türü |
| version | varchar(20) | NOT NULL | Metnin sürümü (ör. 2026-12) |
| accepted_at | timestamptz | NOT NULL | Onay zamanı |
| ip_hash | text |  | IP'nin tuzlu hash'i (ispat için, açık IP değil) |

### `roles`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | serial | PK | Pozisyon (Backend Developer vb.) |
| name | varchar(100) | NOT NULL | Görünen ad |
| slug | varchar(100) | UNIQUE | URL dostu ad |
| synonyms | text[] | GIN INDEX | İlan başlığı normalizasyonu için eş anlamlılar |
| description | text |  |  |

### `skills`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | serial | PK |  |
| canonical_name | varchar(100) | UNIQUE | Standart ad (JavaScript) |
| slug | varchar(100) | UNIQUE |  |
| category | enum(dil, framework, veritabani, bulut, devops, arac, metodoloji, soft) | INDEX | Kategori |
| synonyms | text[] | GIN INDEX | JS, Javascript, ECMAScript… |
| esco_uri | text | NULL | ESCO referansı |
| embedding | vector(384) | HNSW (vector_cosine_ops) | Anlamsal eşleşme vektörü |

### `job_sources`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | serial | PK |  |
| name | varchar(100) | UNIQUE | Kaynak adı |
| type | enum(api, scrape, dataset) | NOT NULL | Toplama yöntemi |
| base_url | text |  |  |
| tos_checked | boolean | DEFAULT false | Kullanım koşulları/robots.txt incelendi mi |
| rate_limit_sec | numeric(4,1) | DEFAULT 4 | İstekler arası bekleme |
| is_active | boolean | DEFAULT true | Kapatılabilir |

### `job_postings`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | bigserial | PK |  |
| source_id | int | FK → job_sources.id |  |
| external_id | text | UNIQUE(source_id, external_id) | Kaynaktaki kimlik |
| url | text |  | İlan linki |
| title_raw | text |  | Orijinal başlık |
| role_id | int | FK → roles.id, INDEX | Normalize edilmiş pozisyon |
| company | text |  |  |
| location | text |  | Şehir / uzaktan |
| description_clean | text |  | Temizlenmiş ilan metni |
| language | char(2) |  | tr / en |
| posted_at | date | INDEX | Yayın tarihi (son 6 ay filtrelenir) |
| content_hash | char(64) | UNIQUE | Tekrar kayıt engeli |
| embedding | vector(384) | HNSW |  |
| is_active | boolean | DEFAULT true |  |

### `job_posting_skills`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| posting_id | bigint | PK(posting_id, skill_id), FK |  |
| skill_id | int | FK → skills.id, INDEX |  |
| importance | enum(required, preferred) |  | Zorunlu / tercih sebebi |

### `role_skill_stats`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| role_id | int | PK(role_id, skill_id) |  |
| skill_id | int | FK |  |
| posting_count | int |  | Bu yetkinliği isteyen ilan sayısı |
| total_postings | int |  | Pozisyondaki toplam ilan |
| demand_ratio | numeric(5,4) |  | posting_count / total_postings → "%75" |
| computed_at | timestamptz |  | Gece yenilenir |

### `scrape_runs`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | bigserial | PK |  |
| source_id | int | FK |  |
| started_at / finished_at | timestamptz |  |  |
| status | enum(running, success, partial, failed) | INDEX |  |
| fetched / inserted / duplicates / errors | int |  | Sayaçlar |
| error_log | text |  | Son hata özeti |

### `resources`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | serial | PK | Eğitim kaynağı |
| skill_id | int | FK → skills.id, INDEX |  |
| title | text | NOT NULL |  |
| url | text | UNIQUE |  |
| provider | enum(youtube, udemy, coursera, btk_akademi, docs, blog, other) |  |  |
| language | char(2) |  | tr öncelikli |
| level | enum(beginner, intermediate, advanced) |  |  |
| duration_min | int |  |  |
| is_free | boolean |  |  |
| is_alive | boolean | DEFAULT true | Haftalık link kontrolü |
| last_checked_at | timestamptz |  |  |

### `analyses`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | uuid | PK |  |
| user_id | uuid | FK → users.id ON DELETE CASCADE, INDEX |  |
| target_role_id | int | FK → roles.id |  |
| status | enum(queued, processing, done, failed) | INDEX |  |
| cv_sha256 | char(64) | INDEX | Önbellek anahtarı; dosya/metin SAKLANMAZ |
| cv_pages | smallint |  |  |
| match_score | numeric(5,2) |  | 0-100 uyum skoru |
| postings_analyzed | int |  | "İncelenen 150 ilan" |
| model_name / prompt_version | varchar(60) |  | Tekrarlanabilirlik |
| duration_ms | int |  | Performans takibi |
| error_code | varchar(40) | NULL |  |
| completed_at | timestamptz |  |  |

### `analysis_skills`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| analysis_id | uuid | PK(analysis_id, skill_id), FK CASCADE |  |
| skill_id | int | FK |  |
| kind | enum(present, missing) |  | CV'de var / eksik |
| level | enum(beginner, intermediate, advanced, unknown) |  |  |
| confidence | numeric(3,2) |  | 0-1 |
| demand_ratio | numeric(5,4) |  | O anki talep oranı (anlık görüntü) |

### `analysis_recommendations`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | bigserial | PK |  |
| analysis_id | uuid | FK CASCADE, INDEX |  |
| skill_id | int | FK |  |
| resource_id | int | FK → resources.id | Sadece DB'deki kaynaklar → uydurma link yok |
| rank | smallint |  | Öncelik sırası |
| reason_text | text |  | LLM'in Türkçe gerekçesi |

### `feedback`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | bigserial | PK |  |
| analysis_id | uuid | FK CASCADE |  |
| rating | smallint | CHECK 1-5 |  |
| comment | text |  |  |

### `audit_logs`

| Sütun | Tip | Kısıt / İndeks | Açıklama |
|---|---|---|---|
| id | bigserial | PK |  |
| user_id | uuid | NULL, INDEX |  |
| action | varchar(60) |  | login, analysis.create, account.delete, data.export… |
| entity / entity_id | text |  |  |
| ip_hash | text |  |  |
| created_at | timestamptz | INDEX | 180 gün saklanır |

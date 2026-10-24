# ERD: veritabanı şeması

> **Kaynak:** `docs/veritabani.md`. Ataberk'in şeması (T-011) kesinleşince onunla karşılaştırılıp güncellenecek. Şemanın kendisi Alembic migration'larıdır; bu diyagram onların resmidir, tersi değil.

Tüm tablolarda `created_at` / `updated_at` vardır; diyagramı sade tutmak için gösterilmedi. **CV dosyası ve ham CV metni hiçbir tabloda yoktur**; analizde sadece `cv_sha256` ve sayfa sayısı tutulur (karar #9).

```mermaid
erDiagram
    users ||--o{ refresh_tokens : "oturum"
    users ||--o{ consents : "KVKK rızası"
    users ||--o{ analyses : "yapar"
    roles |o--o{ users : "hedef pozisyon"
    roles ||--o{ analyses : "hedef"
    analyses ||--o{ analysis_skills : "içerir"
    skills ||--o{ analysis_skills : ""
    analyses ||--o{ analysis_recommendations : "önerir"
    resources ||--o{ analysis_recommendations : ""
    skills ||--o{ analysis_recommendations : ""
    analyses ||--o{ feedback : "puanlanır"
    skills ||--o{ resources : "öğretir"

    job_sources ||--o{ job_postings : "kaynak"
    job_sources ||--o{ scrape_runs : "çalışma"
    roles |o--o{ job_postings : "pozisyon"
    job_postings ||--o{ job_posting_skills : "ister"
    skills ||--o{ job_posting_skills : ""
    roles ||--o{ role_skill_stats : ""
    skills ||--o{ role_skill_stats : "talep oranı"
    users |o--o{ audit_logs : "denetim"

    users {
        uuid id PK
        citext email UK
        text password_hash "argon2"
        varchar full_name
        enum role "user | admin"
        int target_role_id FK
        boolean is_verified
        timestamptz deleted_at "soft delete"
    }
    refresh_tokens {
        uuid id PK
        uuid user_id FK
        text token_hash UK "token saklanmaz"
        timestamptz expires_at
        timestamptz revoked_at
    }
    consents {
        uuid id PK
        uuid user_id FK
        enum consent_type
        varchar version
        timestamptz accepted_at
        text ip_hash
    }
    roles {
        serial id PK
        varchar name
        varchar slug UK
        text_array synonyms
    }
    skills {
        serial id PK
        varchar canonical_name UK
        varchar slug UK
        enum category
        text_array synonyms
        vector384 embedding "HNSW"
    }
    resources {
        serial id PK
        int skill_id FK
        text title
        text url UK
        enum provider
        char2 language
        enum level
        boolean is_free
        boolean is_alive "haftalık kontrol"
    }
    analyses {
        uuid id PK
        uuid user_id FK
        int target_role_id FK
        enum status "queued | processing | done | failed"
        char64 cv_sha256 "dosya/metin YOK"
        smallint cv_pages
        numeric match_score "0-100"
        int postings_analyzed
        varchar model_name
        varchar prompt_version
        int duration_ms
        varchar error_code
    }
    analysis_skills {
        uuid analysis_id PK,FK
        int skill_id PK,FK
        enum kind "present | missing"
        enum level
        numeric confidence
        numeric demand_ratio
    }
    analysis_recommendations {
        bigserial id PK
        uuid analysis_id FK
        int skill_id FK
        int resource_id FK "sadece DB'deki kaynak"
        smallint rank
        text reason_text "LLM gerekçesi"
    }
    feedback {
        bigserial id PK
        uuid analysis_id FK
        smallint rating "1-5"
        text comment
    }
    job_sources {
        serial id PK
        varchar name UK
        enum type "api | scrape | dataset"
        boolean tos_checked
        numeric rate_limit_sec
        boolean is_active
    }
    job_postings {
        bigserial id PK
        int source_id FK
        text external_id
        int role_id FK
        text title_raw
        text description_clean
        char2 language
        date posted_at
        char64 content_hash UK
        vector384 embedding "HNSW"
    }
    job_posting_skills {
        bigint posting_id PK,FK
        int skill_id PK,FK
        enum importance "required | preferred"
    }
    role_skill_stats {
        int role_id PK,FK
        int skill_id PK,FK
        int posting_count
        int total_postings
        numeric demand_ratio
        timestamptz computed_at
    }
    scrape_runs {
        bigserial id PK
        int source_id FK
        enum status
        int fetched
        int inserted
        int errors
    }
    audit_logs {
        bigserial id PK
        uuid user_id FK "NULL olabilir"
        varchar action
        text ip_hash
        timestamptz created_at "180 gün"
    }
```

## Notlar

- **Kullanıcı silinince** (`ON DELETE CASCADE`): oturumlar, rızalar, analizler ve analizlere bağlı yetkinlik / öneri / puan kayıtları silinir. `audit_logs` bağımsız denetim kaydıdır (`user_id` boş olabilir, 180 gün saklanır); silmede ne olacağı T-011'de netleşmeli.
- **İki ayrı dünya:** üst yarı kullanıcı ve analizler (Anıl + Burak yazar), alt yarı ilanlar ve istatistikler (Ataberk'in toplayıcısı yazar). İkisi `skills` ve `roles` tablolarında buluşur.
- **Tip kısaltmaları** (Mermaid sınırı): `text_array` = `text[]`, `vector384` = `vector(384)`, `char64` = `char(64)`, `char2` = `char(2)`.

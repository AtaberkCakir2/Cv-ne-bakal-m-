# REST API taslağı (/api/v1)

Taslaktır; kesin hali FastAPI'nin ürettiği OpenAPI dokümanıdır (`/docs`). Hatalar RFC 7807 formatında döner. Kimlik doğrulama: `Authorization: Bearer <access_token>`.

## Kimlik doğrulama
| Metot | Yol | Açıklama |
|---|---|---|
| POST | `/auth/register` | Kayıt + KVKK rızaları |
| POST | `/auth/login` | Giriş → `{access_token, refresh_token}` |
| POST | `/auth/refresh` | Token yenileme |
| POST | `/auth/logout` | Çıkış |
| POST | `/auth/verify-email` | E-posta doğrulama |
| POST | `/auth/forgot-password` | Şifre sıfırlama e-postası |
| POST | `/auth/reset-password` | Yeni şifre |

## Kullanıcı (KVKK)
| Metot | Yol | Açıklama |
|---|---|---|
| GET | `/users/me` | Profil |
| PATCH | `/users/me` | Profil / hedef pozisyon güncelleme |
| GET | `/users/me/export` | Verilerimi indir (JSON) |
| DELETE | `/users/me` | Hesabımı sil |

## Analiz
| Metot | Yol | Açıklama |
|---|---|---|
| POST | `/analyses` | CV yükle (PDF, ≤ 5 MB, ≤ 5 sayfa) + `target_role_id` → `202 {analysis_id, status: "queued"}` |
| GET | `/analyses` | Geçmiş analizlerim |
| GET | `/analyses/{id}` | Sonuç → `analysis_result.schema.json` |
| GET | `/analyses/{id}/events` | İlerleme (SSE) |
| DELETE | `/analyses/{id}` | Analizi sil |
| POST | `/analyses/{id}/feedback` | 1-5 puan + yorum |

## Katalog
| Metot | Yol | Açıklama |
|---|---|---|
| GET | `/roles` | Hedef pozisyonlar |
| GET | `/roles/{slug}/skills` | Pozisyonun en çok istenen yetkinlikleri |
| GET | `/skills?q=` | Yetkinlik arama |
| GET | `/skills/{slug}/resources` | Yetkinlik için eğitim kaynakları |

## Sistem
| Metot | Yol | Açıklama |
|---|---|---|
| GET | `/health` | Canlılık |
| GET | `/health/ready` | DB, Redis, Ollama erişimi |

"""Vektörü üretilecek metinler. Sorgu tarafı (CV yetkinliği, T-042) da aynı fonksiyonları kullanmalı."""

from __future__ import annotations

from collections.abc import Sequence

# e5-small 512 token görür ama süre metinle artıyor (CPU: 1.000 karakter 19 ilan/sn, 2.000 karakter 9 ilan/sn).
# Başlık + açıklamanın başı ilanın konusunu taşıyor; yetkinlikler zaten job_posting_skills'te.
POSTING_MAX_CHARS = 1000


def skill_text(name: str, synonyms: Sequence[str] = ()) -> str:
    """Taksonomi tarafı: "ad, eş anlamlı, ..." (ör. "JavaScript, js, ecmascript"). Sorgu tarafı (CV'deki,
    taksonomide olmayan ad: "Express", "Manuel test") sadece adı verir.

    Eş anlamlıları metne katmak, taksonomide olmayan adın doğru yetkinliğe gitme oranını artırıyor (README ölçümü).
    """
    parts = [" ".join(s.split()) for s in (name, *synonyms)]
    return ", ".join(dict.fromkeys(p for p in parts if p))


def posting_text(title: str, description: str) -> str:
    """Başlık + açıklamanın başı. Açıklama veritabanında maskelenmiş haldedir (pii.mask_posting, T-033)."""
    title = " ".join(title.split())
    body = " ".join(description.split())[:POSTING_MAX_CHARS]
    return f"{title}. {body}" if body else title

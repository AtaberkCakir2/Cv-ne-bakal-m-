"""Birebir aynı olmayan ama aynı ilan olan kayıtlar (ör. şirket her ay aynı ilanı küçük değişiklikle yeniden yazar).

Birebir aynı metin içe aktarmada content_hash ile zaten engelleniyor. Burada aynı şirket + aynı pozisyondaki ilanlar
5 kelimelik parçaların (shingle) Jaccard benzerliğiyle karşılaştırılır; eşiği geçen kümelerde en yeni ilan kalır,
diğerleri pasife alınır (silinmez: yanlış eşleşme geri alınabilsin).
"""

import re
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from etl.text import fold

SHINGLE_SIZE = 5
THRESHOLD = 0.9

_WORD = re.compile(r"\w+")


@dataclass(frozen=True)
class DedupItem:
    id: int
    company: str | None
    role: str | None
    posted_at: date | None
    text: str


def shingles(text: str, size: int = SHINGLE_SIZE) -> frozenset[str]:
    words = _WORD.findall(fold(text))
    if len(words) <= size:
        return frozenset({" ".join(words)})
    return frozenset(" ".join(words[i : i + size]) for i in range(len(words) - size + 1))


def jaccard(a: frozenset[str], b: frozenset[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def near_duplicates(items: Iterable[DedupItem], threshold: float = THRESHOLD) -> set[int]:
    """Pasife alınacak ilanların id'leri. Şirketi bilinmeyen ilanlar karşılaştırılmaz."""
    groups: dict[tuple[str, str | None], list[DedupItem]] = defaultdict(list)
    for item in items:
        if item.company:
            groups[(fold(item.company).strip(), item.role)].append(item)

    drop: set[int] = set()
    for group in groups.values():
        # En yeni önce (tarih yoksa en eski sayılır, eşitse büyük id = sonra eklenen).
        group.sort(key=lambda i: (i.posted_at or date.min, i.id), reverse=True)
        kept: list[tuple[DedupItem, frozenset[str]]] = []
        for item in group:
            sh = shingles(item.text)
            if any(jaccard(sh, k) >= threshold for _, k in kept):
                drop.add(item.id)
            else:
                kept.append((item, sh))
    return drop

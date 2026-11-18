"""Embedding servisi (T-041): çok dilli 384 boyutlu vektörler ve pgvector'e toplu yazma.

from embedding import default_encoder, skill_text
vectors = default_encoder()([skill_text("Express")])   # sorgu tarafı (T-042)

python -m embedding               # vektörü olmayan yetkinlik ve ilanlar (DATABASE_URL)
python -m embedding --hepsi       # model değişince tümü
"""

from embedding.model import DEFAULT_MODEL, DIM, Encoder, SentenceEncoder, Vector, check, cosine, default_encoder
from embedding.store import embed_table, to_literal
from embedding.texts import posting_text, skill_text

__all__ = [
    "DEFAULT_MODEL",
    "DIM",
    "Encoder",
    "SentenceEncoder",
    "Vector",
    "check",
    "cosine",
    "default_encoder",
    "embed_table",
    "posting_text",
    "skill_text",
    "to_literal",
]

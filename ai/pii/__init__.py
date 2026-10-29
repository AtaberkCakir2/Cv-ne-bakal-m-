"""CV metnindeki kişisel verilerin maskelenmesi (T-030).

Kullanım: `mask(text, lang)` / `mask_text(text, lang)`; ilan metni için `mask_posting(text, lang)`.
"""

from pii.kinds import PLACEHOLDERS, Kind
from pii.mask import MaskResult, mask, mask_posting, mask_text
from pii.names import NameDetector

__all__ = ["PLACEHOLDERS", "Kind", "MaskResult", "NameDetector", "mask", "mask_posting", "mask_text"]

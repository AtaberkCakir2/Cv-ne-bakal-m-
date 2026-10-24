"""Yüklenen CV'nin doğrulanması: boyut, tür (MIME + magic byte), şifre, sayfa sayısı, SHA-256.

Dosya sadece bellekte işlenir. Hata kodları contracts/analysis_result.schema.json'daki
error.code değerleriyle uyumludur.
"""

import hashlib
import io
from dataclasses import dataclass

from pypdf import PasswordType, PdfReader
from pypdf.errors import PdfReadError

from app.core.uploads import MAX_PDF_BYTES, MAX_PDF_PAGES

ALLOWED_CONTENT_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream"}
PDF_MAGIC = b"%PDF-"


class CvRejected(Exception):
    def __init__(self, status: int, code: str, detail: str) -> None:
        super().__init__(detail)
        self.status = status
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class ValidatedCv:
    content: bytes
    sha256: str
    pages: int


def validate_cv(content: bytes, content_type: str | None) -> ValidatedCv:
    if not content:
        raise CvRejected(422, "PDF_UNREADABLE", "Dosya boş.")
    if len(content) > MAX_PDF_BYTES:
        raise CvRejected(413, "PDF_TOO_LARGE", "Dosya en fazla 5 MB olabilir.")
    # Önce istemcinin bildirdiği tür, sonra dosyanın gerçek imzası (uzantı/MIME kandırılabilir).
    if (content_type or "").split(";")[0].strip().lower() not in ALLOWED_CONTENT_TYPES:
        raise CvRejected(415, "PDF_UNREADABLE", "Sadece PDF dosyası yüklenebilir.")
    if not content.startswith(PDF_MAGIC):
        raise CvRejected(415, "PDF_UNREADABLE", "Sadece PDF dosyası yüklenebilir.")

    try:
        reader = PdfReader(io.BytesIO(content))
        # Sadece "düzenleme kısıtlı" PDF'ler (boş kullanıcı şifresi) açılabilir; onları reddetme.
        # ai/parsing (T-020) da aynı kuralı kullanır: needs_pass and not authenticate("").
        if reader.is_encrypted and reader.decrypt("") == PasswordType.NOT_DECRYPTED:
            raise CvRejected(422, "PDF_UNREADABLE", "Şifreli PDF okunamıyor. Lütfen şifresiz bir kopya yükleyin.")
        pages = len(reader.pages)
    except CvRejected:
        raise
    except (PdfReadError, ValueError, KeyError, TypeError, OSError) as exc:
        raise CvRejected(422, "PDF_UNREADABLE", "PDF dosyası okunamadı; dosya bozuk olabilir.") from exc

    if pages == 0:
        raise CvRejected(422, "PDF_UNREADABLE", "PDF dosyasında sayfa yok.")
    if pages > MAX_PDF_PAGES:
        raise CvRejected(422, "PDF_TOO_LARGE", f"CV en fazla {MAX_PDF_PAGES} sayfa olabilir ({pages} sayfa).")

    return ValidatedCv(content=content, sha256=hashlib.sha256(content).hexdigest(), pages=pages)

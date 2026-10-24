"""PDF ayrıştırma hataları.

Hata kodları contracts/analysis_result.schema.json içindeki `error.code` değerleriyle aynıdır;
kullanıcıya giden mesaj Türkçedir ve CV içeriği veya dosya ayrıntısı içermez.
"""

from enum import StrEnum


class ErrorCode(StrEnum):
    PDF_UNREADABLE = "PDF_UNREADABLE"
    PDF_TOO_LARGE = "PDF_TOO_LARGE"
    NO_TEXT_FOUND = "NO_TEXT_FOUND"


class Reason(StrEnum):
    """Hatanın ayrıntılı sebebi. Loglama ve test içindir; sözleşmede sadece `code` vardır."""

    NOT_PDF = "not_pdf"
    CORRUPT = "corrupt"
    ENCRYPTED = "encrypted"
    TOO_MANY_BYTES = "too_many_bytes"
    TOO_MANY_PAGES = "too_many_pages"
    NO_TEXT = "no_text"


_MESSAGES = {
    Reason.NOT_PDF: "Dosya bir PDF değil. Lütfen CV'nizi PDF olarak yükleyin.",
    Reason.CORRUPT: "PDF dosyası bozuk veya okunamıyor. Dosyayı yeniden kaydedip tekrar deneyin.",
    Reason.ENCRYPTED: "PDF şifreli. Şifresiz bir kopyasını yükleyin.",
    Reason.TOO_MANY_BYTES: "Dosya 5 MB'tan büyük olamaz.",
    Reason.TOO_MANY_PAGES: "CV en fazla 5 sayfa olabilir.",
    Reason.NO_TEXT: "CV'den metin okunamadı. Taranmış bir belgeyse daha net bir kopyasını deneyin.",
}

_CODES = {
    Reason.NOT_PDF: ErrorCode.PDF_UNREADABLE,
    Reason.CORRUPT: ErrorCode.PDF_UNREADABLE,
    Reason.ENCRYPTED: ErrorCode.PDF_UNREADABLE,
    Reason.TOO_MANY_BYTES: ErrorCode.PDF_TOO_LARGE,
    Reason.TOO_MANY_PAGES: ErrorCode.PDF_TOO_LARGE,
    Reason.NO_TEXT: ErrorCode.NO_TEXT_FOUND,
}


class PdfError(Exception):
    def __init__(self, reason: Reason) -> None:
        self.reason = reason
        self.code = _CODES[reason]
        self.message = _MESSAGES[reason]
        super().__init__(f"{self.code} ({reason}): {self.message}")

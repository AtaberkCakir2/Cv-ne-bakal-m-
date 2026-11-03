"""Maskelenen kişisel veri türleri ve metinde yerlerine konan etiketler.

E-posta, telefon ve TCKN etiketleri backend'in log maskelemesiyle (backend/app/core/logging.py) aynıdır.
"""

from enum import StrEnum


class Kind(StrEnum):
    EMAIL = "email"
    PHONE = "phone"
    TCKN = "tckn"
    IBAN = "iban"
    URL = "url"
    BIRTH_DATE = "birth_date"
    ADDRESS = "address"
    NAME = "name"


PLACEHOLDERS: dict[Kind, str] = {
    Kind.EMAIL: "[E-POSTA]",
    Kind.PHONE: "[TELEFON]",
    Kind.TCKN: "[TCKN]",
    Kind.IBAN: "[IBAN]",
    Kind.URL: "[BAĞLANTI]",
    Kind.BIRTH_DATE: "[DOĞUM TARİHİ]",
    Kind.ADDRESS: "[ADRES]",
    Kind.NAME: "[AD SOYAD]",
}

# Çakışan iki bulguda hangisinin etiketi kullanılır (büyük olan kazanır).
PRIORITY: dict[Kind, int] = {
    Kind.EMAIL: 8,
    Kind.IBAN: 7,
    Kind.URL: 6,
    Kind.PHONE: 5,
    Kind.TCKN: 4,
    Kind.BIRTH_DATE: 3,
    Kind.NAME: 2,
    Kind.ADDRESS: 1,
}

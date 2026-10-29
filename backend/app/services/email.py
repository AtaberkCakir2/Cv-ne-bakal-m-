"""E-posta gönderimi.

Gerçek e-posta servisi (işlemsel e-posta sağlayıcısı) henüz seçilmedi. O zamana kadar `OutboxEmailSender`
iletileri bellekte tutar; testler ve test kullanıcısı betiği bağlantıları buradan okur. Sadece `local`
ortamında bağlantı loga da yazılır (geliştirici e-postayı tıklayabilsin diye); başka ortamda asla.
"""

import logging
from dataclasses import dataclass
from typing import Protocol

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EmailMessage:
    to: str
    subject: str
    body: str
    link: str


class EmailSender(Protocol):
    def send(self, message: EmailMessage) -> None: ...


class OutboxEmailSender:
    def __init__(self, *, log_links: bool = False) -> None:
        self.outbox: list[EmailMessage] = []
        self._log_links = log_links

    def send(self, message: EmailMessage) -> None:
        self.outbox.append(message)
        if self._log_links:
            # Alıcı adresi log maskeleme filtresinden geçer; bağlantı sadece local ortamda yazılır.
            logger.info("E-posta (outbox, sadece local): %s → %s", message.subject, message.link)
        else:
            logger.info("E-posta outbox'a eklendi: %s", message.subject)

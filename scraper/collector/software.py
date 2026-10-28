"""Yazılım ilanı mı? Tüm kategorileri karışık veren kaynaklar (Remote OK, EMSCAD) için başlık süzgeci."""

import re

_SOFTWARE_TITLE = re.compile(
    r"\b(developer|software|engineer|engineering|programmer|devops|sre|data scien\w*|data analyst|ml|ai"
    r"|frontend|front-end|backend|back-end|full[ -]?stack|qa|tester|architect|mobile|ios|android)\b",
    re.IGNORECASE,
)
# "Sales Engineer", "Mechanical Engineer" gibi yazılım dışı mühendislikler.
_NOT_SOFTWARE = re.compile(
    r"\b(sales|account|mechanical|civil|electrical|chemical|structural|field service|hvac|marketing)\b", re.IGNORECASE
)


def is_software_title(title: str) -> bool:
    return bool(_SOFTWARE_TITLE.search(title)) and not _NOT_SOFTWARE.search(title)

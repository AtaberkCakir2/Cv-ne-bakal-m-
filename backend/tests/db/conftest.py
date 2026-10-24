import importlib.util

# DB bağımlılıkları kurulu değilse bu klasör hiç toplanmaz (import hatasıyla tüm pytest çökmesin).
_DB_PACKAGES = ("sqlalchemy", "alembic", "pgvector")
if not all(importlib.util.find_spec(pkg) for pkg in _DB_PACKAGES):
    collect_ignore_glob = ["test_*.py"]

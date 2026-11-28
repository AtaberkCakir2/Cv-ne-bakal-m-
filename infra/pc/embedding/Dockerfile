# Geçici (T-057 gelene kadar): production'da yetkinlik ve ilan vektörlerini üretmek için tek seferlik imaj.
# Kod ai/embedding (Burak); kullanımı infra/pc/deploy.md "7. Vektörler". Bağlam: ai/ klasörü.
FROM python:3.12-slim
ENV PIP_NO_CACHE_DIR=1 PYTHONUNBUFFERED=1 HF_HOME=/models
RUN pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu
COPY . /ai
RUN pip install "/ai[embedding]"
WORKDIR /ai
# Modeli imaja indir (çalışırken internete gerek kalmasın, boyut kontrolü burada yapılsın).
RUN python -c "from embedding.model import SentenceEncoder; SentenceEncoder()"
# Çalışırken Hugging Face'a gitmesin: model imajın içinde.
ENV HF_HUB_OFFLINE=1

# CareerAI analiz işçisi (worker-ai, T-057): backend'in Celery işçisi (app.worker, Anıl) + ai paketi (Burak).
# İşçi kodu backend'de, taksonomi scraper'da olduğu için bağlam repo kökü:  docker build -f ai/Dockerfile .
# (scraper/Dockerfile ile aynı düzen; .dockerignore ai/eval ve ai/tests'i dışarıda bırakır.)
FROM python:3.12-slim

# Taban imajdaki Debian paketlerinin güvenlik yamaları (backend/ ve scraper/Dockerfile ile aynı, G-4).
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/*

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    # Modeller imaja gömülür (aşağıda); çalışırken internete çıkılmaz, sürüm imajla sabit kalır.
    HF_HOME=/opt/hf \
    TOKENIZERS_PARALLELISM=false \
    # Paket site-packages'ta değil /srv/ai'de (editable), ama yol yine de açıkça verilir.
    CAREERAI_TAXONOMY=/srv/scraper/taxonomy/skills.csv

WORKDIR /srv

# 1) torch'un CPU sürümü (CUDA'lı sürüm ~2 GB fazla; işçide GPU yok, LLM Ollama'da). Sürüm ai/pyproject.toml ile aynı.
RUN pip install torch==2.15.0 --index-url https://download.pytorch.org/whl/cpu

# 2) Bağımlılıklar: kod değişince bu katman yeniden kurulmaz. Editable kurulum paket klasörlerini kurulum anında
#    eşler; o yüzden ai'nin bütün paketleri (pyproject.toml'daki include listesi) boş olarak açılır.
COPY backend/pyproject.toml backend/
COPY ai/pyproject.toml ai/
RUN mkdir -p backend/app \
    && touch backend/app/__init__.py \
    && for p in parsing pii extraction prompts embedding matching recommendation pipeline; do \
         mkdir -p "ai/$p" && touch "ai/$p/__init__.py"; \
       done \
    && pip install -e backend -e "ai[ner,embedding]"

# 3) Modeller (NER: pii/ner.py, revizyon sabit; embedding: embedding/model.py). Çalışırken HF_HUB_OFFLINE=1.
RUN python -c "\
from huggingface_hub import snapshot_download; \
snapshot_download('akdeniz27/bert-base-turkish-cased-ner', revision='99995f7d2be4b3a28c74f0d36ee97f8c04ee0571'); \
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('intfloat/multilingual-e5-small', device='cpu')"

# 4) Kod
COPY backend/app backend/app
COPY ai/parsing ai/parsing
COPY ai/pii ai/pii
COPY ai/extraction ai/extraction
COPY ai/prompts ai/prompts
COPY ai/embedding ai/embedding
COPY ai/matching ai/matching
COPY ai/recommendation ai/recommendation
COPY ai/pipeline ai/pipeline
COPY scraper/taxonomy scraper/taxonomy

# Model adları kodla imajdakiyle aynı mı, pipeline içe aktarılıyor mu (build'de yakalansın).
RUN python -c "\
from pii.ner import MODEL_ID, MODEL_REVISION; \
from embedding.model import DEFAULT_MODEL; \
assert (MODEL_ID, MODEL_REVISION) == ('akdeniz27/bert-base-turkish-cased-ner', '99995f7d2be4b3a28c74f0d36ee97f8c04ee0571'), MODEL_ID; \
assert DEFAULT_MODEL == 'intfloat/multilingual-e5-small', DEFAULT_MODEL; \
import pipeline, app.worker.tasks; \
from app.services.analyzer import pipeline_available; assert pipeline_available()"

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# Root olmayan kullanıcı. CV dosyası diske yazılmaz (karar #9); yazılabilir klasör gerekmez.
RUN useradd --create-home --uid 10001 careerai
USER careerai
WORKDIR /srv/backend

HEALTHCHECK --interval=30s --timeout=15s --start-period=60s --retries=3 \
    CMD celery -A app.worker.celery_app inspect ping -d "analysis@$HOSTNAME" --timeout 5 || exit 1

# Eşzamanlılık 1 (RAM: NER ~760 MB + embedding ~470 MB + PDF; T-057 kabul kriteri). -E kullanılmaz (docker-compose.yml
# worker-analysis notu). OLLAMA_URL / OLLAMA_MODEL ortamdan okunur (#173).
CMD ["celery", "-A", "app.worker.celery_app", "worker", "-Q", "analysis", "--concurrency", "1", \
     "-n", "analysis@%h", "--loglevel", "INFO"]

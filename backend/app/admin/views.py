"""Panel ekranları (T-063 kabul kriteri): kaynak ekle/düzenle, ilan kaynağı aç/kapa, toplama çalışmaları, istatistik."""

from typing import Any
from urllib.parse import urlsplit

from sqladmin import BaseView, ModelView, expose
from sqladmin.filters import ForeignKeyFilter, StaticValuesFilter
from starlette.concurrency import run_in_threadpool
from starlette.requests import Request
from starlette.responses import Response

from app.admin import stats
from app.admin.formatting import ANALYSIS_STATUS_TR, dt_column, fmt_dt
from app.db.enums import ScrapeStatus
from app.db.models import JobSource, Resource, ScrapeRun


class StatsView(BaseView):
    name = "İstatistikler"
    icon = "fa-solid fa-chart-line"

    @expose("/istatistik", methods=["GET"])
    async def page(self, request: Request) -> Response:
        def _collect() -> stats.Stats:
            with self._admin_ref.session_maker() as session:
                return stats.collect(session)

        data = await run_in_threadpool(_collect)
        return await self.templates.TemplateResponse(
            request,
            "admin_stats.html",
            {
                "s": data,
                "min_resources": stats.MIN_RESOURCES_PER_SKILL,
                "fmt_dt": fmt_dt,
                "status_tr": ANALYSIS_STATUS_TR,
            },
        )


class ResourceAdmin(ModelView, model=Resource):
    """Eğitim kaynakları. Öneri linkleri sadece buradan gelir (karar #10); elle eklenen her link de bu tablodadır."""

    name = "Kaynak"
    name_plural = "Kaynaklar"
    icon = "fa-solid fa-book"

    # Silme yok: geçmiş analizlerin önerileri kaynağa bağlı. Yayından kaldırmak için "is_alive" kapatılır.
    can_delete = False
    column_list = [
        Resource.id,
        Resource.title,
        Resource.skill,
        Resource.provider,
        Resource.language,
        Resource.level,
        Resource.is_free,
        Resource.is_alive,
    ]
    column_searchable_list = [Resource.title, Resource.url]
    column_sortable_list = [Resource.id, Resource.title, Resource.provider, Resource.is_alive]
    column_default_sort = [(Resource.id, True)]
    form_columns = [
        Resource.skill,
        Resource.title,
        Resource.url,
        Resource.provider,
        Resource.language,
        Resource.level,
        Resource.duration_min,
        Resource.is_free,
        Resource.is_alive,
    ]
    # 374 yetkinlik: açılır liste yerine aramalı seçim.
    form_ajax_refs = {"skill": {"fields": ("canonical_name", "slug"), "order_by": "canonical_name"}}
    form_args = {"is_alive": {"default": True}}
    column_labels = {
        Resource.skill: "Yetkinlik",
        Resource.title: "Başlık",
        Resource.provider: "Sağlayıcı",
        Resource.language: "Dil",
        Resource.level: "Seviye",
        Resource.duration_min: "Süre (dk)",
        Resource.is_free: "Ücretsiz",
        Resource.is_alive: "Yayında",
    }

    async def on_model_change(self, data: dict[str, Any], model: Any, is_created: bool, request: Request) -> None:
        url = str(data.get("url") or "").strip()
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.netloc:
            raise ValueError("Bağlantı https:// ile başlayan tam bir adres olmalı.")
        data["url"] = url
        data["title"] = str(data.get("title") or "").strip()
        if not data["title"]:
            raise ValueError("Başlık boş olamaz.")


class JobSourceAdmin(ModelView, model=JobSource):
    """İlan kaynakları. Sadece aç/kapa ve istek aralığı değişir; yeni kaynak kod ve uygunluk incelemesiyle eklenir."""

    name = "İlan kaynağı"
    name_plural = "İlan kaynakları"
    icon = "fa-solid fa-satellite-dish"

    can_create = False
    can_delete = False  # silmek ilanları da siler (ON DELETE CASCADE)
    column_list = [
        JobSource.name,
        JobSource.type,
        JobSource.is_active,
        JobSource.tos_checked,
        JobSource.rate_limit_sec,
        JobSource.base_url,
    ]
    column_default_sort = [(JobSource.name, False)]
    form_columns = [JobSource.is_active, JobSource.rate_limit_sec]
    column_labels = {
        JobSource.name: "Ad",
        JobSource.type: "Tür",
        JobSource.is_active: "Açık",
        JobSource.tos_checked: "Şartlar incelendi",
        JobSource.rate_limit_sec: "İstek aralığı (sn)",
        JobSource.base_url: "Adres",
    }

    async def on_model_change(self, data: dict[str, Any], model: Any, is_created: bool, request: Request) -> None:
        # scraper/kaynak-uygunluk.md: sadece kullanım şartları incelenmiş (✅) kaynak açılır.
        if data.get("is_active") and not model.tos_checked:
            raise ValueError(
                "Kullanım şartları incelenmemiş kaynak açılamaz (scraper/kaynak-uygunluk.md, tos_checked)."
            )
        # Sütun numeric(4,1): 0 (veri seti, istek yok) ile 999.9 arası. Sınırı kaynağın şartları belirler.
        rate = data.get("rate_limit_sec")
        if rate is None or not 0 <= rate < 1000:
            raise ValueError("İstek aralığı 0 ile 999.9 saniye arasında olmalı.")


class ScrapeRunAdmin(ModelView, model=ScrapeRun):
    """Gece toplama çalışmaları: sadece izleme."""

    name = "Toplama çalışması"
    name_plural = "Toplama çalışmaları"
    icon = "fa-solid fa-clock-rotate-left"

    can_create = False
    can_edit = False
    can_delete = False
    column_list = [
        ScrapeRun.id,
        ScrapeRun.source,
        ScrapeRun.started_at,
        ScrapeRun.finished_at,
        ScrapeRun.status,
        ScrapeRun.fetched,
        ScrapeRun.inserted,
        ScrapeRun.duplicates,
        ScrapeRun.errors,
    ]
    column_details_list = [*column_list, ScrapeRun.error_log]
    column_sortable_list = [ScrapeRun.id, ScrapeRun.started_at, ScrapeRun.status, ScrapeRun.errors]
    column_default_sort = [(ScrapeRun.started_at, True)]
    column_formatters = {ScrapeRun.started_at: dt_column, ScrapeRun.finished_at: dt_column}
    column_formatters_detail = column_formatters
    column_filters = [
        StaticValuesFilter(ScrapeRun.status, [(s.value, s.value) for s in ScrapeStatus], title="Durum"),
        ForeignKeyFilter(ScrapeRun.source_id, JobSource.name, JobSource, title="Kaynak"),
    ]
    column_labels = {
        ScrapeRun.source: "Kaynak",
        ScrapeRun.started_at: "Başlangıç",
        ScrapeRun.finished_at: "Bitiş",
        ScrapeRun.status: "Durum",
        ScrapeRun.fetched: "Çekilen",
        ScrapeRun.inserted: "Eklenen",
        ScrapeRun.duplicates: "Tekrar",
        ScrapeRun.errors: "Hata",
        ScrapeRun.error_log: "Hata kaydı",
    }

import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { ResultDashboard } from "../analysis/ResultDashboard";
import { api, problemMessage, unwrap, type Problem } from "../api/client";
import type { components } from "../api/schema";
import { Alert, Card, Spinner } from "../ui";

type Analysis = components["schemas"]["AnalysisOut"];

const POLL_MS = 3000;
/** İş başına en fazla 180 sn × 2 deneme ve kuyruk (T-039); bunu geçerse kullanıcıya bilgi verilir, yoklama sürer. */
const SLOW_AFTER_S = 7 * 60;

const STEPS = [
  { status: "queued", label: "Sırada" },
  { status: "processing", label: "Analiz ediliyor" },
  { status: "done", label: "Tamamlandı" },
] as const;

const ERROR_HINTS: Partial<Record<string, string>> = {
  PDF_UNREADABLE: "Dosyayı yeniden PDF olarak kaydedip tekrar dene.",
  NO_TEXT_FOUND: "Taranmış (resim) bir CV olabilir; metni seçilebilen bir PDF dene.",
  LLM_TIMEOUT: "Sistem şu an yoğun. Birkaç dakika sonra tekrar dene.",
};

/** T-052: analiz bekleme ekranı. Bitmemiş analiz 3 sn'de bir yoklanır; bitince sonuç panosu (T-053). */
export function AnalysisPage() {
  const { id = "" } = useParams();
  const analysis = useQuery({
    queryKey: ["analysis", id],
    queryFn: async () =>
      unwrap(await api.GET("/api/v1/analyses/{analysis_id}", { params: { path: { analysis_id: id } } })),
    refetchInterval: (query) => (isUnfinished(query.state.data) ? POLL_MS : false),
  });

  if (analysis.isPending) return <Spinner label="Analiz yükleniyor" />;
  // Yoklamada geçici bir hata eldeki veriyi silmez: bekleme ekranı kalır, sonraki yoklama düzeltir.
  if (analysis.isError && !analysis.data) {
    const status = (analysis.error as Partial<Problem>).status;
    const notFound = status === 404 || status === 422; // 422: adres geçerli bir analiz kimliği değil
    return (
      <Card title={notFound ? "Analiz bulunamadı" : "Analiz açılamadı"} headingLevel={1} className="narrow-card">
        <Alert tone="error">{notFound ? "Bu analiz yok ya da silinmiş." : problemMessage(analysis.error)}</Alert>
        <Link to="/yukle">Yeni analiz başlat</Link>
      </Card>
    );
  }

  const data = analysis.data;
  if (data.status === "failed") return <Failed data={data} />;
  if (data.status === "done") return <ResultDashboard data={data} />;
  return <Waiting data={data} />;
}

function isUnfinished(data: Analysis | undefined): boolean {
  return data?.status === "queued" || data?.status === "processing";
}

function Waiting({ data }: { data: Analysis }) {
  const elapsed = useElapsedSeconds(data.created_at);
  const current = STEPS.findIndex((s) => s.status === data.status);
  return (
    <Card title="CV'n analiz ediliyor" headingLevel={1} className="narrow-card">
      <p className="muted">
        Hedef pozisyon: <strong>{data.target_role.name}</strong>. Bu işlem genelde 1-2 dakika sürer; sayfayı
        kapatabilirsin, sonuç Geçmiş'te olur.
      </p>
      {/* Durum değişince ekran okuyucu okusun (metin değişir); süre sayacı bu bölgenin dışında. */}
      <p className="visually-hidden" role="status">
        Durum: {STEPS[current]?.label}
      </p>
      <ol className="steps">
        {STEPS.map((step, i) => (
          <li
            key={step.status}
            className={i < current ? "steps__item--done" : i === current ? "steps__item--now" : undefined}
            aria-current={i === current ? "step" : undefined}
          >
            {step.label}
            {i === current && <Spinner label="" />}
          </li>
        ))}
      </ol>
      <p className="muted" aria-hidden="true">
        Geçen süre: {formatElapsed(elapsed)}
      </p>
      {elapsed > SLOW_AFTER_S && (
        <Alert tone="warning">
          Analiz beklenenden uzun sürüyor. Beklemeye devam edebilir ya da daha sonra Geçmiş'ten bakabilirsin.
        </Alert>
      )}
    </Card>
  );
}

function Failed({ data }: { data: Analysis }) {
  const code = data.error?.code;
  return (
    <Card title="Analiz tamamlanamadı" headingLevel={1} className="narrow-card" focusTitle>
      <Alert tone="error">{data.error?.message ?? "Analiz tamamlanamadı. Lütfen tekrar deneyin."}</Alert>
      {code && ERROR_HINTS[code] && <p>{ERROR_HINTS[code]}</p>}
      <Link className="btn btn--block" to="/yukle">
        Tekrar dene
      </Link>
    </Card>
  );
}

function useElapsedSeconds(since: string): number {
  const start = Date.parse(since);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  return Number.isFinite(start) ? Math.max(0, Math.floor((now - start) / 1000)) : 0;
}

function formatElapsed(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return m ? `${m} dk ${s} sn` : `${s} sn`;
}

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useId, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, problemMessage, unwrap } from "../api/client";
import type { components } from "../api/schema";
import { Alert, Button, Card, Chip, DemandBars, Dialog, ScoreGauge, StarRating } from "../ui";
import { isWebUrl, percentOf } from "./format";
import { SourceAttribution } from "./SourceAttribution";

type Analysis = components["schemas"]["AnalysisOut"];
type MissingSkill = components["schemas"]["MissingSkillOut"];
type Resource = components["schemas"]["ResourceOut"];

/** İlan sayısı bunun altındaysa oranlar daha az güvenilir (risk R-11). */
const LOW_DATA_POSTINGS = 50;
const MAX_COMMENT = 1000;

const LEVEL: Record<string, string> = {
  beginner: "başlangıç",
  intermediate: "orta",
  advanced: "ileri",
  unknown: "seviye belirsiz",
};
const PROVIDER: Record<string, string> = {
  youtube: "YouTube",
  udemy: "Udemy",
  coursera: "Coursera",
  btk_akademi: "BTK Akademi",
  docs: "Dokümantasyon",
  blog: "Blog",
  other: "Diğer",
};
const LANGUAGE: Record<string, string> = { tr: "Türkçe", en: "İngilizce" };

/** "150 ilanın %75'i" — ilan sayısı bilinmiyorsa "ilanların %75'i". */
function demandText(ratio: number, postings: number | null | undefined): string {
  return postings ? `${postings} ilanın ${percentOf(ratio)} istiyor` : `ilanların ${percentOf(ratio)} istiyor`;
}

/** T-053: tamamlanmış analizin sonuç panosu. */
export function ResultDashboard({ data }: { data: Analysis }) {
  const [open, setOpen] = useState<{ resource: Resource; skill: MissingSkill }>();
  // Bekleme ekranından gelindiğinde içerik değişti: odak ve ekran okuyucu başlıktan başlasın.
  const titleRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => titleRef.current?.focus(), []);
  const present = data.present_skills ?? [];
  const missing = [...(data.missing_skills ?? [])].sort((a, b) => a.priority - b.priority);
  const postings = data.postings_analyzed;
  const hasYoutube = missing.some((m) => m.resources.some((r) => r.provider === "youtube"));
  const date = data.completed_at ?? data.created_at;

  return (
    <div className="stack result">
      <Card className="result__head">
        {data.match_score != null && <ScoreGauge score={data.match_score} />}
        <div>
          <h1 ref={titleRef} tabIndex={-1}>
            {data.match_score != null ? `${data.target_role.name} için uyumun` : `${data.target_role.name} analizi`}
          </h1>
          <p className="muted">
            {postings != null && `${postings} güncel ilanla karşılaştırıldı · `}
            {new Date(date).toLocaleDateString("tr-TR", { day: "numeric", month: "long", year: "numeric" })}
          </p>
        </div>
      </Card>

      {postings != null && postings < LOW_DATA_POSTINGS && (
        <Alert tone="warning">
          Bu pozisyon için sadece {postings} güncel ilan var; oranlar daha az güvenilir.
        </Alert>
      )}

      <div className="result__cols">
        <Card title={`CV'nde bulunanlar (${present.length})`}>
          {present.length ? (
            <ul className="chip-list">
              {present.map((s) => (
                <li key={s.skill}>
                  <Chip meta={s.verified === false ? `${LEVEL[s.level]} · tahmini` : LEVEL[s.level]}>{s.skill}</Chip>
                </li>
              ))}
            </ul>
          ) : (
            <p className="muted">CV'nde bu pozisyonla ilgili yetkinlik bulunamadı.</p>
          )}
          {present.some((s) => s.verified === false) && (
            <p className="muted result__note">"Tahmini" yetkinlikler taksonomide yok; yapay zekânın çıkarımıdır.</p>
          )}
        </Card>

        <Card title={`Eksik yetkinlikler (${missing.length})`}>
          {missing.length ? (
            <>
              <p className="muted">Önem sırasına göre; çubuk, bu yetkinliği isteyen ilanların oranı.</p>
              <DemandBars
                caption="Eksik yetkinliklerin ilanlardaki talep oranı"
                items={missing.map((m) => ({ label: m.skill, ratio: m.demand_ratio }))}
              />
            </>
          ) : (
            <p className="muted">Bu pozisyonun öne çıkan yetkinliklerinin hepsi CV'nde var.</p>
          )}
        </Card>
      </div>

      {missing.length > 0 && (
        <Card title="Eksiklerini kapatmak için kaynaklar">
          <ol className="gaps">
            {missing.map((m) => (
              <li key={m.skill} className="gaps__item">
                <h3 className="gaps__title">
                  {m.priority}. {m.skill} <span className="muted">· {demandText(m.demand_ratio, postings)}</span>
                </h3>
                {m.resources.length ? (
                  <ul className="resources">
                    {m.resources.map((r) => (
                      <li key={r.resource_id}>
                        <button type="button" className="resource" onClick={() => setOpen({ resource: r, skill: m })}>
                          <span className="resource__provider">{PROVIDER[r.provider]}</span>
                          <span className="resource__title">{r.title}</span>
                          <span className="resource__meta">{resourceMeta(r)}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="muted">Bu yetkinlik için henüz önerilecek kaynak yok.</p>
                )}
              </li>
            ))}
          </ol>
        </Card>
      )}

      <FeedbackCard analysisId={data.analysis_id} saved={data.feedback ?? undefined} />

      <p>
        <Link to="/yukle">Yeni analiz başlat</Link> · <Link to="/gecmis">Geçmiş analizler</Link>
      </p>
      <SourceAttribution youtube={hasYoutube} />

      <Dialog open={Boolean(open)} title={open?.resource.title} onClose={() => setOpen(undefined)}>
        {open && <ResourceDetail resource={open.resource} skill={open.skill} postings={postings} />}
        <div className="row">
          {open && isWebUrl(open.resource.url) && (
            <a className="btn" href={open.resource.url} target="_blank" rel="noopener noreferrer">
              Kaynağa git <span aria-hidden="true">↗</span>
              <span className="visually-hidden"> (yeni sekmede açılır)</span>
            </a>
          )}
          <Button variant="secondary" onClick={() => setOpen(undefined)}>
            Kapat
          </Button>
        </div>
      </Dialog>
    </div>
  );
}

function resourceMeta(r: Resource): string {
  return [
    LEVEL[r.level],
    r.duration_min != null && `${r.duration_min} dk`,
    r.is_free ? "ücretsiz" : "ücretli",
    r.language && LANGUAGE[r.language],
  ]
    .filter(Boolean)
    .join(" · ");
}

function ResourceDetail({
  resource,
  skill,
  postings,
}: {
  resource: Resource;
  skill: MissingSkill;
  postings: number | null | undefined;
}) {
  return (
    <>
      <dl className="details">
        <dt>Yetkinlik</dt>
        <dd>
          {skill.skill} ({demandText(skill.demand_ratio, postings)})
        </dd>
        <dt>Sağlayıcı</dt>
        <dd>{PROVIDER[resource.provider]}</dd>
        <dt>Seviye</dt>
        <dd>{LEVEL[resource.level]}</dd>
        {resource.duration_min != null && (
          <>
            <dt>Süre</dt>
            <dd>{resource.duration_min} dk</dd>
          </>
        )}
        {resource.language && (
          <>
            <dt>Dil</dt>
            <dd>{LANGUAGE[resource.language]}</dd>
          </>
        )}
        <dt>Ücret</dt>
        <dd>{resource.is_free ? "Ücretsiz" : "Ücretli"}</dd>
      </dl>
      {resource.reason && (
        <p className="dialog__reason">
          <strong>Neden önerildi?</strong> {resource.reason}
        </p>
      )}
    </>
  );
}

function FeedbackCard({ analysisId, saved }: { analysisId: string; saved?: { rating: number; comment?: string | null } }) {
  const queryClient = useQueryClient();
  const commentId = useId();
  const [rating, setRating] = useState<number | undefined>(saved?.rating);
  const [comment, setComment] = useState(saved?.comment ?? "");
  const [error, setError] = useState<string>();
  const [editing, setEditing] = useState(!saved);
  // Form ↔ "Değiştir" geçişinde odak kaybolmasın (ilk çizimde dokunulmaz).
  const cardRef = useRef<HTMLDivElement>(null);
  const previous = useRef(editing);
  useEffect(() => {
    if (previous.current === editing) return; // StrictMode'un çift çalıştırmasında da değişmeyen durumda dokunma
    previous.current = editing;
    const card = cardRef.current;
    const target = editing ? (card?.querySelector("form input:checked") ?? card?.querySelector("form input")) : card?.querySelector("button");
    (target as HTMLElement | null | undefined)?.focus();
  }, [editing]);

  const send = useMutation({
    mutationFn: async (body: { rating: number; comment: string | null }) =>
      unwrap(
        await api.POST("/api/v1/analyses/{analysis_id}/feedback", {
          params: { path: { analysis_id: analysisId } },
          body,
        }),
      ),
    onSuccess: (result) => {
      setEditing(false);
      queryClient.setQueryData<Analysis>(["analysis", analysisId], (old) => old && { ...old, feedback: result });
    },
    onError: (e) => setError(problemMessage(e)),
  });

  function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(undefined);
    if (!rating) {
      setError("Puan için 1 ile 5 arasında bir yıldız seç.");
      return;
    }
    send.mutate({ rating, comment: comment.trim() || null });
  }

  return (
    <Card title="Bu analiz işine yaradı mı?">
      {/* Kaydedildi mesajı sonradan çıkıyor: bölge baştan sayfada (Alert live kuralı). */}
      <div role="status">{!editing && <p>Teşekkürler, geri bildirimin kaydedildi ({rating} / 5).</p>}</div>
      <div ref={cardRef}>
      {editing ? (
        <form onSubmit={submit} noValidate>
          {error && <Alert tone="error">{error}</Alert>}
          <StarRating value={rating} onChange={setRating} legend="Puanın" disabled={send.isPending} />
          <div className="field">
            <label className="field__label" htmlFor={commentId}>
              Yorum (isteğe bağlı)
            </label>
            <textarea
              id={commentId}
              className="field__input"
              rows={3}
              maxLength={MAX_COMMENT}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              disabled={send.isPending}
            />
            <span className="field__hint">Kişisel bilgi yazma; yorumun sadece ürünü geliştirmek için okunur.</span>
          </div>
          <Button type="submit" loading={send.isPending}>
            Gönder
          </Button>
        </form>
      ) : (
        <Button variant="secondary" onClick={() => setEditing(true)}>
          Değiştir
        </Button>
      )}
      </div>
    </Card>
  );
}

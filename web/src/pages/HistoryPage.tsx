import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { Link } from "react-router-dom";

import { api, problemMessage, unwrap } from "../api/client";
import type { components } from "../api/schema";
import { Alert, Button, Card, Dialog, Spinner } from "../ui";

type Summary = components["schemas"]["AnalysisSummaryOut"];

const PAGE = 20;
const STATUS: Record<Summary["status"], string> = {
  queued: "sırada",
  processing: "analiz ediliyor",
  done: "tamamlandı",
  failed: "tamamlanamadı",
};

/** T-053: geçmiş analizler. Yeniden eskiye, 20'şer; silme onay penceresiyle. */
export function HistoryPage() {
  const queryClient = useQueryClient();
  const [toDelete, setToDelete] = useState<Summary>();
  const [notice, setNotice] = useState<string>();
  const noticeRef = useRef<HTMLParagraphElement>(null);

  const history = useInfiniteQuery({
    queryKey: ["analyses"],
    initialPageParam: 0,
    queryFn: async ({ pageParam }) =>
      unwrap(await api.GET("/api/v1/analyses", { params: { query: { limit: PAGE, offset: pageParam } } })),
    getNextPageParam: (last, pages) => {
      const loaded = pages.reduce((n, p) => n + p.items.length, 0);
      return loaded < last.total ? loaded : undefined;
    },
  });

  const remove = useMutation({
    mutationFn: async (id: string) => {
      const { error, response } = await api.DELETE("/api/v1/analyses/{analysis_id}", {
        params: { path: { analysis_id: id } },
      });
      if (!response.ok && response.status !== 404) throw error; // 404: zaten silinmiş, listeden kalksın
    },
    onSuccess: (_, id) => {
      setToDelete(undefined);
      setNotice("Analiz silindi.");
      // Pencere odağı "Sil" düğmesine geri verir, ama o satır birazdan listeden kalkar: odak bildirime gelsin.
      requestAnimationFrame(() => noticeRef.current?.focus());
      queryClient.removeQueries({ queryKey: ["analysis", id] });
      void queryClient.invalidateQueries({ queryKey: ["analyses"] });
    },
  });

  if (history.isPending) return <Spinner label="Geçmiş yükleniyor" />;
  if (history.isError) return <Alert tone="error">{problemMessage(history.error)}</Alert>;

  const items = history.data.pages.flatMap((p) => p.items);
  return (
    <Card title="Geçmiş analizler" headingLevel={1}>
      <div role="status">
        {notice && (
          <p ref={noticeRef} tabIndex={-1}>
            {notice}
          </p>
        )}
      </div>
      {items.length === 0 ? (
        <>
          <p className="muted">Henüz analizin yok.</p>
          <Link className="btn" to="/yukle">
            İlk analizini yap
          </Link>
        </>
      ) : (
        <>
          {/* Dar ekranda yatay kaydırılabilir; klavyeyle de kaydırılabilsin diye odaklanabilir bölge. */}
          <div className="table-wrap" tabIndex={0} role="region" aria-label="Geçmiş analizler tablosu">
            <table className="history">
              <caption className="visually-hidden">
                Analizlerin, yeniden eskiye ({history.data.pages[0].total} analiz)
              </caption>
              <thead>
                <tr>
                  <th scope="col">Tarih</th>
                  <th scope="col">Pozisyon</th>
                  <th scope="col">Uyum</th>
                  <th scope="col">
                    <span className="visually-hidden">İşlemler</span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {items.map((a) => (
                  <tr key={a.analysis_id}>
                    <td>{formatDate(a.created_at)}</td>
                    <td>{a.target_role.name}</td>
                    <td>{a.status === "done" && a.match_score != null ? `${Math.round(a.match_score)} / 100` : STATUS[a.status]}</td>
                    <td>
                      <div className="history__actions">
                      {a.status === "failed" ? (
                        <Link to="/yukle" aria-label={`${formatDate(a.created_at)} ${a.target_role.name} analizini tekrar dene`}>
                          Tekrar dene
                        </Link>
                      ) : (
                        <Link to={`/analiz/${a.analysis_id}`} aria-label={`${formatDate(a.created_at)} ${a.target_role.name} analizini aç`}>
                          Aç
                        </Link>
                      )}
                      <button
                        type="button"
                        className="link-button"
                        onClick={() => {
                          remove.reset();
                          setNotice(undefined);
                          setToDelete(a);
                        }}
                        aria-label={`${formatDate(a.created_at)} ${a.target_role.name} analizini sil`}
                      >
                        Sil
                      </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {history.hasNextPage && (
            <Button variant="secondary" loading={history.isFetchingNextPage} onClick={() => void history.fetchNextPage()}>
              Daha fazla göster
            </Button>
          )}
        </>
      )}

      <Dialog open={Boolean(toDelete)} title="Analizi sil" onClose={() => setToDelete(undefined)}>
        {toDelete && (
          <p>
            {formatDate(toDelete.created_at)} tarihli <strong>{toDelete.target_role.name}</strong> analizi silinecek. Bu
            işlem geri alınamaz.
          </p>
        )}
        {remove.isError && <Alert tone="error">{problemMessage(remove.error)}</Alert>}
        <div className="row">
          <Button variant="danger" loading={remove.isPending} onClick={() => toDelete && remove.mutate(toDelete.analysis_id)}>
            Sil
          </Button>
          <Button variant="secondary" onClick={() => setToDelete(undefined)}>
            Vazgeç
          </Button>
        </div>
      </Dialog>
    </Card>
  );
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("tr-TR", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
}

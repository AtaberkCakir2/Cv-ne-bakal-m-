import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

/** Backend ve bağımlılıklarının durumu. Tipli istemcinin ve veri çekme katmanının uçtan uca örneği. */
export function StatusPage() {
  const health = useQuery({
    queryKey: ["health", "ready"],
    queryFn: async () => {
      // 503 de anlamlı bir yanıt (bağımlılık kapalı); gövdeyi her iki durumda da göster.
      const { data, error, response } = await api.GET("/api/v1/health/ready");
      return { status: response.status, body: data ?? error };
    },
    refetchInterval: 10_000,
  });

  return (
    <section>
      <h1>Sistem durumu</h1>
      {health.isPending && <p>Kontrol ediliyor…</p>}
      {health.isError && <p role="alert">Backend'e ulaşılamadı. `uvicorn app.main:app` çalışıyor mu?</p>}
      {health.data && (
        <>
          <p>
            API: <strong>{health.data.status === 200 ? "hazır" : "hazır değil"}</strong> (HTTP {health.data.status})
          </p>
          <ul>
            {Object.entries(health.data.body?.checks ?? {}).map(
              ([name, check]) => (
                <li key={name}>
                  {name}: {check.ok ? "✓" : `✗ ${check.error ?? ""}`}
                </li>
              ),
            )}
          </ul>
        </>
      )}
    </section>
  );
}

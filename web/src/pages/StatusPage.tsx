import { useQuery } from "@tanstack/react-query";

import { api } from "../api/client";

/** Backend ve bağımlılıklarının durumu. Tipli istemcinin ve veri çekme katmanının uçtan uca örneği. */
export function StatusPage() {
  const health = useQuery({
    queryKey: ["health", "ready"],
    queryFn: async () => {
      // 503 de anlamlı bir yanıt (bağımlılık kapalı), gövdesi aynı. 429'da gövde Problem'dir, kontrol listesi yoktur.
      const { data, error, response } = await api.GET("/api/v1/health/ready");
      const checks = data?.checks ?? (error && "checks" in error ? error.checks : undefined);
      return { status: response.status, checks };
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
            {Object.entries(health.data.checks ?? {}).map(
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

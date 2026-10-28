import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";

import { api, problemMessage } from "../../api/client";
import { useLinkToken } from "../../auth/useLinkToken";
import { Alert, Card, Spinner } from "../../ui";

type State = { kind: "pending" } | { kind: "ok" } | { kind: "error"; message: string };

/** E-postadaki bağlantı: /e-posta-dogrula?token=… Bağlantı tek kullanımlık. */
export function VerifyEmailPage() {
  const token = useLinkToken();
  const [state, setState] = useState<State>(
    token ? { kind: "pending" } : { kind: "error", message: "Bağlantı eksik. E-postadaki bağlantıyı açtığından emin ol." },
  );
  // StrictMode efektleri geliştirmede iki kez çalıştırır; tek kullanımlık token ikinci istekte "geçersiz" döner.
  const sentFor = useRef<string | null>(null);

  useEffect(() => {
    if (!token || sentFor.current === token) return;
    sentFor.current = token;
    api
      .POST("/api/v1/auth/verify-email", { body: { token } })
      .then(({ response, error }) =>
        setState(response.ok ? { kind: "ok" } : { kind: "error", message: problemMessage(error) }),
      )
      .catch(() => setState({ kind: "error", message: "Sunucuya ulaşılamadı. Sayfayı yenileyip tekrar dene." }));
  }, [token]);

  return (
    <Card title="E-posta doğrulama" className="auth-card" headingLevel={1}>
      {state.kind === "pending" && (
        <div className="row">
          <Spinner label="Doğrulanıyor" />
          <span aria-hidden="true">Doğrulanıyor…</span>
        </div>
      )}
      {state.kind === "ok" && (
        <Alert tone="success" live>
          E-posta adresin doğrulandı.
        </Alert>
      )}
      {state.kind === "error" && <Alert tone="error">{state.message}</Alert>}
      {state.kind !== "pending" && <Link to="/giris">Giriş ekranına git</Link>}
    </Card>
  );
}

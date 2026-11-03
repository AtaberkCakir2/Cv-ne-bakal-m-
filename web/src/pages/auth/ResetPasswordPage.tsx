import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, problemMessage } from "../../api/client";
import { clearSession } from "../../auth/session";
import { useLinkToken } from "../../auth/useLinkToken";
import {
  confirmError,
  focusFirstError,
  hasErrors,
  passwordError,
  PASSWORD_MIN,
  type Errors,
} from "../../auth/validation";
import { Alert, Button, Card, TextField } from "../../ui";

/** E-postadaki bağlantı: /sifre-sifirla?token=… (backend/app/services/auth.py). */
export function ResetPasswordPage() {
  const token = useLinkToken();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<Errors<"password" | "confirm">>({});
  const [formError, setFormError] = useState<string>();
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const next = { password: passwordError(password), confirm: confirmError(password, confirm) };
    setErrors(next);
    setFormError(undefined);
    if (hasErrors(next)) {
      requestAnimationFrame(() => focusFirstError(form));
      return;
    }
    setPending(true);
    try {
      const { response, error } = await api.POST("/api/v1/auth/reset-password", {
        body: { token, new_password: password },
      });
      if (response.ok) {
        clearSession(); // backend tüm oturumları kapattı; bu cihazdaki eski token da geçersiz
        setDone(true);
      } else {
        setFormError(problemMessage(error));
      }
    } catch {
      setFormError("Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.");
    } finally {
      setPending(false);
    }
  }

  if (!token) {
    return (
      <Card title="Şifre sıfırlama" className="auth-card" headingLevel={1}>
        <Alert tone="error">Bağlantı eksik. E-postadaki bağlantıyı açtığından emin ol.</Alert>
        <Link to="/sifremi-unuttum">Yeni bağlantı iste</Link>
      </Card>
    );
  }

  if (done) {
    return (
      <Card title="Şifren değişti" className="auth-card" headingLevel={1} focusTitle>
        <Alert tone="success" live>
          Yeni şifrenle giriş yapabilirsin. Güvenlik için diğer cihazlardaki oturumların kapatıldı.
        </Alert>
        <Link to="/giris">Giriş yap</Link>
      </Card>
    );
  }

  return (
    <Card title="Yeni şifre belirle" className="auth-card" headingLevel={1}>
      {formError && (
        <Alert tone="error">
          {formError} <Link to="/sifremi-unuttum">Yeni bağlantı iste</Link>
        </Alert>
      )}
      <form onSubmit={submit} noValidate>
        <TextField
          label="Yeni şifre"
          type="password"
          autoComplete="new-password"
          hint={`En az ${PASSWORD_MIN} karakter.`}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          required
        />
        <TextField
          label="Yeni şifre (tekrar)"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={errors.confirm}
          required
        />
        <Button type="submit" block loading={pending}>
          Şifreyi değiştir
        </Button>
      </form>
    </Card>
  );
}

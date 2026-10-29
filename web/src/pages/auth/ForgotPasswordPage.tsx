import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, problemMessage } from "../../api/client";
import { emailError, focusFirstError } from "../../auth/validation";
import { Alert, Button, Card, TextField } from "../../ui";

export function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string>();
  const [formError, setFormError] = useState<string>();
  const [pending, setPending] = useState(false);
  const [sent, setSent] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const err = emailError(email);
    setError(err);
    setFormError(undefined);
    if (err) {
      requestAnimationFrame(() => focusFirstError(form));
      return;
    }
    setPending(true);
    try {
      const { response, error: problem } = await api.POST("/api/v1/auth/forgot-password", { body: { email: email.trim() } });
      if (response.ok) setSent(true);
      else setFormError(problemMessage(problem));
    } catch {
      setFormError("Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.");
    } finally {
      setPending(false);
    }
  }

  if (sent) {
    // Backend e-postanın kayıtlı olup olmadığını söylemez; mesaj da söylememeli.
    return (
      <Card title="E-postanı kontrol et" className="auth-card" headingLevel={1} focusTitle>
        <Alert tone="success" live>
          Bu adresle bir hesap varsa şifre sıfırlama bağlantısı gönderdik. Bağlantı 1 saat geçerli.
        </Alert>
        <Link to="/giris">Giriş ekranına dön</Link>
      </Card>
    );
  }

  return (
    <Card title="Şifremi unuttum" className="auth-card" headingLevel={1}>
      <p className="muted">Hesabının e-posta adresini yaz; şifreni sıfırlaman için bir bağlantı gönderelim.</p>
      {formError && <Alert tone="error">{formError}</Alert>}
      <form onSubmit={submit} noValidate>
        <TextField
          label="E-posta"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={error}
          required
        />
        <Button type="submit" block loading={pending}>
          Bağlantı gönder
        </Button>
      </form>
      <p className="auth-links">
        <Link to="/giris">Giriş ekranına dön</Link>
      </p>
    </Card>
  );
}

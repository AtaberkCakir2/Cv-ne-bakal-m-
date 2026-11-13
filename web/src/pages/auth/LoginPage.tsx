import { useQueryClient } from "@tanstack/react-query";
import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";

import { api, problemMessage } from "../../api/client";
import { safeNext } from "../../auth/next";
import { setTokens } from "../../auth/session";
import { emailError, focusFirstError, hasErrors, type Errors } from "../../auth/validation";
import { Alert, Button, Card, TextField } from "../../ui";

export function LoginPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [params] = useSearchParams();
  // Başka bir sayfadan bilgi mesajıyla gelinmiş olabilir (ör. hesap silindikten sonra).
  const notice = (useLocation().state as { notice?: string } | null)?.notice;
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors<"email" | "password">>({});
  const [formError, setFormError] = useState<string>();
  const [pending, setPending] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const next = { email: emailError(email), password: password ? undefined : "Şifreni girin." };
    setErrors(next);
    setFormError(undefined);
    if (hasErrors(next)) {
      requestAnimationFrame(() => focusFirstError(form));
      return;
    }
    setPending(true);
    try {
      const { data, error } = await api.POST("/api/v1/auth/login", { body: { email: email.trim(), password } });
      if (data) {
        queryClient.clear(); // oturum kendiliğinden bittiyse önceki kullanıcının verisi önbellekte kalmış olabilir
        setTokens(data);
        navigate(safeNext(params.get("sonra")), { replace: true });
      } else {
        setFormError(problemMessage(error));
      }
    } catch {
      setFormError("Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.");
    } finally {
      setPending(false);
    }
  }

  return (
    <Card title="Giriş yap" className="auth-card" headingLevel={1} focusTitle={Boolean(notice)}>
      {notice && !formError && <Alert tone="success">{notice}</Alert>}
      {params.get("sonra") && !formError && <Alert tone="info">Devam etmek için giriş yap.</Alert>}
      {formError && <Alert tone="error">{formError}</Alert>}
      <form onSubmit={submit} noValidate>
        <TextField
          label="E-posta"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          error={errors.email}
          required
        />
        <TextField
          label="Şifre"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          required
        />
        <Button type="submit" block loading={pending}>
          Giriş yap
        </Button>
      </form>
      <p className="auth-links">
        <Link to="/sifremi-unuttum">Şifremi unuttum</Link>
        <span>
          Hesabın yok mu? <Link to="/kayit">Kayıt ol</Link>
        </span>
      </p>
    </Card>
  );
}

import { useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { api, fieldErrors, problemMessage } from "../../api/client";
import type { components } from "../../api/schema";
import {
  confirmError,
  emailError,
  focusFirstError,
  hasErrors,
  passwordError,
  PASSWORD_MIN,
  type Errors,
} from "../../auth/validation";
import { Alert, Button, Card, Checkbox, TextField } from "../../ui";

type ConsentType = components["schemas"]["ConsentType"];

// Kabul edilen metnin sürümü backend'de onayla birlikte saklanır. Metinler T-065'te kesinleşince sürüm değişir.
const CONSENT_VERSION = "2026-10-taslak";

const CONSENTS: { type: ConsentType; label: string }[] = [
  { type: "kvkk_aydinlatma", label: "KVKK aydınlatma metnini okudum." },
  { type: "acik_riza", label: "CV'mdeki yetkinliklerin analiz için işlenmesine açık rıza veriyorum." },
  { type: "kullanim_kosullari", label: "Kullanım koşullarını kabul ediyorum." },
];

type Field = "full_name" | "email" | "password" | "confirm" | ConsentType;

export function RegisterPage() {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [accepted, setAccepted] = useState<Record<ConsentType, boolean>>({
    kvkk_aydinlatma: false,
    acik_riza: false,
    kullanim_kosullari: false,
  });
  const [errors, setErrors] = useState<Errors<Field>>({});
  const [formError, setFormError] = useState<string>();
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);

  async function submit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const next: Errors<Field> = {
      email: emailError(email),
      password: passwordError(password),
      confirm: confirmError(password, confirm),
      full_name: fullName.length > 120 ? "Ad soyad en fazla 120 karakter olabilir." : undefined,
    };
    for (const c of CONSENTS) if (!accepted[c.type]) next[c.type] = "Kayıt için bu onay zorunlu.";
    setErrors(next);
    setFormError(undefined);
    if (hasErrors(next)) {
      requestAnimationFrame(() => focusFirstError(form));
      return;
    }
    setPending(true);
    try {
      const { response, error } = await api.POST("/api/v1/auth/register", {
        body: {
          email: email.trim(),
          password,
          full_name: fullName.trim() || null,
          consents: CONSENTS.map((c) => ({ consent_type: c.type, version: CONSENT_VERSION })),
        },
      });
      if (response.ok) {
        setDone(true);
        return;
      }
      // Backend onay hatasını tek "consents" alanıyla döner; ilk kutuya bağlanır ki odak bir yere gitsin.
      const { consents, ...rest } = fieldErrors(error);
      setErrors(consents ? { ...rest, kvkk_aydinlatma: consents } : rest);
      setFormError(problemMessage(error));
      requestAnimationFrame(() => focusFirstError(form));
    } catch {
      setFormError("Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.");
    } finally {
      setPending(false);
    }
  }

  if (done) {
    return (
      <Card title="E-postanı kontrol et" className="auth-card" headingLevel={1} focusTitle>
        <Alert tone="success" live>
          Hesabın oluşturuldu. <strong>{email.trim()}</strong> adresine bir doğrulama bağlantısı gönderdik.
        </Alert>
        <p>Bağlantı 24 saat geçerli. Doğrulamadan da giriş yapabilirsin.</p>
        <Link to="/giris">Giriş ekranına git</Link>
      </Card>
    );
  }

  return (
    <Card title="Kayıt ol" className="auth-card" headingLevel={1}>
      {formError && <Alert tone="error">{formError}</Alert>}
      <form onSubmit={submit} noValidate>
        <TextField
          label="Ad soyad (isteğe bağlı)"
          autoComplete="name"
          maxLength={120}
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          error={errors.full_name}
        />
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
          autoComplete="new-password"
          hint={`En az ${PASSWORD_MIN} karakter.`}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          error={errors.password}
          required
        />
        <TextField
          label="Şifre (tekrar)"
          type="password"
          autoComplete="new-password"
          value={confirm}
          onChange={(e) => setConfirm(e.target.value)}
          error={errors.confirm}
          required
        />
        <fieldset className="consents">
          <legend>Onaylar (zorunlu)</legend>
          {CONSENTS.map((c) => (
            <Checkbox
              key={c.type}
              label={c.label}
              checked={accepted[c.type]}
              onChange={(e) => setAccepted((a) => ({ ...a, [c.type]: e.target.checked }))}
              error={errors[c.type]}
              required
            />
          ))}
          <p className="field__hint">Metinlerin son hali yayından önce eklenecek (T-065).</p>
        </fieldset>
        <Alert tone="info">CV dosyan saklanmaz; analizden sonra sadece çıkan yetkinlikler hesabında kalır.</Alert>
        <Button type="submit" block loading={pending}>
          Kayıt ol
        </Button>
      </form>
      <p className="auth-links">
        <span>
          Zaten hesabın var mı? <Link to="/giris">Giriş yap</Link>
        </span>
      </p>
    </Card>
  );
}

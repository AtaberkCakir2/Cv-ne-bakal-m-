import { useState } from "react";
import { Linking } from "react-native";

import { api, fieldErrors, problemMessage } from "../api/client";
import { CONSENT_VERSION, CONSENTS, type ConsentType } from "../auth/consents";
import { confirmError, emailError, hasErrors, passwordError, PASSWORD_MIN, type Errors } from "../auth/validation";
import type { ScreenProps } from "../navigation";
import { Alert, Body, Button, Checkbox, Field, Screen, Title } from "../ui";

type FieldName = "full_name" | "email" | "password" | "confirm" | ConsentType;

/**
 * T-061: kayıt + KVKK onayları (web/src/pages/auth/RegisterPage.tsx ile aynı kurallar). Üç onay da zorunlu; her
 * onayın metni tarayıcıda açılabilir. Onaylar sürümüyle birlikte backend'e gider (consents tablosu).
 */
export function RegisterScreen({ navigation }: ScreenProps<"Register">) {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [accepted, setAccepted] = useState<Record<ConsentType, boolean>>({
    kvkk_aydinlatma: false,
    acik_riza: false,
    kullanim_kosullari: false,
  });
  const [errors, setErrors] = useState<Errors<FieldName>>({});
  const [formError, setFormError] = useState<string>();
  const [pending, setPending] = useState(false);
  const [done, setDone] = useState(false);

  async function submit() {
    const next: Errors<FieldName> = {
      email: emailError(email),
      password: passwordError(password),
      confirm: confirmError(password, confirm),
      full_name: fullName.length > 120 ? "Ad soyad en fazla 120 karakter olabilir." : undefined,
    };
    for (const c of CONSENTS) if (!accepted[c.type]) next[c.type] = "Kayıt için bu onay zorunlu.";
    setErrors(next);
    setFormError(hasErrors(next) ? "Formdaki işaretli alanları düzelt." : undefined);
    if (hasErrors(next)) return;
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
      const { consents, ...rest } = fieldErrors(error);
      setErrors(consents ? { ...rest, kvkk_aydinlatma: consents } : rest);
      setFormError(problemMessage(error));
    } catch {
      setFormError("Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.");
    } finally {
      setPending(false);
    }
  }

  if (done) {
    return (
      <Screen>
        <Title>E-postanı kontrol et</Title>
        <Alert tone="success">
          Hesabın oluşturuldu. {email.trim()} adresine bir doğrulama bağlantısı gönderdik. Bağlantı 24 saat geçerli;
          doğrulamadan da giriş yapabilirsin.
        </Alert>
        <Button
          title="Giriş ekranına git"
          onPress={() => navigation.navigate("Login", { notice: "Hesabın hazır, giriş yapabilirsin." })}
        />
      </Screen>
    );
  }

  return (
    <Screen>
      <Title>Kayıt ol</Title>
      {formError && <Alert tone="error">{formError}</Alert>}
      <Field
        label="Ad soyad (isteğe bağlı)"
        value={fullName}
        onChangeText={setFullName}
        error={errors.full_name}
        maxLength={120}
        autoComplete="name"
        textContentType="name"
      />
      <Field
        label="E-posta"
        value={email}
        onChangeText={setEmail}
        error={errors.email}
        keyboardType="email-address"
        autoCapitalize="none"
        autoComplete="email"
        textContentType="emailAddress"
      />
      <Field
        label="Şifre"
        value={password}
        onChangeText={setPassword}
        error={errors.password}
        hint={`En az ${PASSWORD_MIN} karakter.`}
        secureTextEntry
        autoComplete="new-password"
        textContentType="newPassword"
      />
      <Field
        label="Şifre (tekrar)"
        value={confirm}
        onChangeText={setConfirm}
        error={errors.confirm}
        secureTextEntry
        autoComplete="new-password"
        textContentType="newPassword"
      />
      <Body>Onaylar (zorunlu)</Body>
      {CONSENTS.map((c) => (
        <Checkbox
          key={c.type}
          label={c.label}
          checked={accepted[c.type]}
          onChange={(value) => setAccepted((a) => ({ ...a, [c.type]: value }))}
          error={errors[c.type]}
          link={{ title: "Metni oku", onPress: () => void Linking.openURL(c.url) }}
        />
      ))}
      <Alert tone="info">CV dosyan saklanmaz; analizden sonra sadece çıkan yetkinlikler hesabında kalır.</Alert>
      <Button title="Kayıt ol" onPress={() => void submit()} loading={pending} />
      <Button variant="link" title="Zaten hesabın var mı? Giriş yap" onPress={() => navigation.navigate("Login")} />
    </Screen>
  );
}

import { useRef, useState } from "react";

import { api, problemMessage } from "../api/client";
import { setTokens } from "../auth/session";
import { emailError, hasErrors, type Errors } from "../auth/validation";
import type { ScreenProps } from "../navigation";
import { Alert, Body, Button, Field, Screen, Title, type TextInputRef } from "../ui";

/** T-061: giriş (web/src/pages/auth/LoginPage.tsx ile aynı kurallar). Başarılı girişte uygulama ekranları açılır. */
export function LoginScreen({ navigation, route }: ScreenProps<"Login">) {
  const notice = route.params?.notice;
  const passwordRef = useRef<TextInputRef>(null);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors<"email" | "password">>({});
  const [formError, setFormError] = useState<string>();
  const [pending, setPending] = useState(false);

  async function submit() {
    const next = { email: emailError(email), password: password ? undefined : "Şifreni girin." };
    setErrors(next);
    setFormError(undefined);
    if (hasErrors(next)) return;
    setPending(true);
    try {
      const { data, error } = await api.POST("/api/v1/auth/login", { body: { email: email.trim(), password } });
      if (data) {
        await setTokens(data); // oturum açılınca App.tsx uygulama ekranlarına geçer
        return;
      }
      setFormError(problemMessage(error));
    } catch {
      setFormError("Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.");
    } finally {
      setPending(false);
    }
  }

  return (
    <Screen>
      <Title>Cv'ne Bakalım!</Title>
      <Body muted>CV'ni hedeflediğin pozisyonun güncel ilanlarıyla karşılaştır, eksiklerini gör.</Body>
      {notice && !formError && <Alert tone="success">{notice}</Alert>}
      {formError && <Alert tone="error">{formError}</Alert>}
      <Field
        label="E-posta"
        value={email}
        onChangeText={setEmail}
        error={errors.email}
        keyboardType="email-address"
        autoCapitalize="none"
        autoComplete="email"
        textContentType="emailAddress"
        returnKeyType="next"
        onSubmitEditing={() => passwordRef.current?.focus()}
      />
      <Field
        ref={passwordRef}
        label="Şifre"
        value={password}
        onChangeText={setPassword}
        error={errors.password}
        secureTextEntry
        autoComplete="current-password"
        textContentType="password"
        returnKeyType="go"
        onSubmitEditing={() => void submit()}
      />
      <Button title="Giriş yap" onPress={() => void submit()} loading={pending} />
      <Button variant="link" title="Hesabın yok mu? Kayıt ol" onPress={() => navigation.navigate("Register")} />
    </Screen>
  );
}

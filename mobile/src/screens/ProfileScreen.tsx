import { useEffect, useState } from "react";
import { Alert as NativeAlert, Pressable, StyleSheet, Text, View } from "react-native";

import { formatDate } from "../analysis/format";
import { api, problemMessage, unwrap } from "../api/client";
import type { components } from "../api/schema";
import { CONSENT_NAMES, CONSENT_VERSION } from "../auth/consents";
import { clearSession, pendingRefresh } from "../auth/session";
import { setSignOutNotice } from "../auth/useSession";
import { Alert, Body, Button, Field, Loading, Screen, Section } from "../ui";
import { useColors } from "../ui/theme";

type Profile = components["schemas"]["ProfileOut"];
type Role = components["schemas"]["RoleOut"];
type Consent = components["schemas"]["ConsentOut"];

const MAX_NAME = 120;

/**
 * T-062: profil (web/src/pages/ProfilePage.tsx): hesap bilgileri ve hedef pozisyon, onaylar (açık rızayı geri alma /
 * yeniden verme) ve hesap silme (KVKK md. 11). Verileri JSON olarak indirme web uygulamasında.
 */
export function ProfileScreen() {
  const [profile, setProfile] = useState<Profile>();
  const [roles, setRoles] = useState<Role[]>();
  const [error, setError] = useState<string>();

  useEffect(() => {
    let active = true;
    Promise.all([api.GET("/api/v1/users/me").then(unwrap), api.GET("/api/v1/roles").then(unwrap)])
      .then(([me, list]) => {
        if (!active) return;
        setProfile(me);
        setRoles(list);
      })
      .catch((e) => active && setError(problemMessage(e)));
    return () => {
      active = false;
    };
  }, []);

  if (error) {
    return (
      <Screen>
        <Alert tone="error">{error}</Alert>
      </Screen>
    );
  }
  if (!profile || !roles) return <Loading label="Profil yükleniyor" />;

  return (
    <Screen>
      <AccountSection profile={profile} roles={roles} onSaved={setProfile} />
      <ConsentsSection />
      <DeleteAccountSection />
    </Screen>
  );
}

function AccountSection({ profile, roles, onSaved }: { profile: Profile; roles: Role[]; onSaved: (p: Profile) => void }) {
  const c = useColors();
  const [name, setName] = useState(profile.full_name ?? "");
  const [roleId, setRoleId] = useState(profile.target_role?.id);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);

  async function save() {
    setSaved(false);
    setError(undefined);
    setPending(true);
    try {
      const data = unwrap(
        await api.PATCH("/api/v1/users/me", {
          // Pozisyon sadece değiştiyse gönderilir: profildeki pozisyon artık aktif değilse ad kaydı 422 almasın.
          body: {
            full_name: name.trim() || null,
            ...(roleId !== profile.target_role?.id && { target_role_id: roleId ?? null }),
          },
        }),
      );
      onSaved(data);
      setSaved(true);
    } catch (e) {
      setError(problemMessage(e));
    } finally {
      setPending(false);
    }
  }

  return (
    <Section title="Hesap bilgileri">
      <Body>E-posta: {profile.email}</Body>
      <Body muted>{profile.is_verified ? "E-postan doğrulandı." : "E-postan doğrulanmadı; e-postandaki bağlantıyı aç."}</Body>
      {error && <Alert tone="error">{error}</Alert>}
      <Field
        label="Ad soyad (isteğe bağlı)"
        value={name}
        onChangeText={(v) => {
          setName(v);
          setSaved(false);
        }}
        maxLength={MAX_NAME}
        autoComplete="name"
      />
      <Text style={[styles.label, { color: c.text }]}>Hedef pozisyon</Text>
      <View accessibilityRole="radiogroup" style={styles.roles}>
        {[{ id: undefined, name: "Seçilmedi" } as { id: number | undefined; name: string }, ...roles].map((r) => {
          const selected = r.id === roleId || (r.id === undefined && !roles.some((x) => x.id === roleId));
          return (
            <Pressable
              key={r.id ?? "none"}
              accessibilityRole="radio"
              accessibilityState={{ selected }}
              onPress={() => {
                setRoleId(r.id);
                setSaved(false);
              }}
              style={[styles.role, { borderColor: selected ? c.primary : c.border, backgroundColor: selected ? c.infoBg : c.surface }]}
            >
              <Text style={{ color: selected ? c.primary : c.text, fontWeight: selected ? "700" : "400" }}>{r.name}</Text>
            </Pressable>
          );
        })}
      </View>
      <Text style={{ color: c.muted }}>CV yüklerken bu pozisyon hazır seçili gelir.</Text>
      <Button title="Kaydet" onPress={() => void save()} loading={pending} />
      {saved && <Alert tone="success">Kaydedildi.</Alert>}
    </Section>
  );
}

function ConsentsSection() {
  const [consents, setConsents] = useState<Consent[]>();
  const [error, setError] = useState<string>();
  const [notice, setNotice] = useState<string>();
  const [pending, setPending] = useState(false);

  useEffect(() => {
    let active = true;
    api
      .GET("/api/v1/users/me/consents")
      .then(unwrap)
      .then((data) => active && setConsents(data))
      .catch((e) => active && setError(problemMessage(e)));
    return () => {
      active = false;
    };
  }, []);

  // Her tür için en son kayıt yürürlüktedir; eski sürüm satırları silinmez (backend sürümlü tutar).
  const latest = new Map<string, Consent>();
  for (const c of consents ?? []) {
    const prev = latest.get(c.consent_type);
    if (!prev || Date.parse(c.accepted_at) >= Date.parse(prev.accepted_at)) latest.set(c.consent_type, c);
  }
  const explicit = latest.get("acik_riza");
  const explicitActive = explicit != null && explicit.withdrawn_at == null;

  async function change(give: boolean) {
    setNotice(undefined);
    setError(undefined);
    setPending(true);
    try {
      const data = give
        ? unwrap(
            await api.POST("/api/v1/users/me/consents", {
              body: { consents: [{ consent_type: "acik_riza", version: CONSENT_VERSION }] },
            }),
          )
        : unwrap(
            await api.DELETE("/api/v1/users/me/consents/{consent_type}", {
              params: { path: { consent_type: "acik_riza" } },
            }),
          );
      setConsents(data);
      setNotice(give ? "Açık rızan kaydedildi; yeniden analiz başlatabilirsin." : "Açık rızan geri alındı.");
    } catch (e) {
      setError(problemMessage(e));
    } finally {
      setPending(false);
    }
  }

  function confirmWithdraw() {
    NativeAlert.alert(
      "Açık rızan geri alınsın mı?",
      "Geri alırsan yeni CV analizi başlatamazsın. Önceki analizlerin silinmez; istersen Geçmiş'ten silebilirsin. Rızanı daha sonra buradan yeniden verebilirsin.",
      [
        { text: "Vazgeç", style: "cancel" },
        { text: "Geri al", style: "destructive", onPress: () => void change(false) },
      ],
    );
  }

  return (
    <Section title="Onaylarım">
      {error && <Alert tone="error">{error}</Alert>}
      {!consents && !error && <Loading label="Onaylar yükleniyor" />}
      {[...latest.values()].map((c) => (
        <Body key={c.consent_type}>
          {CONSENT_NAMES[c.consent_type]} · sürüm {c.version} · {formatDate(c.accepted_at)}
          {c.withdrawn_at ? ` · ${formatDate(c.withdrawn_at)} tarihinde geri alındı` : ""}
        </Body>
      ))}
      {notice && <Alert tone="success">{notice}</Alert>}
      {consents &&
        (explicitActive ? (
          <Button variant="secondary" title="Açık rızamı geri al" onPress={confirmWithdraw} loading={pending} />
        ) : (
          <>
            <Body muted>
              Açık rıza metninin {CONSENT_VERSION} sürümünü onaylamış olursun; CV'ndeki yetkinlikler analiz için işlenir.
            </Body>
            <Button title="Açık rıza ver" onPress={() => void change(true)} loading={pending} />
          </>
        ))}
      <Body muted>
        Aydınlatma metni ve kullanım koşulları hizmetin kendisi için gerekli; onlardan çıkmak için hesabını silebilirsin.
        Verilerini indirmek için web uygulamasında Profil → Verilerim.
      </Body>
    </Section>
  );
}

function DeleteAccountSection() {
  const [open, setOpen] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string>();
  const [pending, setPending] = useState(false);

  async function submit() {
    if (!password) {
      setError("Onaylamak için şifreni gir.");
      return;
    }
    setError(undefined);
    setPending(true);
    try {
      const { error: problem, response } = await api.DELETE("/api/v1/users/me", { body: { password } });
      if (!response.ok) {
        setError(problemMessage(problem));
        return;
      }
      await pendingRefresh(); // süren bir yenileme, silinen oturumu temizlendikten sonra geri yazmasın
      setSignOutNotice("Hesabın kapatıldı. Verilerin 30 gün içinde kalıcı olarak silinecek.");
      await clearSession(); // backend tüm oturumları kapattı; uygulama giriş ekranına döner
    } catch {
      setError("Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.");
    } finally {
      setPending(false);
    }
  }

  return (
    <Section title="Hesabını sil">
      <Body>
        Hesabın hemen kapatılır, tüm oturumların sonlanır ve kişisel bilgilerin anonimleştirilir. Hesap bilgilerin,
        analizlerin ve onay kayıtların 30 gün sonra kalıcı olarak silinir. Bu işlem geri alınamaz.
      </Body>
      {!open ? (
        <Button variant="danger" title="Hesabımı sil" onPress={() => setOpen(true)} />
      ) : (
        <>
          <Body>Onaylamak için şifreni gir.</Body>
          {error && <Alert tone="error">{error}</Alert>}
          <Field label="Şifre" value={password} onChangeText={setPassword} secureTextEntry autoComplete="current-password" />
          <Button variant="danger" title="Hesabımı kalıcı olarak sil" onPress={() => void submit()} loading={pending} />
          <Button
            variant="secondary"
            title="Vazgeç"
            onPress={() => {
              setOpen(false);
              setPassword("");
              setError(undefined);
            }}
          />
        </>
      )}
    </Section>
  );
}

const styles = StyleSheet.create({
  label: { fontWeight: "600" },
  roles: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  role: { minHeight: 44, borderWidth: 1, borderRadius: 22, paddingHorizontal: 14, justifyContent: "center" },
});

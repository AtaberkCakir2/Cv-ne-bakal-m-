import * as DocumentPicker from "expo-document-picker";
import { useEffect, useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { cvFileError, formatSize, formatWait, MAX_CV_PAGES, type PickedFile } from "../analysis/cvFile";
import { api, problemMessage, unwrap, type Problem } from "../api/client";
import type { components } from "../api/schema";
import type { ScreenProps } from "../navigation";
import { Alert, Body, Button, Loading, Screen, Title } from "../ui";
import { useColors } from "../ui/theme";

type Role = components["schemas"]["RoleOut"];

/** 5 MB yavaş mobil bağlantıda da bu sürede gider; sunucu yanıt vermezse düğme sonsuza dek "İşleniyor" kalmasın. */
const UPLOAD_TIMEOUT_MS = 90_000;

/**
 * T-061: hedef pozisyon seçimi + CV seçme (expo-document-picker) ve yükleme (web/src/pages/UploadPage.tsx ile aynı
 * kurallar). Dosya sadece seçildiği anda cihazdaki geçici kopyasıyla gönderilir; uygulama dosyayı ya da içeriğini
 * saklamaz. Başarılı yüklemede bekleme ekranına geçilir.
 */
export function UploadScreen({ navigation }: ScreenProps<"Upload">) {
  const c = useColors();
  const [roles, setRoles] = useState<Role[]>();
  const [loadError, setLoadError] = useState<string>();
  const [roleId, setRoleId] = useState<number>();
  const [file, setFile] = useState<PickedFile>();
  const [fileError, setFileError] = useState<string>();
  const [roleError, setRoleError] = useState<string>();
  const [formError, setFormError] = useState<string>();
  const [pending, setPending] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const [list, me] = await Promise.all([
          api.GET("/api/v1/roles").then(unwrap),
          api.GET("/api/v1/users/me").then(unwrap),
        ]);
        if (!active) return;
        setRoles(list);
        // Profildeki hedef pozisyon hâlâ listede ise önceden seçili gelir.
        const profileRole = me.target_role?.id;
        if (list.some((r) => r.id === profileRole)) setRoleId((current) => current ?? profileRole);
      } catch (error) {
        if (active) setLoadError(problemMessage(error));
      }
    })();
    return () => {
      active = false;
    };
  }, []);

  async function pick() {
    setFormError(undefined);
    const picked = await DocumentPicker.getDocumentAsync({
      type: "application/pdf",
      copyToCacheDirectory: true, // content:// adresleri yükleme için okunabilir olsun
      multiple: false,
    });
    if (picked.canceled) return;
    const asset = picked.assets[0];
    const candidate: PickedFile = { uri: asset.uri, name: asset.name, size: asset.size, mimeType: asset.mimeType };
    const error = cvFileError(candidate);
    setFileError(error);
    setFile(error ? undefined : candidate);
  }

  async function submit() {
    setFormError(undefined);
    setRoleError(roleId ? undefined : "Hedef pozisyonu seç.");
    if (!file) setFileError((current) => current ?? "CV dosyanı seç.");
    if (!roleId || !file) return;
    setPending(true);
    const abort = new AbortController();
    const timer = setTimeout(() => abort.abort(), UPLOAD_TIMEOUT_MS);
    try {
      const { data, error, response } = await api.POST("/api/v1/analyses", {
        signal: abort.signal,
        // openapi tipi dosyayı string (binary) sayar; React Native'de dosya {uri, name, type} parçası olarak gider.
        body: { file: file.uri, target_role_id: roleId },
        bodySerializer: () => {
          const form = new FormData();
          form.append("file", { uri: file.uri, name: file.name, type: "application/pdf" } as unknown as Blob);
          form.append("target_role_id", String(roleId));
          return form;
        },
      });
      if (data) {
        setFile(undefined); // aynı dosya yanlışlıkla iki kez gönderilmesin
        navigation.navigate("Analysis", { id: data.analysis_id });
        return;
      }
      setFormError(uploadErrorMessage(error, response));
    } catch {
      setFormError(
        abort.signal.aborted
          ? "Yükleme zaman aşımına uğradı. Bağlantını kontrol edip tekrar dene."
          : "Sunucuya ulaşılamadı. İnternet bağlantını kontrol edip tekrar dene.",
      );
    } finally {
      clearTimeout(timer);
      setPending(false);
    }
  }

  if (loadError) {
    return (
      <Screen>
        <Alert tone="error">{loadError}</Alert>
      </Screen>
    );
  }
  if (!roles) return <Loading label="Yükleniyor" />;

  return (
    <Screen>
      <Title>CV'ni yükle</Title>
      <Body muted>CV'n seçtiğin pozisyonun güncel ilanlarıyla karşılaştırılır.</Body>
      {formError && <Alert tone="error">{formError}</Alert>}

      <Text style={[styles.label, { color: c.text }]}>Hedef pozisyon</Text>
      <View accessibilityRole="radiogroup" style={styles.roles}>
        {roles.map((r) => {
          const selected = r.id === roleId;
          return (
            <Pressable
              key={r.id}
              accessibilityRole="radio"
              accessibilityState={{ selected, disabled: pending }}
              disabled={pending}
              onPress={() => {
                setRoleId(r.id);
                setRoleError(undefined);
              }}
              style={[
                styles.role,
                { borderColor: selected ? c.primary : c.border, backgroundColor: selected ? c.infoBg : c.surface },
              ]}
            >
              <Text style={{ color: selected ? c.primary : c.text, fontWeight: selected ? "700" : "400" }}>{r.name}</Text>
            </Pressable>
          );
        })}
      </View>
      {roleError && <Text style={{ color: c.error }}>{roleError}</Text>}

      <Text style={[styles.label, { color: c.text }]}>CV dosyası</Text>
      <Text accessibilityLiveRegion="polite" style={{ color: file ? c.text : c.muted }}>
        {file ? `${file.name}${file.size ? ` · ${formatSize(file.size)}` : ""}` : "Henüz dosya seçilmedi."}
      </Text>
      <Button variant="secondary" title={file ? "Başka dosya seç" : "PDF seç"} onPress={() => void pick()} disabled={pending} />
      <Text style={{ color: c.muted }}>Sadece PDF · en fazla 5 MB ve {MAX_CV_PAGES} sayfa · Türkçe veya İngilizce</Text>
      {fileError && (
        <Text accessibilityRole="alert" style={{ color: c.error }}>
          {fileError}
        </Text>
      )}

      <Button title="Analizi başlat" onPress={() => void submit()} loading={pending} />
      <Alert tone="info">CV dosyan saklanmaz; analizden sonra sadece çıkan yetkinlikler hesabında kalır.</Alert>
    </Screen>
  );
}

/** Web'deki uploadErrorMessage ile aynı metinler. */
function uploadErrorMessage(error: unknown, response: Response): string {
  const problem = error as Partial<Problem> | undefined;
  const wait = Number(response.headers.get("Retry-After"));
  if (response.status === 429) {
    return `Saatte en fazla 5 analiz yapabilirsin.${wait > 0 ? ` ${formatWait(wait)} sonra tekrar dene.` : ""}`;
  }
  if (response.status === 503) {
    return `Sistem şu an yoğun, analiz başlatılamadı.${wait > 0 ? ` ${formatWait(wait)} sonra tekrar dene.` : ""}`;
  }
  if (problem?.code === "PDF_TOO_LARGE") {
    if (problem.detail) return problem.detail;
    return response.status === 413 ? "Dosya en fazla 5 MB olabilir." : `CV en fazla ${MAX_CV_PAGES} sayfa olabilir.`;
  }
  if (problem?.code === "PDF_UNREADABLE") return "PDF okunamadı. Dosya bozuk ya da şifreli olabilir.";
  if (problem?.code === "CONSENT_WITHDRAWN") {
    return "CV analizi için açık rızan geri alınmış. Web uygulamasında Profil → Verilerim bölümünden yeniden verebilirsin.";
  }
  return problemMessage(error);
}

const styles = StyleSheet.create({
  label: { fontWeight: "600", marginTop: 4 },
  roles: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  role: { minHeight: 44, borderWidth: 1, borderRadius: 22, paddingHorizontal: 14, justifyContent: "center" },
});

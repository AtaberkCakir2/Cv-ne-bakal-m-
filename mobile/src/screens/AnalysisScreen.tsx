import { useEffect, useState } from "react";
import { ActivityIndicator, AppState, StyleSheet, Text, View } from "react-native";

import { formatElapsed } from "../analysis/cvFile";
import { ResultView } from "../analysis/ResultView";
import { api, problemMessage, unwrap, type Problem } from "../api/client";
import type { components } from "../api/schema";
import type { ScreenProps } from "../navigation";
import { Alert, Body, Button, Loading, Screen, Title } from "../ui";
import { useColors } from "../ui/theme";

type Analysis = components["schemas"]["AnalysisOut"];

const POLL_MS = 3000;
/** İş başına en fazla 180 sn × 2 deneme ve kuyruk (T-039); bunu geçerse kullanıcıya bilgi verilir, yoklama sürer. */
const SLOW_AFTER_S = 7 * 60;

const STEPS = [
  { status: "queued", label: "Sırada" },
  { status: "processing", label: "Analiz ediliyor" },
  { status: "done", label: "Tamamlandı" },
] as const;

const ERROR_HINTS: Partial<Record<string, string>> = {
  PDF_UNREADABLE: "Dosyayı yeniden PDF olarak kaydedip tekrar dene.",
  NO_TEXT_FOUND: "Taranmış (resim) bir CV olabilir; metni seçilebilen bir PDF dene.",
  LLM_TIMEOUT: "Sistem şu an yoğun. Birkaç dakika sonra tekrar dene.",
};

/**
 * T-061: analiz bekleme ekranı (web/src/pages/AnalysisPage.tsx ile aynı). Bitmemiş analiz 3 sn'de bir yoklanır;
 * uygulama arka plandayken yoklama durur, öne gelince sürer. Bitince sonuç panosu (ResultView, T-062).
 */
export function AnalysisScreen({ navigation, route }: ScreenProps<"Analysis">) {
  const { id } = route.params;
  const [analysis, setAnalysis] = useState<Analysis>();
  const [loadError, setLoadError] = useState<{ notFound: boolean; message: string }>();

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;
    let active = true;
    let foreground = AppState.currentState === "active";

    async function poll() {
      timer = undefined;
      try {
        const data = unwrap(await api.GET("/api/v1/analyses/{analysis_id}", { params: { path: { analysis_id: id } } }));
        if (!active) return;
        setAnalysis(data);
        setLoadError(undefined);
        if (data.status === "done" || data.status === "failed") return;
      } catch (error) {
        if (!active) return;
        const status = (error as Partial<Problem>).status;
        // Kalıcı hata (yok/silinmiş) yoklamayı bitirir; geçici hata eldeki veriyi silmez, sonraki yoklama düzeltir.
        if (status === 404 || status === 422) {
          setLoadError({ notFound: true, message: "Bu analiz yok ya da silinmiş." });
          return;
        }
        setLoadError({ notFound: false, message: problemMessage(error) });
      }
      if (active && foreground) timer = setTimeout(() => void poll(), POLL_MS);
    }

    const sub = AppState.addEventListener("change", (state) => {
      const wasForeground = foreground;
      foreground = state === "active";
      if (foreground && !wasForeground && timer === undefined) void poll();
      if (!foreground && timer !== undefined) {
        clearTimeout(timer);
        timer = undefined;
      }
    });
    void poll();
    return () => {
      active = false;
      if (timer !== undefined) clearTimeout(timer);
      sub.remove();
    };
  }, [id]);

  const again = () => navigation.popTo("Upload");

  if (!analysis) {
    if (!loadError) return <Loading label="Analiz yükleniyor" />;
    return (
      <Screen>
        <Title>{loadError.notFound ? "Analiz bulunamadı" : "Analiz açılamadı"}</Title>
        <Alert tone="error">{loadError.message}</Alert>
        <Button title="Yeni analiz başlat" onPress={again} />
      </Screen>
    );
  }

  if (analysis.status === "failed") {
    const code = analysis.error?.code;
    return (
      <Screen>
        <Title>Analiz tamamlanamadı</Title>
        <Alert tone="error">{analysis.error?.message ?? "Analiz tamamlanamadı. Lütfen tekrar deneyin."}</Alert>
        {code && ERROR_HINTS[code] && <Body>{ERROR_HINTS[code]}</Body>}
        <Button title="Tekrar dene" onPress={again} />
      </Screen>
    );
  }

  if (analysis.status === "done") {
    return (
      <Screen>
        <ResultView
          data={analysis}
          onAgain={again}
          onOpenResource={(resource, skill, demand) => navigation.navigate("Resource", { resource, skill, demand })}
        />
      </Screen>
    );
  }
  return <Waiting data={analysis} />;
}

function Waiting({ data }: { data: Analysis }) {
  const c = useColors();
  const elapsed = useElapsedSeconds(data.created_at);
  const current = STEPS.findIndex((s) => s.status === data.status);
  return (
    <Screen>
      <Title>CV'n analiz ediliyor</Title>
      <Body muted>
        Hedef pozisyon: {data.target_role.name}. Bu işlem genelde 1-2 dakika sürer; uygulamayı kapatabilirsin, sonuç
        hesabında kalır.
      </Body>
      <Text accessibilityLiveRegion="polite" style={styles.hidden}>
        Durum: {STEPS[current]?.label}
      </Text>
      <View style={styles.steps}>
        {STEPS.map((step, i) => {
          const done = i < current;
          const now = i === current;
          return (
            <View key={step.status} style={styles.step}>
              <View
                style={[
                  styles.dot,
                  { borderColor: done || now ? c.primary : c.border, backgroundColor: done ? c.primary : "transparent" },
                ]}
              />
              <Text style={{ color: done || now ? c.text : c.muted, fontWeight: now ? "700" : "400" }}>{step.label}</Text>
              {now && <ActivityIndicator color={c.primary} accessibilityLabel="" />}
            </View>
          );
        })}
      </View>
      <Text importantForAccessibility="no" style={{ color: c.muted }}>
        Geçen süre: {formatElapsed(elapsed)}
      </Text>
      {elapsed > SLOW_AFTER_S && (
        <Alert tone="warning">
          Analiz beklenenden uzun sürüyor. Beklemeye devam edebilir ya da daha sonra tekrar bakabilirsin.
        </Alert>
      )}
    </Screen>
  );
}

function useElapsedSeconds(since: string): number {
  const start = Date.parse(since);
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(timer);
  }, []);
  return Number.isFinite(start) ? Math.max(0, Math.floor((now - start) / 1000)) : 0;
}

const styles = StyleSheet.create({
  steps: { gap: 12, marginVertical: 8 },
  step: { flexDirection: "row", alignItems: "center", gap: 10, minHeight: 32 },
  dot: { width: 16, height: 16, borderRadius: 8, borderWidth: 2 },
  hidden: { position: "absolute", width: 1, height: 1, opacity: 0 },
});

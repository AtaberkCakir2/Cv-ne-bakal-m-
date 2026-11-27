import { useCallback, useEffect, useState } from "react";
import { Alert as NativeAlert, FlatList, Pressable, RefreshControl, StyleSheet, Text, View } from "react-native";

import { formatDate } from "../analysis/format";
import { api, problemMessage, unwrap } from "../api/client";
import type { components } from "../api/schema";
import type { ScreenProps } from "../navigation";
import { Alert, Body, Button, Loading } from "../ui";
import { useColors } from "../ui/theme";

type Summary = components["schemas"]["AnalysisSummaryOut"];

const PAGE = 20;
const STATUS: Record<Summary["status"], string> = {
  queued: "sırada",
  processing: "analiz ediliyor",
  done: "tamamlandı",
  failed: "tamamlanamadı",
};

/** T-062: geçmiş analizler (web/src/pages/HistoryPage.tsx). Yeniden eskiye 20'şer; silme onay sorusuyla. */
export function HistoryScreen({ navigation }: ScreenProps<"History">) {
  const c = useColors();
  const [items, setItems] = useState<Summary[]>();
  const [total, setTotal] = useState(0);
  const [error, setError] = useState<string>();
  const [notice, setNotice] = useState<string>();
  const [loadingMore, setLoadingMore] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async (offset: number) => {
    const page = unwrap(await api.GET("/api/v1/analyses", { params: { query: { limit: PAGE, offset } } }));
    setTotal(page.total);
    setItems((old) => (offset === 0 ? page.items : [...(old ?? []), ...page.items]));
  }, []);

  const refresh = useCallback(async () => {
    setError(undefined);
    try {
      await load(0);
    } catch (e) {
      setError(problemMessage(e));
    }
  }, [load]);

  // Ekrana her dönüşte (ör. analizden geri) liste tazelenir.
  useEffect(() => navigation.addListener("focus", () => void refresh()), [navigation, refresh]);

  async function more() {
    if (loadingMore || !items || items.length >= total) return;
    setLoadingMore(true);
    try {
      await load(items.length);
    } catch (e) {
      setError(problemMessage(e));
    } finally {
      setLoadingMore(false);
    }
  }

  function confirmDelete(a: Summary) {
    setNotice(undefined);
    NativeAlert.alert(
      "Analizi sil",
      `${formatDate(a.created_at, true)} tarihli ${a.target_role.name} analizi silinecek. Bu işlem geri alınamaz.`,
      [
        { text: "Vazgeç", style: "cancel" },
        { text: "Sil", style: "destructive", onPress: () => void remove(a) },
      ],
    );
  }

  async function remove(a: Summary) {
    try {
      const { error: problem, response } = await api.DELETE("/api/v1/analyses/{analysis_id}", {
        params: { path: { analysis_id: a.analysis_id } },
      });
      if (!response.ok && response.status !== 404) throw problem; // 404: zaten silinmiş, listeden kalksın
      setItems((old) => old?.filter((x) => x.analysis_id !== a.analysis_id));
      setTotal((n) => Math.max(0, n - 1));
      setNotice("Analiz silindi.");
    } catch (e) {
      setError(problemMessage(e));
    }
  }

  if (!items) {
    if (!error) return <Loading label="Geçmiş yükleniyor" />;
    return (
      <View style={styles.failed}>
        <Alert tone="error">{error}</Alert>
        <Button title="Tekrar dene" onPress={() => void refresh()} />
      </View>
    );
  }

  return (
    <FlatList
      style={{ backgroundColor: c.bg }}
      contentContainerStyle={styles.list}
      data={items}
      keyExtractor={(a) => a.analysis_id}
      onEndReached={() => void more()}
      onEndReachedThreshold={0.5}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={async () => {
            setRefreshing(true);
            await refresh();
            setRefreshing(false);
          }}
        />
      }
      ListHeaderComponent={
        <View style={{ gap: 10 }}>
          {notice && <Alert tone="success">{notice}</Alert>}
          {error && <Alert tone="error">{error}</Alert>}
        </View>
      }
      ListEmptyComponent={
        <View style={{ gap: 12 }}>
          <Body muted>Henüz analizin yok.</Body>
          <Button title="İlk analizini yap" onPress={() => navigation.popTo("Upload")} />
        </View>
      }
      ListFooterComponent={loadingMore ? <Loading label="Daha fazla yükleniyor" /> : undefined}
      renderItem={({ item: a }) => {
        const label = `${formatDate(a.created_at, true)} ${a.target_role.name}`;
        const result = a.status === "done" && a.match_score != null ? `Uyum ${Math.round(a.match_score)} / 100` : STATUS[a.status];
        return (
          <View style={[styles.row, { borderColor: c.border, backgroundColor: c.surface }]}>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`${label}, ${result}`}
              accessibilityHint={a.status === "failed" ? "Yeni analiz ekranını açar" : "Analizi açar"}
              onPress={() =>
                a.status === "failed" ? navigation.popTo("Upload") : navigation.navigate("Analysis", { id: a.analysis_id })
              }
              style={styles.open}
            >
              <Text style={{ color: c.text, fontWeight: "600" }}>{a.target_role.name}</Text>
              <Text style={{ color: c.muted }}>
                {formatDate(a.created_at, true)} · {result}
              </Text>
            </Pressable>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`${label} analizini sil`}
              onPress={() => confirmDelete(a)}
              style={styles.delete}
            >
              <Text style={{ color: c.error }}>Sil</Text>
            </Pressable>
          </View>
        );
      }}
    />
  );
}

const styles = StyleSheet.create({
  failed: { padding: 20, gap: 12 },
  list: { padding: 20, gap: 10, flexGrow: 1 },
  row: { flexDirection: "row", alignItems: "center", borderWidth: 1, borderRadius: 10 },
  open: { flex: 1, padding: 14, gap: 2, minHeight: 56 },
  delete: { minWidth: 56, minHeight: 56, alignItems: "center", justifyContent: "center" },
});

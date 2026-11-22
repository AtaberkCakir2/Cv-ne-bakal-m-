import { StatusBar } from "expo-status-bar";
import { useCallback, useEffect, useState } from "react";
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from "react-native";

import { api, problemMessage, unwrap } from "./src/api/client";
import { API_URL } from "./src/config";

type Health = { state: "loading" } | { state: "ok" } | { state: "error"; message: string };

/**
 * T-060 iskeleti: tipli istemciyle backend sağlığını gösterir (web'deki /durum sayfasının karşılığı).
 * Giriş, KVKK onayı ve CV yükleme ekranları T-061'de.
 */
export default function App() {
  const [health, setHealth] = useState<Health>({ state: "loading" });

  const check = useCallback(async () => {
    setHealth({ state: "loading" });
    try {
      unwrap(await api.GET("/api/v1/health"));
      setHealth({ state: "ok" });
    } catch (error) {
      setHealth({ state: "error", message: problemMessage(error) });
    }
  }, []);

  useEffect(() => {
    void check();
  }, [check]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Cv'ne Bakalım!</Text>
      <Text style={styles.muted}>{API_URL}</Text>
      {health.state === "loading" && <ActivityIndicator accessibilityLabel="Sunucu kontrol ediliyor" />}
      {health.state === "ok" && <Text style={styles.ok}>Sunucu çalışıyor</Text>}
      {health.state === "error" && <Text style={styles.error}>{health.message}</Text>}
      <Pressable accessibilityRole="button" onPress={() => void check()} style={styles.button}>
        <Text style={styles.buttonText}>Tekrar dene</Text>
      </Pressable>
      <StatusBar style="auto" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#fff", alignItems: "center", justifyContent: "center", gap: 12, padding: 24 },
  title: { fontSize: 24, fontWeight: "700" },
  muted: { color: "#555" },
  ok: { color: "#126b2f" },
  error: { color: "#a11a1a", textAlign: "center" },
  button: { paddingHorizontal: 16, paddingVertical: 10, borderRadius: 8, backgroundColor: "#1d4ed8" },
  buttonText: { color: "#fff", fontWeight: "600" },
});

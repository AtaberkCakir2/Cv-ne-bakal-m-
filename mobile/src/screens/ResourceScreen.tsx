import { Linking, StyleSheet, Text, View } from "react-native";

import { isWebUrl, LANGUAGE, LEVEL, PROVIDER } from "../analysis/format";
import type { ScreenProps } from "../navigation";
import { Body, Button, Screen, Title } from "../ui";
import { useColors } from "../ui/theme";

/** T-062: kaynak detayı (web'deki ResourceDetail penceresinin karşılığı). Bağlantı tarayıcıda açılır. */
export function ResourceScreen({ route, navigation }: ScreenProps<"Resource">) {
  const c = useColors();
  const { resource, skill, demand } = route.params;
  const rows: [string, string][] = [
    ["Yetkinlik", `${skill} (${demand})`],
    ["Sağlayıcı", PROVIDER[resource.provider]],
    ["Seviye", LEVEL[resource.level]],
    ...(resource.duration_min != null ? [["Süre", `${resource.duration_min} dk`] as [string, string]] : []),
    ...(resource.language ? [["Dil", LANGUAGE[resource.language]] as [string, string]] : []),
    ["Ücret", resource.is_free ? "Ücretsiz" : "Ücretli"],
  ];
  return (
    <Screen>
      <Title>{resource.title}</Title>
      <View style={styles.rows}>
        {rows.map(([k, v]) => (
          <View key={k} accessible style={[styles.row, { borderColor: c.border }]}>
            <Text style={{ color: c.muted, width: 96 }}>{k}</Text>
            <Text style={{ color: c.text, flex: 1 }}>{v}</Text>
          </View>
        ))}
      </View>
      {resource.reason && (
        <Body>
          <Text style={{ fontWeight: "700" }}>Neden önerildi? </Text>
          {resource.reason}
        </Body>
      )}
      {isWebUrl(resource.url) && (
        <Button title="Kaynağa git (tarayıcıda açılır)" onPress={() => void Linking.openURL(resource.url)} />
      )}
      <Button variant="secondary" title="Geri" onPress={() => navigation.goBack()} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  rows: { gap: 0 },
  row: { flexDirection: "row", gap: 12, paddingVertical: 10, borderBottomWidth: StyleSheet.hairlineWidth },
});

import type { ComponentRef, ReactNode, Ref } from "react";
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";

import { useColors } from "./theme";

/** Kaydırılabilir ekran gövdesi; klavye açılınca alanlar görünür kalır. */
export function Screen({ children }: { children: ReactNode }) {
  const c = useColors();
  return (
    <KeyboardAvoidingView style={{ flex: 1, backgroundColor: c.bg }} behavior={Platform.OS === "ios" ? "padding" : undefined}>
      <ScrollView contentContainerStyle={styles.screen} keyboardShouldPersistTaps="handled">
        {children}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

export function Title({ children }: { children: ReactNode }) {
  const c = useColors();
  return (
    <Text accessibilityRole="header" style={[styles.title, { color: c.text }]}>
      {children}
    </Text>
  );
}

export function Body({ children, muted }: { children: ReactNode; muted?: boolean }) {
  const c = useColors();
  return <Text style={[styles.body, { color: muted ? c.muted : c.text }]}>{children}</Text>;
}

type Tone = "error" | "success" | "info" | "warning";

/** Bilgi/hata kutusu; hata ve başarı ekran okuyucuya hemen okunur. */
export function Alert({ tone, children }: { tone: Tone; children: ReactNode }) {
  const c = useColors();
  return (
    <View
      accessibilityLiveRegion={tone === "error" ? "assertive" : "polite"}
      accessibilityRole={tone === "error" ? "alert" : undefined}
      style={[styles.alert, { backgroundColor: c[`${tone}Bg`], borderColor: c[tone] }]}
    >
      <Text style={{ color: c[tone] }}>{children}</Text>
    </View>
  );
}

export function Button({
  title,
  onPress,
  loading,
  disabled,
  variant = "primary",
}: {
  title: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
  variant?: "primary" | "secondary" | "link";
}) {
  const c = useColors();
  const off = disabled || loading;
  const primary = variant === "primary";
  return (
    <Pressable
      accessibilityRole={variant === "link" ? "link" : "button"}
      accessibilityState={{ disabled: off, busy: loading }}
      disabled={off}
      onPress={onPress}
      style={({ pressed }) => [
        variant === "link" ? styles.link : styles.button,
        primary && { backgroundColor: c.primary },
        variant === "secondary" && { borderColor: c.primary, borderWidth: 1 },
        (pressed || off) && { opacity: 0.6 },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={primary ? c.onPrimary : c.primary} accessibilityLabel="İşleniyor" />
      ) : (
        <Text style={[styles.buttonText, { color: primary ? c.onPrimary : c.primary }]}>{title}</Text>
      )}
    </Pressable>
  );
}

export type TextInputRef = ComponentRef<typeof TextInput>;
type FieldProps = TextInputProps & { label: string; error?: string; hint?: string; ref?: Ref<TextInputRef> };

/** Etiketli metin alanı; hata alanın altında ve erişilebilirlik etiketinde. */
export function Field({ label, error, hint, style, ref, ...rest }: FieldProps) {
  const c = useColors();
  return (
    <View style={styles.field}>
      <Text style={[styles.label, { color: c.text }]}>{label}</Text>
      <TextInput
        ref={ref}
        accessibilityLabel={label}
        accessibilityHint={error ?? hint}
        placeholderTextColor={c.muted}
        style={[styles.input, { color: c.text, borderColor: error ? c.error : c.border, backgroundColor: c.surface }, style]}
        {...rest}
      />
      {hint && !error && <Text style={{ color: c.muted }}>{hint}</Text>}
      {error && <Text style={{ color: c.error }}>{error}</Text>}
    </View>
  );
}

export function Checkbox({
  label,
  checked,
  onChange,
  error,
  link,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
  error?: string;
  link?: { title: string; onPress: () => void };
}) {
  const c = useColors();
  return (
    <View style={styles.field}>
      <Pressable
        accessibilityRole="checkbox"
        accessibilityState={{ checked }}
        accessibilityHint={error}
        onPress={() => onChange(!checked)}
        style={styles.checkRow}
      >
        <View style={[styles.box, { borderColor: error ? c.error : c.border }, checked && { backgroundColor: c.primary, borderColor: c.primary }]}>
          {checked && <Text style={{ color: c.onPrimary, fontWeight: "700" }}>✓</Text>}
        </View>
        <Text style={[styles.checkLabel, { color: c.text }]}>{label}</Text>
      </Pressable>
      {link && <Button variant="link" title={link.title} onPress={link.onPress} />}
      {error && <Text style={{ color: c.error }}>{error}</Text>}
    </View>
  );
}

export function Loading({ label }: { label: string }) {
  const c = useColors();
  return (
    <View style={[styles.center, { backgroundColor: c.bg }]}>
      <ActivityIndicator size="large" color={c.primary} accessibilityLabel={label} />
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { padding: 20, gap: 14, flexGrow: 1 },
  title: { fontSize: 24, fontWeight: "700" },
  body: { fontSize: 15, lineHeight: 21 },
  alert: { borderWidth: 1, borderRadius: 8, padding: 12 },
  button: { minHeight: 48, borderRadius: 8, alignItems: "center", justifyContent: "center", paddingHorizontal: 16 },
  link: { minHeight: 44, justifyContent: "center", alignSelf: "flex-start" },
  buttonText: { fontSize: 16, fontWeight: "600" },
  field: { gap: 4 },
  label: { fontWeight: "600" },
  input: { minHeight: 48, borderWidth: 1, borderRadius: 8, paddingHorizontal: 12, fontSize: 16 },
  checkRow: { flexDirection: "row", alignItems: "flex-start", gap: 10, minHeight: 44, paddingVertical: 4 },
  box: { width: 24, height: 24, borderWidth: 2, borderRadius: 4, alignItems: "center", justifyContent: "center" },
  checkLabel: { flex: 1, fontSize: 15, lineHeight: 21 },
  center: { flex: 1, alignItems: "center", justifyContent: "center" },
});

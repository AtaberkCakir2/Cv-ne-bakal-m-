import { useColorScheme } from "react-native";

/**
 * Renkler web'deki tasarım değerleriyle aynı aileden (web/src/ui/tokens.css): mavi ana renk, açık/koyu tema.
 * Metin/zemin çiftleri WCAG AA kontrastını sağlar.
 */
const light = {
  bg: "#f7f8fa",
  surface: "#ffffff",
  text: "#111827",
  muted: "#4b5563",
  border: "#d1d5db",
  primary: "#1d4ed8",
  onPrimary: "#ffffff",
  error: "#b91c1c",
  errorBg: "#fef2f2",
  success: "#166534",
  successBg: "#f0fdf4",
  info: "#1e3a8a",
  infoBg: "#eff6ff",
  warning: "#92400e",
  warningBg: "#fffbeb",
};

const dark: typeof light = {
  bg: "#0b1220",
  surface: "#111a2e",
  text: "#f3f4f6",
  muted: "#a3acbd",
  border: "#334155",
  primary: "#60a5fa",
  onPrimary: "#0b1220",
  error: "#fca5a5",
  errorBg: "#3b1111",
  success: "#86efac",
  successBg: "#0f2a1a",
  info: "#bfdbfe",
  infoBg: "#14213d",
  warning: "#fcd34d",
  warningBg: "#33260a",
};

export type Colors = typeof light;

export function useColors(): Colors {
  return useColorScheme() === "dark" ? dark : light;
}

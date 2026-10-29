export type Theme = "light" | "dark" | "system";

const KEY = "careerai-theme";

/** Tercih tarayıcıda saklanır; erişilemezse (gizli pencere vb.) sistem tercihine düşer. */
export function loadTheme(): Theme {
  try {
    const v = localStorage.getItem(KEY);
    return v === "light" || v === "dark" ? v : "system";
  } catch {
    return "system";
  }
}

export function applyTheme(theme: Theme): void {
  const root = document.documentElement;
  if (theme === "system") root.removeAttribute("data-theme");
  else root.setAttribute("data-theme", theme);
  try {
    if (theme === "system") localStorage.removeItem(KEY);
    else localStorage.setItem(KEY, theme);
  } catch {
    // Saklanamazsa tema sadece bu oturumda geçerli olur.
  }
}

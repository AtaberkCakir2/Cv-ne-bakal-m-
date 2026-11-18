import { useState } from "react";

import { applyTheme, loadTheme, type Theme } from "./theme";

const LABELS: Record<Theme, string> = { system: "Sistem", light: "Açık", dark: "Koyu" };

export function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(loadTheme);
  return (
    <label>
      <span className="visually-hidden">Tema</span>
      <select
        className="field__input"
        value={theme}
        onChange={(e) => {
          const next = e.target.value as Theme;
          setTheme(next);
          applyTheme(next);
        }}
      >
        {(Object.keys(LABELS) as Theme[]).map((t) => (
          <option key={t} value={t}>
            {LABELS[t]} tema
          </option>
        ))}
      </select>
    </label>
  );
}

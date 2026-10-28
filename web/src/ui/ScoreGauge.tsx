import type { CSSProperties } from "react";

/** Uyum skoru halkası (0–100). Görsel halka gizli; ekran okuyucu metni okur. */
export function ScoreGauge({ score, label = "Uyum skoru" }: { score: number; label?: string }) {
  const value = Number.isFinite(score) ? Math.round(Math.min(100, Math.max(0, score))) : 0;
  return (
    <div className="gauge" style={{ "--value": value } as CSSProperties} role="img" aria-label={`${label}: 100 üzerinden ${value}`}>
      <div className="gauge__inner" aria-hidden="true">
        <span>
          {value}
          <span className="gauge__unit">/ 100</span>
        </span>
      </div>
    </div>
  );
}

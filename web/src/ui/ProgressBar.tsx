/**
 * 0–1 arası oran. Ekran okuyucu `label`'ı ve yüzdeyi okur; `valueText` verilirse yüzde yerine o okunur.
 * Geçersiz değer (NaN, eksik alan) 0 sayılır.
 */
export function ProgressBar({ value, label, valueText }: { value: number; label: string; valueText?: string }) {
  const pct = Number.isFinite(value) ? Math.round(Math.min(1, Math.max(0, value)) * 100) : 0;
  return (
    <div
      className="progress"
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={pct}
      aria-valuetext={valueText}
    >
      <div className="progress__fill" style={{ width: `${pct}%` }} />
    </div>
  );
}

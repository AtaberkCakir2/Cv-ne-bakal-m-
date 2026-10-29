import { ProgressBar } from "./ProgressBar";

export interface DemandItem {
  label: string;
  /** 0–1: bu yetkinliği isteyen ilanların oranı (contracts: missing_skills[].demand_ratio). */
  ratio: number;
}

/** Yatay çubuk grafik: eksik yetkinliklerin ilanlardaki talep oranı. Değer metin olarak da yazılır, renge bağlı kalmaz. */
export function DemandBars({ items, caption }: { items: DemandItem[]; caption: string }) {
  return (
    <figure style={{ margin: 0 }}>
      <figcaption className="visually-hidden">{caption}</figcaption>
      <ul className="bars">
        {items.map((item) => {
          const pct = Number.isFinite(item.ratio) ? Math.round(item.ratio * 100) : 0;
          return (
            <li key={item.label} className="bars__row">
              <span aria-hidden="true">{item.label}</span>
              <ProgressBar value={item.ratio} label={item.label} valueText={`ilanların %${pct} kadarı istiyor`} />
              <span className="bars__value" aria-hidden="true">
                %{pct}
              </span>
            </li>
          );
        })}
      </ul>
    </figure>
  );
}

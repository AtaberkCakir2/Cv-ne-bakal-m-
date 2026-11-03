import type { ReactNode } from "react";

/** Yetkinlik etiketi; `meta` seviye gibi ikincil bilgi için. */
export function Chip({ children, meta }: { children: ReactNode; meta?: ReactNode }) {
  return (
    <span className="chip">
      {children}
      {meta && <span className="chip__meta">{meta}</span>}
    </span>
  );
}

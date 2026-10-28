import type { ReactNode } from "react";

type Props = {
  tone?: "info" | "error" | "success" | "warning";
  title?: string;
  /**
   * Hata uyarıları sonradan çıktığında ekran okuyucu hemen okur (role="alert"). Diğerleri varsayılan olarak sessizdir:
   * sayfada sabit duran "Az ilan verisi" gibi uyarılar her açılışta okumayı kesmesin. Sonradan çıkan bilgi/başarı
   * mesajı için `live` verin; bu durumda Alert, içerik değişmeden önce sayfada bulunmalı (koşullu render değil).
   */
  live?: boolean;
  children: ReactNode;
};

export function Alert({ tone = "info", title, live, children }: Props) {
  const role = tone === "error" ? "alert" : live ? "status" : undefined;
  return (
    <div className={`alert alert--${tone}`} role={role}>
      {title && <strong>{title}</strong>}
      <div className="alert__body">{children}</div>
    </div>
  );
}

import type { ButtonHTMLAttributes } from "react";

import { Spinner } from "./Spinner";

type Props = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
  block?: boolean;
  /**
   * İstek sürerken tıklamayı yok sayar. `disabled` yerine `aria-disabled` kullanılır: düğme odağı kaybetmez
   * (gönderimden sonra odak sayfanın başına düşmez) ve ekran okuyucu "İşleniyor" metnini okur.
   */
  loading?: boolean;
};

export function Button({ variant = "primary", block, loading, className, children, type = "button", onClick, ...rest }: Props) {
  const classes = ["btn", variant !== "primary" && `btn--${variant}`, block && "btn--block", className]
    .filter(Boolean)
    .join(" ");
  return (
    <button
      {...rest}
      type={type}
      className={classes}
      aria-disabled={loading || rest["aria-disabled"]}
      onClick={(e) => {
        if (loading) {
          e.preventDefault(); // submit düğmesinde formu da göndermez
          return;
        }
        onClick?.(e);
      }}
    >
      {loading && <Spinner label="" />}
      {loading && <span className="visually-hidden">İşleniyor: </span>}
      {children}
    </button>
  );
}

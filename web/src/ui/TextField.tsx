import { useId, type InputHTMLAttributes } from "react";

type Props = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
  hint?: string;
  /**
   * Doluysa alan hatalı işaretlenir ve mesaj alanla birlikte okunur. Mesaj sonradan çıktığında ekran okuyucu
   * hemen okur (role="alert"); formlar gönderimde ayrıca ilk hatalı alana odaklanmalı.
   */
  error?: string;
};

export function TextField({ label, hint, error, id, className, "aria-describedby": describedBy, ...rest }: Props) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const hintId = hint ? `${inputId}-hint` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;
  return (
    <div className="field">
      <label className="field__label" htmlFor={inputId}>
        {label}
      </label>
      <input
        {...rest}
        id={inputId}
        className={["field__input", className].filter(Boolean).join(" ")}
        aria-invalid={error ? true : rest["aria-invalid"]}
        aria-describedby={[describedBy, hintId, errorId].filter(Boolean).join(" ") || undefined}
      />
      {hint && (
        <span id={hintId} className="field__hint">
          {hint}
        </span>
      )}
      {error && (
        <span id={errorId} className="field__error" role="alert">
          {error}
        </span>
      )}
    </div>
  );
}

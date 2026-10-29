import { useId, type InputHTMLAttributes, type ReactNode } from "react";

type Props = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  label: ReactNode;
  hint?: ReactNode;
  /** Zorunlu onay verilmediğinde (ör. KVKK) gösterilir; TextField ile aynı şekilde bağlanır. */
  error?: string;
};

/** KVKK onayları gibi zorunlu kutular için; etiket tıklanabilir. */
export function Checkbox({ label, hint, error, id, "aria-describedby": describedBy, ...rest }: Props) {
  const autoId = useId();
  const inputId = id ?? autoId;
  const hintId = hint ? `${inputId}-hint` : undefined;
  const errorId = error ? `${inputId}-error` : undefined;
  return (
    <div className="field">
      <div className="checkbox">
        <input
          {...rest}
          id={inputId}
          type="checkbox"
          aria-invalid={error ? true : rest["aria-invalid"]}
          aria-describedby={[describedBy, hintId, errorId].filter(Boolean).join(" ") || undefined}
        />
        <label htmlFor={inputId}>{label}</label>
      </div>
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

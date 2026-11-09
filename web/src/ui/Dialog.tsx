import { useEffect, useId, useRef, type ReactNode } from "react";

type Props = {
  open: boolean;
  title: ReactNode;
  onClose: () => void;
  children: ReactNode;
};

/**
 * Yerel <dialog> ile pop-up (showModal): odak içeride kalır, Esc kapatır, arka plan ekran okuyucudan gizlenir.
 * Kapanınca odak, açılmadan önceki öğeye (ör. kaynak kartı) döner. Arka plana tıklamak da kapatır.
 */
export function Dialog({ open, title, onClose, children }: Props) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();

  useEffect(() => {
    const dialog = ref.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      const opener = document.activeElement as HTMLElement | null;
      dialog.showModal();
      return () => {
        if (dialog.open) dialog.close();
        opener?.focus();
      };
    }
  }, [open]);

  return (
    <dialog
      ref={ref}
      className="dialog"
      aria-labelledby={titleId}
      onClose={onClose}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose(); // kenar boşluğu = arka plan
      }}
    >
      {open && (
        <div className="dialog__body">
          <h2 id={titleId} className="dialog__title">
            {title}
          </h2>
          {children}
        </div>
      )}
    </dialog>
  );
}

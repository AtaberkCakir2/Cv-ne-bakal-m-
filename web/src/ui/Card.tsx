import { useEffect, useRef, type HTMLAttributes, type ReactNode } from "react";

type Props = Omit<HTMLAttributes<HTMLElement>, "title"> & {
  title?: ReactNode;
  /** Başlık sırası bozulmasın: sayfanın tek kartıysa h1, sayfa h1'i altındaki kart h2, kart içindeki kart h3. */
  headingLevel?: 1 | 2 | 3 | 4;
  /**
   * Kart açılınca odağı başlığa taşır. Form yerine sonuç ekranı geldiğinde ("E-postanı kontrol et") odak kaybolmasın
   * ve ekran okuyucu yeni içeriği başlıktan itibaren okusun.
   */
  focusTitle?: boolean;
};

export function Card({ title, headingLevel = 2, focusTitle, className, children, ...rest }: Props) {
  const Heading = `h${headingLevel}` as const;
  const headingRef = useRef<HTMLHeadingElement>(null);
  useEffect(() => {
    if (focusTitle) headingRef.current?.focus();
  }, [focusTitle]);
  return (
    <section {...rest} className={["card", className].filter(Boolean).join(" ")}>
      {title && (
        <Heading ref={headingRef} className="card__title" tabIndex={focusTitle ? -1 : undefined}>
          {title}
        </Heading>
      )}
      {children}
    </section>
  );
}

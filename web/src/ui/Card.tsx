import type { HTMLAttributes, ReactNode } from "react";

type Props = Omit<HTMLAttributes<HTMLElement>, "title"> & {
  title?: ReactNode;
  /** Başlık sırası bozulmasın: sayfa h1'i altındaki kart h2, kart içindeki kart h3 olmalı. */
  headingLevel?: 2 | 3 | 4;
};

export function Card({ title, headingLevel = 2, className, children, ...rest }: Props) {
  const Heading = `h${headingLevel}` as const;
  return (
    <section {...rest} className={["card", className].filter(Boolean).join(" ")}>
      {title && <Heading className="card__title">{title}</Heading>}
      {children}
    </section>
  );
}

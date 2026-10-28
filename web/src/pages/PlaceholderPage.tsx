/** Henüz yapılmamış ekranlar için geçici sayfa; tasarım web/prototip'te. */
export function PlaceholderPage({ title, note }: { title: string; note?: string }) {
  return (
    <section>
      <h1>{title}</h1>
      {note && <p>{note}</p>}
      <p className="muted">Bu ekran henüz yapım aşamasında.</p>
    </section>
  );
}

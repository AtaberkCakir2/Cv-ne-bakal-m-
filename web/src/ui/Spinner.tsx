/** `label` boşsa süs olarak gizlenir (ör. düğme içinde; düğme kendi "İşleniyor" metnini taşır). */
export function Spinner({ label = "Yükleniyor" }: { label?: string }) {
  if (!label) return <span className="spinner" aria-hidden="true" />;
  // Canlı bölgeler içerikten okunur; aria-label çoğu ekran okuyucuda okunmaz.
  return (
    <span role="status">
      <span className="spinner" aria-hidden="true" />
      <span className="visually-hidden">{label}</span>
    </span>
  );
}

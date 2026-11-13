/**
 * İlan veya ilan sayısı gösterilen her yerde zorunlu kaynak atfı (scraper/kaynak-uygunluk.md kural 7).
 * Kaynaklar API şartları gereği adıyla ve sitesine linkle anılır; Remote OK linki "follow" kalır (nofollow yok),
 * hiçbir kaynağın logosu kullanılmaz. Liste değişirse önce o dosya güncellenir.
 */
const SOURCES = [
  { name: "Remotive", url: "https://remotive.com" },
  { name: "Himalayas", url: "https://himalayas.app" },
  { name: "Remote OK", url: "https://remoteok.com" },
  { name: "Hacker News", url: "https://news.ycombinator.com" },
  { name: "Arbeitnow", url: "https://www.arbeitnow.com" },
  { name: "Jobicy", url: "https://jobicy.com" },
];

export function SourceAttribution() {
  return (
    <footer className="attribution">
      <p>
        İlan verileri:{" "}
        {SOURCES.map((s, i) => (
          <span key={s.name}>
            {i > 0 && ", "}
            <a href={s.url} target="_blank" rel="noopener">
              {s.name}
              <span className="visually-hidden"> (yeni sekmede açılır)</span>
            </a>
          </span>
        ))}
        .
      </p>
      <p lang="en">This service uses the ESCO classification of the European Commission.</p>
    </footer>
  );
}

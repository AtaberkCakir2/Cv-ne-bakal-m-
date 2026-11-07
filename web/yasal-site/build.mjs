/**
 * Tanıtım ve yasal sayfaları docs/yasal/*.md'den statik HTML olarak üretir (T-065, karar #30, go-live #52).
 * Çıktı Cloudflare Pages'te yayımlanır; uygulamanın çalıştığı bilgisayar kapalıyken de açılır.
 *
 *   npm run build:yasal          → yasal-site/dist/
 *   ACIK_RIZA=1 npm run build:yasal   (açık rıza metni de yayımlansın: docs/yasal/README.md madde 3)
 *
 * Metin tek yerde durur: HTML elle düzenlenmez, Markdown değişir ve yeniden üretilir.
 */
import { copyFileSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { Marked } from "marked";

const HERE = dirname(fileURLToPath(import.meta.url));
const DOCS = join(HERE, "..", "..", "docs", "yasal");
const OUT = join(HERE, "dist");
const APP_URL = process.env.APP_URL ?? "https://app.cvnebakalim.com";

/** Sayfa adresi ← kaynak dosya. Sıra, alt bilgideki bağlantı sırasıdır. */
const PAGES = [
  { slug: "aydinlatma", file: "aydinlatma-metni.md", nav: "Aydınlatma Metni" },
  { slug: "gizlilik", file: "gizlilik-politikasi.md", nav: "Gizlilik Politikası" },
  { slug: "kullanim-kosullari", file: "kullanim-kosullari.md", nav: "Kullanım Koşulları" },
  { slug: "hesap-silme", file: "hesap-silme.md", nav: "Hesap Silme" },
  ...(process.env.ACIK_RIZA === "1" ? [{ slug: "acik-riza", file: "acik-riza.md", nav: "Açık Rıza" }] : []),
];
const BY_FILE = new Map(PAGES.map((p) => [p.file, p.slug]));
// acik-riza.md uygulama içi yolları kullanıyor ("./aydinlatma"); onlar da site adresine çevrilir.
const BY_SLUG = new Set(PAGES.map((p) => p.slug));

/** GitHub'ın başlık kimliğiyle aynı: metinlerdeki "aydinlatma-metni.md#4-kimlere-aktarılıyor" bağlantıları çalışsın. */
function slugify(text) {
  return text
    .toLowerCase()
    .replace(/[^\p{L}\p{M}\p{N}\s-]/gu, "")
    .trim()
    .replace(/\s/g, "-");
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
}

/** Kaynak bağlantısını site adresine çevirir; bilinmeyen .md bağlantısı derlemeyi durdurur (kırık link yayımlanmasın). */
function rewriteHref(href, from) {
  if (/^(https?:|mailto:|#)/.test(href)) return href;
  const [path, hash] = href.split("#");
  const name = path.replace(/^\.\//, "");
  const slug = BY_FILE.get(name) ?? (BY_SLUG.has(name) ? name : undefined);
  if (!slug) throw new Error(`${from}: bilinmeyen bağlantı "${href}" (sayfa yayımlanmıyor olabilir)`);
  return `../${slug}/${hash ? `#${hash}` : ""}`;
}

function render(markdown, from) {
  const marked = new Marked({
    gfm: true,
    renderer: {
      heading({ tokens, depth }) {
        const text = this.parser.parseInline(tokens);
        const plain = text.replace(/<[^>]+>/g, "").replace(/&(#\d+|\w+);/g, "");
        return `<h${depth} id="${escapeHtml(slugify(plain))}">${text}</h${depth}>\n`;
      },
      link({ href, title, tokens }) {
        const text = this.parser.parseInline(tokens);
        const attrs = /^https?:/.test(href) ? ' rel="noopener"' : "";
        const t = title ? ` title="${escapeHtml(title)}"` : "";
        return `<a href="${escapeHtml(rewriteHref(href, from))}"${t}${attrs}>${text}</a>`;
      },
      // Kaynakta HTML yazılmaz; yazılırsa metin olarak gösterilir. Tek istisna prepare'in eklediği işaret etiketi.
      html({ text }) {
        return /^<\/?mark( class="todo")?>$/.test(text) ? text : escapeHtml(text);
      },
    },
  });
  return marked.parse(markdown);
}

/**
 * Kaynak dosyayı yayına hazırlar: ekip için yazılmış "> TASLAK …" notu sayfada çıkmaz, yerine genel bir uyarı konur.
 * Henüz kararı verilmemiş "[…]" yerleri işaretlenir; yayımlanacak sürümde hiç kalmamalı.
 */
function prepare(file) {
  const raw = readFileSync(join(DOCS, file), "utf8").replace(/\r\n/g, "\n");
  const lines = raw.split("\n");
  const isNote = (l) => /^>\s*\**TASLAK/.test(l);
  const draft = lines.some(isNote);
  const kept = [];
  let inNote = false;
  for (const line of lines) {
    if (isNote(line)) inNote = true;
    else if (inNote && !line.startsWith(">")) inNote = false;
    if (!inNote) kept.push(line);
  }
  const titleLine = kept.find((l) => l.startsWith("# "));
  if (!titleLine) throw new Error(`${file}: "# " ile başlayan başlık yok`);
  return { draft, title: titleLine.slice(2).trim(), body: kept.join("\n") };
}

function page({ title, bodyHtml, draft, depth }) {
  const up = depth ? "../" : "";
  const nav = PAGES.map((p) => `<a href="${up}${p.slug}/">${p.nav}</a>`).join("\n        ");
  return `<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${escapeHtml(title)}</title>
  ${draft ? '<meta name="robots" content="noindex, nofollow">\n  ' : ""}<link rel="stylesheet" href="${up}tokens.css">
  <link rel="stylesheet" href="${up}site.css">
</head>
<body>
  <a class="skip" href="#icerik">İçeriğe geç</a>
  <header class="top">
    <a class="brand" href="${up || "./"}">CareerAI</a>
    <a href="${escapeHtml(APP_URL)}">Uygulamaya git</a>
  </header>
  <main id="icerik">
    ${draft ? '<p class="draft" role="note"><strong>Taslak:</strong> Bu metin henüz hukuki incelemeden geçmedi ve yürürlükte değildir. Köşeli parantezli yerler kesinleşmedi.</p>\n    ' : ""}${bodyHtml}
  </main>
  <footer class="bottom">
    <nav aria-label="Yasal sayfalar">
        ${nav}
    </nav>
  </footer>
</body>
</html>
`;
}

const HOME = `# CareerAI

CareerAI, öğrencinin CV'sini seçtiği hedef pozisyon için toplanan güncel iş ilanlarıyla karşılaştırır, eksik yetkinlikleri ilanlardaki talep oranıyla birlikte gösterir ve bu eksikleri kapatmak için doğrulanmış eğitim kaynakları önerir. Bitirme projesi olarak geliştirilen ücretsiz bir hizmettir.

- **CV'niz saklanmaz.** Dosya sadece analiz sırasında işlenir; kalıcı olarak sadece çıkarılan yetkinlikler, dosyanın parmak izi ve sayfa sayısı tutulur.
- **CV'niz yapay zeka şirketlerine gitmez.** Analiz, yerel bir dil modeliyle yapılır; kişisel bilgiler modele verilmeden önce maskelenir.
- **Öneriler uydurma değildir.** Kaynak bağlantıları yalnızca ekibin doğruladığı listeden seçilir.

## Yasal metinler

${PAGES.map((p) => `- [${p.nav}](${p.file})`).join("\n")}
`;

rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });
copyFileSync(join(HERE, "..", "src", "ui", "tokens.css"), join(OUT, "tokens.css"));
copyFileSync(join(HERE, "site.css"), join(OUT, "site.css"));

let anyDraft = false;
for (const p of PAGES) {
  const { draft, title, body } = prepare(p.file);
  anyDraft ||= draft;
  const html = render(body.replace(/\[([^\][\n`]+)\](?![(:[])/g, '<mark class="todo">[$1]</mark>'), p.file);
  mkdirSync(join(OUT, p.slug), { recursive: true });
  writeFileSync(join(OUT, p.slug, "index.html"), page({ title: `${title} · CareerAI`, bodyHtml: html, draft, depth: 1 }));
}
// Ana sayfadaki bağlantılar alt klasörden değil kökten: "../x/" yerine "x/".
const homeHtml = render(HOME, "ana sayfa").replaceAll('href="../', 'href="');
writeFileSync(join(OUT, "index.html"), page({ title: "CareerAI", bodyHtml: homeHtml, draft: anyDraft, depth: 0 }));

// Cloudflare Pages başlıkları: taslakken arama motorlarına kapalı; sayfa başka sitede çerçeve içine alınamaz.
writeFileSync(
  join(OUT, "_headers"),
  `/*
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: strict-origin-when-cross-origin
  Content-Security-Policy: default-src 'none'; style-src 'self'; img-src 'self'; base-uri 'none'; form-action 'none'; frame-ancestors 'none'
${anyDraft ? "  X-Robots-Tag: noindex, nofollow\n" : ""}`,
);
console.log(`Yasal sayfalar: ${OUT} (${PAGES.length} sayfa + ana sayfa${anyDraft ? ", TASLAK" : ""})`);

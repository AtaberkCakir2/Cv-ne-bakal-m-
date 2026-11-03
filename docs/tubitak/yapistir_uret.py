"""2209a-basvuru-taslagi.md → 2209a-basvuru-yapistir.html (TYBS'ye yapıştırmaya hazır sürüm).

Markdown değişince yeniden çalıştırın (repo kökünden):
    python docs/tubitak/yapistir_uret.py

Gerekli paket: markdown (pip install markdown==3.7). Her TYBS metin kutusu için ayrı bir blok ve "Kopyala" düğmesi
üretir; tablolar HTML tablo olarak kopyalanır, TYBS editörüne tablo olarak yapışır. Karakter ve kelime sayısı
blokların üstünde görünür (Bilgi Notu: bölümler en az 350 karakter, özet 25–450 kelime).
"""

import html
import re
from pathlib import Path

import markdown

HERE = Path(__file__).resolve().parent
SRC = HERE / "2209a-basvuru-taslagi.md"
OUT = HERE / "2209a-basvuru-yapistir.html"

# (başlık, kaynak bölüm başlığı, TYBS'deki yer, en az karakter, kelime sınırı)
BLOCKS = [
    ("Genel bilgiler (TYBS alanları)", "## C. TYBS genel bilgi alanları", "Başvurunun genel bilgi adımları", 0, None),
    ("Özet", "## ÖZET", "Özet", 0, (25, 450)),
    ("1.1. Konunun Önemi ve Bilimsel Niteliği", "### 1.1.", "1.1", 350, None),
    ("1.2. Amaç ve Hedefler", "### 1.2.", "1.2", 350, None),
    ("2. Yöntem", "## 2. YÖNTEM", "2", 350, None),
    ("3.1. Çalışma Takvimi", "### 3.1.", "3.1 (tablo)", 0, None),
    ("3.2. Risk Yönetimi", "### 3.2.", "3.2 (tablo)", 0, None),
    ("3.3. Araştırma Olanakları", "### 3.3.", "3.3", 0, None),
    ("4. Yaygın Etki", "## 4. ARAŞTIRMA", "4", 0, None),
    ("5. Belirtmek İstediğiniz Diğer Konular", "## 5. BELİRTMEK", "5", 0, None),
    ("6. Ekler", "## 6. EKLER", "6", 0, None),
    ("Kaynakça", "## KAYNAKLAR", "Kaynakça adımı", 0, None),
    ("Bütçe", "## 7. BÜTÇE", "Bütçe adımı (varsa)", 0, None),
]

_HEADING = re.compile(r"^(#{2,3}) ", re.MULTILINE)
_LIST_ITEM = re.compile(r"^\s*(?:[-*]|\d+\.) ")


def loosen_lists(md: str) -> str:
    """python-markdown listeden önce boş satır ister; "...şunlardır:" altındaki maddeleri de liste yapar."""
    out: list[str] = []
    for line in md.splitlines():
        prev = out[-1] if out else ""
        if _LIST_ITEM.match(line) and prev.strip() and not _LIST_ITEM.match(prev) and not prev.startswith(" "):
            out.append("")
        out.append(line)
    return "\n".join(out)


def section(text: str, start: str) -> str:
    """`start` ile başlayan başlığın altındaki metin; aynı veya üst düzeydeki bir sonraki başlıkta biter."""
    i = text.index(start)
    level = len(start.split(" ", 1)[0])
    body_start = text.index("\n", i) + 1
    end = len(text)
    for m in _HEADING.finditer(text, body_start):
        if len(m.group(1)) <= level:
            end = m.start()
            break
    body = text[body_start:end]
    return re.sub(r"\n---\s*$", "", body.strip()).strip()


def plain_length(md: str) -> tuple[int, int]:
    rendered = markdown.markdown(md, extensions=["tables"])
    plain = html.unescape(re.sub(r"<[^>]+>", " ", rendered))
    plain = re.sub(r"\s+", " ", plain).strip()
    return len(plain), len(plain.split())


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    cards = []
    for n, (title, start, where, min_chars, words) in enumerate(BLOCKS):
        md = loosen_lists(section(text, start))
        body = markdown.markdown(md, extensions=["tables"])
        chars, word_count = plain_length(md)
        checks = [f"{chars} karakter"]
        ok = chars >= min_chars
        if min_chars:
            checks.append(f"en az {min_chars}")
        if words:
            checks.append(f"{word_count} kelime ({words[0]}–{words[1]})")
            ok = ok and words[0] <= word_count <= words[1]
        status = "ok" if ok else "warn"
        cards.append(
            f'<section class="card"><header><div><h2>{html.escape(title)}</h2>'
            f'<p class="meta">TYBS: {html.escape(where)} · <span class="{status}">{" · ".join(checks)}</span></p></div>'
            f'<button type="button" data-target="b{n}">Kopyala</button></header>'
            f'<div class="body" id="b{n}">{body}</div></section>'
        )
    OUT.write_text(TEMPLATE.replace("{{CARDS}}", "\n".join(cards)), encoding="utf-8")
    print(f"{len(cards)} blok yazıldı: {OUT}")


TEMPLATE = """<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>2209-A Başvuru Metni</title>
<style>
:root { --bg:#f6f7f9; --card:#fff; --fg:#1d2330; --muted:#5b6475; --line:#d9dde5; --accent:#1f5fbf;
        --ok:#1f7a3a; --warn:#b3261e; --mark:#fff3b0; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#14171c; --card:#1d2128; --fg:#e7eaf0; --muted:#9aa3b2; --line:#333a45; --accent:#7fb0ff;
          --ok:#6fd08c; --warn:#ff8a80; --mark:#5c4d00; }
}
* { box-sizing: border-box; }
body { margin:0; background:var(--bg); color:var(--fg); font:15px/1.55 system-ui, -apple-system, "Segoe UI", sans-serif; }
main { max-width: 960px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 22px; margin: 0 0 4px; }
.lead { color: var(--muted); margin: 0 0 20px; }
.card { background: var(--card); border: 1px solid var(--line); border-radius: 10px; margin: 0 0 18px; overflow: hidden; }
.card header { display:flex; justify-content:space-between; gap:12px; align-items:flex-start; padding:14px 16px; border-bottom:1px solid var(--line); }
.card h2 { font-size: 17px; margin: 0; }
.meta { margin: 2px 0 0; color: var(--muted); font-size: 13px; }
.ok { color: var(--ok); } .warn { color: var(--warn); font-weight: 600; }
button { flex: none; border: 1px solid var(--accent); background: transparent; color: var(--accent); border-radius: 8px;
         padding: 6px 14px; font: inherit; cursor: pointer; }
button.done { background: var(--accent); color: var(--card); }
.body { padding: 14px 16px; overflow-x: auto; }
.body table { border-collapse: collapse; width: 100%; margin: 8px 0; }
.body th, .body td { border: 1px solid var(--line); padding: 6px 8px; vertical-align: top; text-align: left; }
.body code { background: var(--mark); padding: 0 3px; border-radius: 3px; font-family: inherit; }
</style>
</head>
<body>
<main>
<h1>TÜBİTAK 2209-A · Yapıştırmaya hazır metin</h1>
<p class="lead">Her bloğun "Kopyala" düğmesine basıp TYBS'deki ilgili kutuya yapıştırın; ardından "Proje Önerisini Önizle" ile kontrol edin.
Sarı işaretli yerler doldurulmadan gönderilmemeli. Kaynak: <code>2209a-basvuru-taslagi.md</code> (değişirse <code>python docs/tubitak/yapistir_uret.py</code>).</p>
{{CARDS}}
</main>
<script>
document.querySelectorAll("button[data-target]").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const el = document.getElementById(btn.dataset.target);
    try {
      await navigator.clipboard.write([new ClipboardItem({
        "text/html": new Blob([el.innerHTML], { type: "text/html" }),
        "text/plain": new Blob([el.innerText], { type: "text/plain" }),
      })]);
    } catch (e) {
      const range = document.createRange(); range.selectNodeContents(el);
      const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(range);
      document.execCommand("copy"); sel.removeAllRanges();
    }
    btn.textContent = "Kopyalandı"; btn.classList.add("done");
    setTimeout(() => { btn.textContent = "Kopyala"; btn.classList.remove("done"); }, 1800);
  });
});
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()

// Testlerde kullanılan sahte, anonim CV (CLAUDE.md kural 4): gerçek kişi bilgisi yok, dosya repoda tutulmaz.
// Tek sayfalık, metin içeren geçerli bir PDF'i çalışma anında üretir (backend pypdf ile sayfa sayısını okur).

export function sahteCvPdf(): Buffer {
  const metin = [
    "Ornek Aday - Backend Gelistirici",
    "Yetkinlikler: Python, SQL, Git, REST API",
    "Deneyim: 2 yil web servisleri gelistirme (sahte veri)",
  ];
  const akis = ["BT", "/F1 12 Tf", "72 760 Td", "16 TL", ...metin.map((s) => `(${s}) Tj T*`), "ET"].join("\n");
  const nesneler = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    `<< /Length ${Buffer.byteLength(akis, "latin1")} >>\nstream\n${akis}\nendstream`,
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
  ];
  let pdf = "%PDF-1.4\n";
  const konumlar: number[] = [];
  nesneler.forEach((govde, i) => {
    konumlar.push(Buffer.byteLength(pdf, "latin1"));
    pdf += `${i + 1} 0 obj\n${govde}\nendobj\n`;
  });
  const xref = Buffer.byteLength(pdf, "latin1");
  pdf += `xref\n0 ${nesneler.length + 1}\n0000000000 65535 f \n`;
  pdf += konumlar.map((k) => `${String(k).padStart(10, "0")} 00000 n \n`).join("");
  pdf += `trailer\n<< /Size ${nesneler.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return Buffer.from(pdf, "latin1");
}

// Yük testi (T-072, k6). Kabul kriteri: 20 eşzamanlı kullanıcı, 30 dk; API p95 < 300 ms (analiz hariç), hata < %1.
// Çalıştırma: tests/yuk/README.md (bash tests/yuk/calistir.sh). Kullanıcılar sahte ve her çalıştırmada yenidir.
//
// İki senaryo:
//   gezinme: her sanal kullanıcı giriş yapar, pozisyon/yetkinlik/kaynak/profil/geçmiş uçlarını gezer (1–3 sn ara).
//   analiz:  aynı kullanıcılar seyrek olarak sahte CV yükler ve analizin bitmesini bekler; kuyruk + işçi süresi
//            `analiz_suresi` metriğine yazılır. Analiz uçları p95 hedefine dahil değildir (kriterde "analiz hariç").
import http from "k6/http";
import { check, sleep } from "k6";
import { Trend, Counter } from "k6/metrics";
import exec from "k6/execution";

const BASE = (__ENV.BASE_URL || "http://api:8000").replace(/\/$/, "") + "/api/v1";
const VUS = Number(__ENV.VUS || 20);
const SURE = __ENV.SURE || "30m";
const ANALIZ_ARALIK = Number(__ENV.ANALIZ_ARALIK_SN || 300); // bir kullanıcının iki analizi arası (sn)
const ANALIZ_BEKLEME = Number(__ENV.ANALIZ_BEKLEME_SN || 600);

const analizSuresi = new Trend("analiz_suresi", true);
const analizHatasi = new Counter("analiz_hatasi");
// 503 + Retry-After: bekleyen CV sınırı (analysis_queue_limit = 8) doldu. Hata değil, tasarlanmış geri basınç;
// kapasiteyi gösterir (gerçek modelle analiz 1–2 dk, eşzamanlılık 1).
const kuyrukDolu = new Counter("analiz_kuyruk_dolu");

export const options = {
  setupTimeout: "5m",
  scenarios: {
    gezinme: { executor: "constant-vus", vus: VUS, duration: SURE, exec: "gezinme" },
    analiz: { executor: "constant-vus", vus: VUS, duration: SURE, exec: "analiz", startTime: "10s" },
  },
  thresholds: {
    "http_req_duration{tip:api}": ["p(95)<300"],
    "http_req_failed{tip:api}": ["rate<0.01"],
    "http_req_failed{tip:analiz}": ["rate<0.01"],
    analiz_hatasi: ["count<1"],
  },
  summaryTrendStats: ["avg", "med", "p(90)", "p(95)", "p(99)", "max"],
};

const JSON_BASLIK = { "Content-Type": "application/json" };
const api = (tip, ad) => ({ tags: { tip, name: ad } });

// Sahte, anonim tek sayfalık PDF (tests/e2e/yardimci/pdf.ts ile aynı yapı; gerçek kişi bilgisi yok).
function sahteCvPdf() {
  const metin = [
    "Ornek Aday - Backend Gelistirici",
    "Yetkinlikler: Python, SQL, Git, Docker, REST API",
    "Deneyim: 2 yil web servisleri gelistirme (sahte veri)",
  ];
  const akis = ["BT", "/F1 12 Tf", "72 760 Td", "16 TL", ...metin.map((s) => `(${s}) Tj T*`), "ET"].join("\n");
  const nesneler = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>",
    `<< /Length ${akis.length} >>\nstream\n${akis}\nendstream`,
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
  ];
  let pdf = "%PDF-1.4\n";
  const konumlar = [];
  nesneler.forEach((govde, i) => {
    konumlar.push(pdf.length);
    pdf += `${i + 1} 0 obj\n${govde}\nendobj\n`;
  });
  const xref = pdf.length;
  pdf += `xref\n0 ${nesneler.length + 1}\n0000000000 65535 f \n`;
  pdf += konumlar.map((k) => `${String(k).padStart(10, "0")} 00000 n \n`).join("");
  pdf += `trailer\n<< /Size ${nesneler.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
  return pdf; // sadece ASCII: uzunluk = bayt sayısı
}
const PDF = sahteCvPdf();

// Her sanal kullanıcı için bir hesap; aynı hesabı iki senaryo paylaşır (gerçek kullanıcı gibi).
export function setup() {
  const calisma = Date.now().toString(36);
  const kullanicilar = [];
  for (let i = 0; i < VUS; i++) {
    const email = `yuk-${calisma}-${i}@example.com`;
    const sifre = `yuk-testi-${calisma}-sifre`;
    const res = http.post(
      `${BASE}/auth/register`,
      JSON.stringify({
        email,
        password: sifre,
        consents: ["kvkk_aydinlatma", "acik_riza", "kullanim_kosullari"].map((t) => ({
          consent_type: t,
          version: "2026-12",
        })),
      }),
      { headers: JSON_BASLIK, ...api("kurulum", "register") },
    );
    if (res.status !== 201) throw new Error(`kayıt başarısız (${res.status}): istek sınırı kapalı mı? ${res.body}`);
    kullanicilar.push({ email, sifre });
  }
  const roller = http.get(`${BASE}/roles`, api("kurulum", "roles")).json();
  if (!Array.isArray(roller) || roller.length === 0) throw new Error("pozisyon yok: seed-taxonomy çalıştı mı?");
  return { kullanicilar, roller: roller.map((r) => ({ id: r.id, slug: r.slug })) };
}

// Sanal kullanıcı başına oturum; access token 15 dk, 10 dakikada bir yeniden giriş yapılır.
const oturum = {};
function yetki(data) {
  const vu = exec.vu.idInTest;
  const simdi = Date.now();
  const o = oturum[vu];
  if (o && simdi - o.zaman < 10 * 60 * 1000) return o.baslik;
  const k = data.kullanicilar[(vu - 1) % data.kullanicilar.length];
  const res = http.post(`${BASE}/auth/login`, JSON.stringify({ email: k.email, password: k.sifre }), {
    headers: JSON_BASLIK,
    ...api("api", "login"),
  });
  check(res, { "giriş 200": (r) => r.status === 200 });
  const baslik = { Authorization: `Bearer ${res.json("access_token")}` };
  oturum[vu] = { zaman: simdi, baslik };
  return baslik;
}

const sec = (dizi) => dizi[Math.floor(Math.random() * dizi.length)];

export function gezinme(data) {
  const headers = yetki(data);
  const rol = sec(data.roller);
  http.get(`${BASE}/roles`, api("api", "roles"));
  const ist = http.get(`${BASE}/roles/${rol.slug}/skills`, api("api", "roles/{slug}/skills"));
  check(ist, { "pozisyon yetkinlikleri 200": (r) => r.status === 200 });
  // Kullanıcı sonuç ekranında bir yetkinliğin kaynaklarını açar. (`GET /skills?q=` arama ucu henüz yok.)
  const yetkinlikler = ist.status === 200 ? ist.json("skills") || [] : [];
  if (yetkinlikler.length > 0) {
    const kaynak = http.get(
      `${BASE}/skills/${sec(yetkinlikler).slug}/resources`,
      api("api", "skills/{slug}/resources"),
    );
    check(kaynak, { "kaynaklar 200": (r) => r.status === 200 });
  }
  http.get(`${BASE}/users/me`, { headers, ...api("api", "users/me") });
  http.get(`${BASE}/analyses`, { headers, ...api("api", "analyses (liste)") });
  sleep(1 + Math.random() * 2);
}

export function analiz(data) {
  // Kullanıcılar aynı anda yüklemesin: ilk analiz rastgele bir anda, sonra ANALIZ_ARALIK'ta bir.
  if (exec.scenario.iterationInInstance === 0) sleep(Math.random() * ANALIZ_ARALIK);
  const headers = yetki(data);
  const baslangic = Date.now();
  const res = http.post(
    `${BASE}/analyses`,
    { file: http.file(PDF, "cv.pdf", "application/pdf"), target_role_id: String(sec(data.roller).id) },
    { headers, ...api("analiz", "analyses (yükle)"), responseCallback: http.expectedStatuses(202, 503) },
  );
  if (res.status === 503) {
    kuyrukDolu.add(1);
    sleep(Number(res.headers["Retry-After"] || 30));
    return;
  }
  if (!check(res, { "analiz 202": (r) => r.status === 202 })) {
    analizHatasi.add(1, { kod: String(res.status) });
    console.warn(`analiz yüklenemedi: ${res.status} ${String(res.body).slice(0, 200)}`);
    sleep(ANALIZ_ARALIK);
    return;
  }
  const id = res.json("analysis_id");
  let durum = "queued";
  while (Date.now() - baslangic < ANALIZ_BEKLEME * 1000) {
    sleep(3);
    const r = http.get(`${BASE}/analyses/${id}`, { headers, ...api("analiz", "analyses/{id}") });
    durum = r.status === 200 ? r.json("status") : durum;
    if (durum === "done" || durum === "failed") break;
  }
  if (durum === "done") analizSuresi.add(Date.now() - baslangic);
  else analizHatasi.add(1);
  sleep(Math.max(0, ANALIZ_ARALIK - (Date.now() - baslangic) / 1000));
}

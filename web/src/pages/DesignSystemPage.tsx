import { useState } from "react";

import { Alert, Button, Card, Checkbox, Chip, DemandBars, ProgressBar, ScoreGauge, Spinner, TextField } from "../ui";

// Örnek veri contracts/examples/analysis_result.example.json ile aynı biçimde (uydurma).
const MISSING = [
  { label: "Docker", ratio: 0.75 },
  { label: "PostgreSQL", ratio: 0.62 },
  { label: "Kubernetes", ratio: 0.41 },
];
const PRESENT = [
  { skill: "Python", level: "ileri" },
  { skill: "SQL", level: "başlangıç" },
  { skill: "Git", level: "orta" },
];
const SWATCHES = ["bg", "surface", "surface-muted", "border-strong", "text", "text-muted", "accent", "danger", "success", "warning"];

/** Tasarım sistemi vitrini (T-022): bileşenlerin tüm durumları tek sayfada. Tema seçici üst menüde. */
export function DesignSystemPage() {
  const [email, setEmail] = useState("");
  const emailError = email && !email.includes("@") ? "Geçerli bir e-posta adresi girin." : undefined;

  return (
    <div className="stack">
      <div>
        <h1>Tasarım sistemi</h1>
        <p className="muted">
          Renkler ve ölçüler <code>src/ui/tokens.css</code> içinde; kontrast <code>npm run check:contrast</code> ile kontrol
          edilir. Üst menüden temayı değiştirip iki temayı da görebilirsiniz.
        </p>
      </div>

      <Card title="Renkler">
        <ul className="chip-list">
          {SWATCHES.map((name) => (
            <li key={name} className="row" style={{ gap: "var(--space-2)" }}>
              <span
                aria-hidden="true"
                style={{
                  width: "1.5rem",
                  height: "1.5rem",
                  borderRadius: "var(--radius-sm)",
                  border: "1px solid var(--border)",
                  background: `var(--${name})`,
                }}
              />
              <code>--{name}</code>
            </li>
          ))}
        </ul>
      </Card>

      <Card title="Tipografi">
        <p className="demo-heading" style={{ fontSize: "var(--text-2xl)" }}>Başlık 1 · 32px</p>
        <p className="demo-heading" style={{ fontSize: "var(--text-xl)" }}>Başlık 2 · 24px</p>
        <p className="demo-heading" style={{ fontSize: "var(--text-lg)" }}>Başlık 3 · 18px</p>
        <p>Gövde metni 16px, satır yüksekliği 1.5. Türkçe karakterler: çğıöşü ÇĞİÖŞÜ.</p>
        <p className="muted">İkincil metin, açıklamalar ve ipuçları için.</p>
      </Card>

      <Card title="Düğmeler">
        <div className="row">
          <Button>Analizi başlat</Button>
          <Button variant="secondary">Vazgeç</Button>
          <Button variant="danger">Hesabı sil</Button>
          <Button loading>Yükleniyor</Button>
          <Button disabled>Pasif</Button>
        </div>
      </Card>

      <Card title="Form">
        <form onSubmit={(e) => e.preventDefault()} noValidate style={{ maxWidth: "26rem" }}>
          <TextField
            label="E-posta"
            type="email"
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            error={emailError}
          />
          <TextField label="Şifre" type="password" autoComplete="new-password" hint="En az 8 karakter." />
          <Checkbox label="KVKK aydınlatma metnini okudum." required />
          <Button type="submit" block>
            Kayıt ol
          </Button>
        </form>
      </Card>

      <Card title="Uyarılar">
        <Alert tone="info">CV dosyan saklanmaz; analizden sonra sadece çıkan yetkinlikler hesabında kalır.</Alert>
        <Alert tone="success">Analiz tamamlandı.</Alert>
        <Alert tone="warning" title="Az ilan verisi">
          Bu pozisyon için sadece 41 güncel ilan var; oranlar daha az güvenilir.
        </Alert>
        <Alert tone="error">Sadece PDF dosyası yükleyebilirsin.</Alert>
      </Card>

      <Card title="Sonuç bileşenleri">
        <div className="row" style={{ gap: "var(--space-6)", alignItems: "flex-start" }}>
          <ScoreGauge score={62.5} />
          <div className="stack" style={{ flex: 1, minWidth: "16rem" }}>
            <div>
              <h3>Sahip olduğun yetkinlikler</h3>
              <ul className="chip-list">
                {PRESENT.map((p) => (
                  <li key={p.skill}>
                    <Chip meta={p.level}>{p.skill}</Chip>
                  </li>
                ))}
              </ul>
            </div>
            <div>
              <h3>Eksik yetkinlikler (ilanlardaki talep)</h3>
              <DemandBars items={MISSING} caption="Eksik yetkinliklerin Backend Developer ilanlarındaki talep oranı" />
            </div>
          </div>
        </div>
      </Card>

      <Card title="Bekleme durumu">
        <div className="row">
          <Spinner />
          <span>CV'n analiz ediliyor…</span>
        </div>
        <div style={{ marginTop: "var(--space-4)" }}>
          <ProgressBar value={0.48} label="Analiz ilerlemesi" />
        </div>
      </Card>
    </div>
  );
}

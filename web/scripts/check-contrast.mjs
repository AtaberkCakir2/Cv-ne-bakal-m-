// src/ui/tokens.css içindeki renk çiftlerinin WCAG AA kontrastını iki temada kontrol eder (npm run check:contrast).
// Ayrıca koyu temanın iki kopyasının (sistem tercihi ve data-theme) aynı olduğunu doğrular.
import { readFileSync } from "node:fs";

const css = readFileSync(new URL("../src/ui/tokens.css", import.meta.url), "utf8");

function block(selector) {
  const start = css.indexOf(selector);
  if (start < 0) throw new Error(`${selector} bulunamadı`);
  const open = css.indexOf("{", start);
  const close = css.indexOf("}", open);
  // Tüm değişkenler ham değerleriyle alınır; renk biçimi aşağıda kontrol edilir (#fff, rgb() sessizce atlanmasın).
  return Object.fromEntries([...css.slice(open, close).matchAll(/--([\w-]+):\s*([^;]+);/g)].map((m) => [m[1], m[2].trim()]));
}

const light = block(":root {");
const darkMedia = block(':root:not([data-theme="light"])');
const darkManual = block(':root[data-theme="dark"]');
const dark = { ...light, ...darkManual };
const HEX6 = /^#[0-9a-f]{6}$/i;

function luminance(hex) {
  const [r, g, b] = [1, 3, 5].map((i) => {
    const c = parseInt(hex.slice(i, i + 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

function ratio(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// [ön plan, arka plan, en az oran]. 4.5: normal metin; 3: kenarlık, odak halkası ve grafik (WCAG 1.4.11).
const PAIRS = [
  ...["bg", "surface", "surface-muted", "info-surface"].flatMap((bg) => [
    ["text", bg, 4.5],
    ["text-muted", bg, 4.5],
  ]),
  ["accent", "surface", 4.5],
  ["accent", "bg", 4.5],
  ["accent", "surface-muted", 4.5],
  ["accent", "info-surface", 4.5],
  ["danger", "bg", 4.5],
  ["border-strong", "bg", 3],
  ["text-on-accent", "accent", 4.5],
  ["text-on-accent", "accent-hover", 4.5],
  ["surface", "danger", 4.5],
  ["danger", "surface", 4.5],
  ["danger", "danger-surface", 4.5],
  ["success", "success-surface", 4.5],
  ["warning", "warning-surface", 4.5],
  ["text", "danger-surface", 4.5],
  ["text", "success-surface", 4.5],
  ["text", "warning-surface", 4.5],
  ["border-strong", "surface", 3],
  ["border-strong", "surface-muted", 3],
  ["focus", "surface", 3],
  ["focus", "bg", 3],
  ["chart-fill", "chart-track", 3],
  ["chart-fill", "surface", 3],
];

let failed = 0;
const colorVars = new Set(PAIRS.flatMap(([fg, bg]) => [fg, bg]));
for (const [name, theme] of [["açık", light], ["koyu (data-theme)", darkManual], ["koyu (sistem)", darkMedia]]) {
  for (const v of colorVars) {
    if (!HEX6.test(theme[v] ?? "")) {
      failed++;
      console.error(`✗ ${name}: --${v} eksik veya 6 haneli hex değil (${theme[v] ?? "yok"}); betik ölçemez`);
    }
  }
}
if (failed) process.exit(1);

for (const [name, theme] of [["açık", light], ["koyu", dark]]) {
  for (const [fg, bg, min] of PAIRS) {
    const r = ratio(theme[fg], theme[bg]);
    if (r < min) {
      failed++;
      console.error(`✗ ${name}: --${fg} / --${bg} = ${r.toFixed(2)} (en az ${min})`);
    }
  }
}

for (const key of new Set([...Object.keys(darkMedia), ...Object.keys(darkManual)])) {
  if (darkMedia[key] !== darkManual[key]) {
    failed++;
    console.error(`✗ koyu temanın iki kopyası farklı: --${key} (${darkMedia[key]} / ${darkManual[key]})`);
  }
}

if (failed) process.exit(1);
console.log(`✓ ${PAIRS.length * 2} renk çifti AA kontrastını geçiyor; koyu tema kopyaları aynı.`);

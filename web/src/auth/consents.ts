import type { components } from "../api/schema";

export type ConsentType = components["schemas"]["ConsentType"];

/**
 * Onaylanan metnin sürümü; backend onayla birlikte saklar (consents.version). docs/yasal/*.md başındaki sürüm
 * satırıyla aynı olmalı (docs/yasal/README.md "Sürümleme"). Metin değişince burası da değişir.
 */
export const CONSENT_VERSION = "2026-12-taslak";

/** Kayıt ekranındaki onay kutuları. */
export const CONSENTS: { type: ConsentType; label: string }[] = [
  { type: "kvkk_aydinlatma", label: "KVKK aydınlatma metnini okudum." },
  { type: "acik_riza", label: "CV'mdeki yetkinliklerin analiz için işlenmesine açık rıza veriyorum." },
  { type: "kullanim_kosullari", label: "Kullanım koşullarını kabul ediyorum." },
];

/** Profildeki onay listesinde metnin adı. */
export const CONSENT_NAMES: Record<ConsentType, string> = {
  kvkk_aydinlatma: "KVKK aydınlatma metni",
  acik_riza: "CV analizi için açık rıza",
  kullanim_kosullari: "Kullanım koşulları",
};

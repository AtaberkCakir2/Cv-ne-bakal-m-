import type { components } from "../api/schema";
import { LEGAL_URL } from "../config";

export type ConsentType = components["schemas"]["ConsentType"];

/**
 * Onaylanan metnin sürümü; web/src/auth/consents.ts ile aynı olmalı (backend onayla birlikte saklar). Metin değişince
 * ikisi birlikte değişir.
 */
export const CONSENT_VERSION = "2026-12-taslak";

/** Kayıt ekranındaki onay kutuları ve metnin yayınlandığı sayfa (yasal site, T-065). */
export const CONSENTS: { type: ConsentType; label: string; url: string }[] = [
  { type: "kvkk_aydinlatma", label: "KVKK aydınlatma metnini okudum.", url: `${LEGAL_URL}/aydinlatma/` },
  {
    type: "acik_riza",
    label: "CV'mdeki yetkinliklerin analiz için işlenmesine açık rıza veriyorum.",
    url: `${LEGAL_URL}/aydinlatma/`,
  },
  { type: "kullanim_kosullari", label: "Kullanım koşullarını kabul ediyorum.", url: `${LEGAL_URL}/kullanim-kosullari/` },
];

// İstemci tarafı form kuralları; backend'deki şemalarla aynı (backend/app/schemas/auth.py). Son söz backend'in.

export const PASSWORD_MIN = 8;
export const PASSWORD_MAX = 128;

// Kaba kontrol: yazım hatalarını yakalar. Asıl doğrulama backend'de (email-validator) ve doğrulama e-postasıyla.
const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type Errors<K extends string> = Partial<Record<K, string>>;

export function emailError(value: string): string | undefined {
  if (!value.trim()) return "E-posta adresini girin.";
  if (!EMAIL.test(value.trim())) return "Geçerli bir e-posta adresi girin (ör. ad@ornek.com).";
}

export function passwordError(value: string): string | undefined {
  if (!value) return "Şifreni girin.";
  if (value.length < PASSWORD_MIN) return `Şifre en az ${PASSWORD_MIN} karakter olmalı.`;
  if (value.length > PASSWORD_MAX) return `Şifre en fazla ${PASSWORD_MAX} karakter olabilir.`;
}

export function confirmError(password: string, confirm: string): string | undefined {
  if (!confirm) return "Şifreni tekrar gir.";
  if (password !== confirm) return "Şifreler aynı değil.";
}

/** Gönderimde ilk hatalı alana odaklanır; hata mesajı alanla birlikte okunur. */
export function focusFirstError(form: HTMLFormElement): void {
  form.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus();
}

export function hasErrors(errors: Record<string, string | undefined>): boolean {
  return Object.values(errors).some(Boolean);
}

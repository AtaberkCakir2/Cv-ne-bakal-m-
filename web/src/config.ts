// Ortam değişkenleri Vite üzerinden gelir (web/.env.local, commit'lenmez; bkz. web/README.md). Boş değer de varsayılana düşer.
// "localhost" değil 127.0.0.1: Windows'ta localhost önce IPv6'ya gider (backend/README.md).
export const API_URL: string = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// 127.0.0.1: backend CORS ayarı ve Windows IPv6 sorunu (backend/README.md).
export default defineConfig({
  plugins: [react()],
  server: { host: "127.0.0.1", port: 5173, strictPort: true },
});

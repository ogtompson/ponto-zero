import path from "node:path";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { defineConfig } from "vite";

// Em desenvolvimento (npm run dev) as chamadas /api vão para a API local.
// No Docker quem faz esse encaminhamento é o Nginx (ver nginx.conf).
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: { alias: { "@": path.resolve(__dirname, "src") } },
  server: {
    port: 5173,
    proxy: { "/api": process.env.API_URL ?? "http://localhost:8000" },
  },
  build: { chunkSizeWarningLimit: 900 },
});

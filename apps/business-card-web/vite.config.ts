import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Served behind nginx at /cards/ in Docker; the API lives on the same origin at /api.
export default defineConfig({
  base: process.env.VITE_BASE ?? "/cards/",
  plugins: [react(), tailwindcss()],
  server: {
    port: 5174,
    proxy: { "/api": { target: process.env.API_PROXY ?? "http://localhost:8000", changeOrigin: false } },
  },
  preview: { port: 5174 },
  build: { sourcemap: false, target: "es2022" },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    css: false,
  },
});

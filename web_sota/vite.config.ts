import react from "@vitejs/plugin-react";
import path from "path";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    allowedHosts: ["goliath"],
    port: 10728,
    strictPort: true,
    host: "127.0.0.1",
    proxy: {
      "/api": "http://127.0.0.1:10729",
      "/docs": { target: "http://127.0.0.1:10729", changeOrigin: true },
      "/openapi.json": { target: "http://127.0.0.1:10729", changeOrigin: true },
      "/redoc": { target: "http://127.0.0.1:10729", changeOrigin: true },
    },
  },
});

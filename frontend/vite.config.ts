import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const proxyTarget = process.env.VITE_PROXY_TARGET || "http://127.0.0.1:8000";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  base: "/app/",
  server: {
    proxy: {
      "/agent": {
        target: proxyTarget,
        changeOrigin: true,
      },
    },
  },
});

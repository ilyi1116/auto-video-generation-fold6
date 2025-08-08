import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [sveltekit()],
  test: {
    include: ["src/**/*.{test,spec}.{js,ts}"],
    environment: "jsdom",
    coverage: {
      reporter: ["text", "json", "html"],
    },
  },
  server: {
    port: 5173,
    strictPort: false,
    host: "127.0.0.1", // 強制使用 IPv4
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000", // 使用 IPv4 地址
        changeOrigin: true,
        secure: false,
        configure: (proxy, options) => {
          proxy.on("error", (err, req, res) => {
            console.log("proxy error", err);
          });
          proxy.on("proxyReq", (proxyReq, req, res) => {
            console.log("Sending Request to the Target:", req.method, req.url);
          });
          proxy.on("proxyRes", (proxyRes, req, res) => {
            console.log("Received Response from the Target:", proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
  build: {
    target: "es2022",
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["svelte", "@sveltejs/kit"],
          ui: ["lucide-svelte"],
          utils: ["axios", "zod"],
        },
      },
    },
  },
});

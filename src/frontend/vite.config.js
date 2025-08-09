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
        target: "http://127.0.0.1:8001", // Mock API Gateway 運行在端口 8001
        changeOrigin: true,
        secure: false,
        ws: true,
        rewrite: (path) => path,
        configure: (proxy, options) => {
          proxy.on("error", (err, req, res) => {
            console.log("proxy error", err);
          });
          proxy.on("proxyReq", (proxyReq, req, res) => {
            console.log("Sending Request to the Target:", req.method, req.url);
            // 添加 CORS 頭部
            proxyReq.setHeader('Access-Control-Allow-Origin', '*');
          });
          proxy.on("proxyRes", (proxyRes, req, res) => {
            console.log("Received Response from the Target:", proxyRes.statusCode, req.url);
            // 確保 CORS 頭部
            proxyRes.headers['Access-Control-Allow-Origin'] = '*';
            proxyRes.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS';
            proxyRes.headers['Access-Control-Allow-Headers'] = '*';
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

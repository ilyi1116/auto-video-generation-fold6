
import root from '../root.svelte';
import { set_building, set_prerendering } from '__sveltekit/environment';
import { set_assets } from '__sveltekit/paths';
import { set_manifest, set_read_implementation } from '__sveltekit/server';
import { set_private_env, set_public_env, set_safe_public_env } from '../../../node_modules/.pnpm/@sveltejs+kit@2.27.3_@sveltejs+vite-plugin-svelte@3.1.2_svelte@4.2.20_vite@5.4.19__svelte@4.2.20_vite@5.4.19/node_modules/@sveltejs/kit/src/runtime/shared-server.js';

export const options = {
	app_template_contains_nonce: false,
	csp: {"mode":"hash","directives":{"child-src":["none"],"default-src":["self"],"connect-src":["self"],"font-src":["self","data:"],"img-src":["self","data:","https:"],"media-src":["self"],"object-src":["none"],"script-src":["self"],"style-src":["self","unsafe-inline"],"base-uri":["self"],"form-action":["self"],"frame-ancestors":["none"],"upgrade-insecure-requests":false,"block-all-mixed-content":false},"reportOnly":{"upgrade-insecure-requests":false,"block-all-mixed-content":false}},
	csrf_check_origin: true,
	embedded: false,
	env_public_prefix: 'PUBLIC_',
	env_private_prefix: '',
	hash_routing: false,
	hooks: null, // added lazily, via `get_hooks`
	preload_strategy: "modulepreload",
	root,
	service_worker: false,
	templates: {
		app: ({ head, body, assets, nonce, env }) => "<!doctype html>\n<html lang=\"zh-TW\" class=\"%sveltekit.theme%\">\n  <head>\n    <meta charset=\"utf-8\" />\n    <link rel=\"icon\" href=\"" + assets + "/favicon.png\" />\n\n    <!-- 核心 Meta 標籤 -->\n    <meta\n      name=\"viewport\"\n      content=\"width=device-width, initial-scale=1, viewport-fit=cover\"\n    />\n    <meta\n      name=\"description\"\n      content=\"AI 驅動的自動影片生成平台，支援多平台發布和智能內容創作\"\n    />\n    <meta\n      name=\"keywords\"\n      content=\"AI影片生成,語音合成,自動剪輯,社群媒體,內容創作\"\n    />\n    <meta name=\"author\" content=\"Auto Video Team\" />\n\n    <!-- PWA Meta 標籤 -->\n    <meta name=\"theme-color\" content=\"#0ea5e9\" />\n    <meta name=\"application-name\" content=\"Auto Video\" />\n    <meta name=\"apple-mobile-web-app-capable\" content=\"yes\" />\n    <meta name=\"apple-mobile-web-app-status-bar-style\" content=\"default\" />\n    <meta name=\"apple-mobile-web-app-title\" content=\"Auto Video\" />\n    <meta name=\"mobile-web-app-capable\" content=\"yes\" />\n    <meta name=\"msapplication-TileColor\" content=\"#0ea5e9\" />\n    <meta name=\"msapplication-tap-highlight\" content=\"no\" />\n\n    <!-- PWA Manifest -->\n    <link rel=\"manifest\" href=\"" + assets + "/manifest.json\" />\n\n    <!-- 預載入關鍵字體 -->\n    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />\n    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin />\n    <link\n      rel=\"preload\"\n      href=\"https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap\"\n      as=\"style\"\n      onload=\"this.onload=null;this.rel='stylesheet'\"\n    />\n\n    <!-- SEO Meta 標籤 -->\n    <meta property=\"og:type\" content=\"website\" />\n    <meta property=\"og:title\" content=\"Auto Video - AI 影片生成平台\" />\n    <meta\n      property=\"og:description\"\n      content=\"AI 驅動的自動影片生成平台，支援多平台發布和智能內容創作\"\n    />\n    <meta property=\"og:image\" content=\"" + assets + "/og-image.png\" />\n    <meta property=\"og:url\" content=\"https://app.autovideo.com\" />\n    <meta property=\"og:site_name\" content=\"Auto Video\" />\n\n    <meta name=\"twitter:card\" content=\"summary_large_image\" />\n    <meta name=\"twitter:title\" content=\"Auto Video - AI 影片生成平台\" />\n    <meta\n      name=\"twitter:description\"\n      content=\"AI 驅動的自動影片生成平台，支援多平台發布和智能內容創作\"\n    />\n    <meta name=\"twitter:image\" content=\"" + assets + "/og-image.png\" />\n\n    <!-- 安全性標頭 -->\n    <meta http-equiv=\"X-Content-Type-Options\" content=\"nosniff\" />\n    <meta http-equiv=\"X-Frame-Options\" content=\"DENY\" />\n    <meta http-equiv=\"X-XSS-Protection\" content=\"1; mode=block\" />\n    <meta\n      http-equiv=\"Referrer-Policy\"\n      content=\"strict-origin-when-cross-origin\"\n    />\n\n    " + head + "\n  </head>\n  <body data-sveltekit-preload-data=\"hover\" class=\"antialiased\">\n    <!-- 主要應用程式內容 -->\n    <div id=\"svelte\" style=\"display: contents\">" + body + "</div>\n\n    <!-- Service Worker 註冊 -->\n    <script>\n      // PWA 支援檢測和 Service Worker 註冊\n      if (\"serviceWorker\" in navigator) {\n        window.addEventListener(\"load\", () => {\n          navigator.serviceWorker\n            .register(\"/service-worker.js\")\n            .then((registration) => {\n              console.log(\"SW registered: \", registration);\n            })\n            .catch((registrationError) => {\n              console.log(\"SW registration failed: \", registrationError);\n            });\n        });\n      }\n\n      // 檢測網路狀態\n      function updateNetworkStatus() {\n        const isOnline = navigator.onLine;\n        document.body.classList.toggle(\"offline\", !isOnline);\n      }\n\n      window.addEventListener(\"online\", updateNetworkStatus);\n      window.addEventListener(\"offline\", updateNetworkStatus);\n      updateNetworkStatus();\n    </script>\n  </body>\n</html>\n",
		error: ({ status, message }) => "<!doctype html>\n<html lang=\"en\">\n\t<head>\n\t\t<meta charset=\"utf-8\" />\n\t\t<title>" + message + "</title>\n\n\t\t<style>\n\t\t\tbody {\n\t\t\t\t--bg: white;\n\t\t\t\t--fg: #222;\n\t\t\t\t--divider: #ccc;\n\t\t\t\tbackground: var(--bg);\n\t\t\t\tcolor: var(--fg);\n\t\t\t\tfont-family:\n\t\t\t\t\tsystem-ui,\n\t\t\t\t\t-apple-system,\n\t\t\t\t\tBlinkMacSystemFont,\n\t\t\t\t\t'Segoe UI',\n\t\t\t\t\tRoboto,\n\t\t\t\t\tOxygen,\n\t\t\t\t\tUbuntu,\n\t\t\t\t\tCantarell,\n\t\t\t\t\t'Open Sans',\n\t\t\t\t\t'Helvetica Neue',\n\t\t\t\t\tsans-serif;\n\t\t\t\tdisplay: flex;\n\t\t\t\talign-items: center;\n\t\t\t\tjustify-content: center;\n\t\t\t\theight: 100vh;\n\t\t\t\tmargin: 0;\n\t\t\t}\n\n\t\t\t.error {\n\t\t\t\tdisplay: flex;\n\t\t\t\talign-items: center;\n\t\t\t\tmax-width: 32rem;\n\t\t\t\tmargin: 0 1rem;\n\t\t\t}\n\n\t\t\t.status {\n\t\t\t\tfont-weight: 200;\n\t\t\t\tfont-size: 3rem;\n\t\t\t\tline-height: 1;\n\t\t\t\tposition: relative;\n\t\t\t\ttop: -0.05rem;\n\t\t\t}\n\n\t\t\t.message {\n\t\t\t\tborder-left: 1px solid var(--divider);\n\t\t\t\tpadding: 0 0 0 1rem;\n\t\t\t\tmargin: 0 0 0 1rem;\n\t\t\t\tmin-height: 2.5rem;\n\t\t\t\tdisplay: flex;\n\t\t\t\talign-items: center;\n\t\t\t}\n\n\t\t\t.message h1 {\n\t\t\t\tfont-weight: 400;\n\t\t\t\tfont-size: 1em;\n\t\t\t\tmargin: 0;\n\t\t\t}\n\n\t\t\t@media (prefers-color-scheme: dark) {\n\t\t\t\tbody {\n\t\t\t\t\t--bg: #222;\n\t\t\t\t\t--fg: #ddd;\n\t\t\t\t\t--divider: #666;\n\t\t\t\t}\n\t\t\t}\n\t\t</style>\n\t</head>\n\t<body>\n\t\t<div class=\"error\">\n\t\t\t<span class=\"status\">" + status + "</span>\n\t\t\t<div class=\"message\">\n\t\t\t\t<h1>" + message + "</h1>\n\t\t\t</div>\n\t\t</div>\n\t</body>\n</html>\n"
	},
	version_hash: "9ddok9"
};

export async function get_hooks() {
	let handle;
	let handleFetch;
	let handleError;
	let handleValidationError;
	let init;
	

	let reroute;
	let transport;
	

	return {
		handle,
		handleFetch,
		handleError,
		handleValidationError,
		init,
		reroute,
		transport
	};
}

export { set_assets, set_building, set_manifest, set_prerendering, set_private_env, set_public_env, set_read_implementation, set_safe_public_env };

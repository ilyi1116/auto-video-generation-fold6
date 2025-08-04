import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vitest/config';

export default defineConfig({
	plugins: [sveltekit()],
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}'],
		environment: 'jsdom',
		coverage: {
			reporter: ['text', 'json', 'html']
		}
	},
	server: {
		port: 5173,
		strictPort: false,
		host: true,
		proxy: {
			'/api': {
				target: 'http://localhost:8000',
				changeOrigin: true,
				secure: false
			}
		}
	},
	build: {
		target: 'es2022',
		rollupOptions: {
			output: {
				manualChunks: {
					vendor: ['svelte', '@sveltejs/kit'],
					ui: ['lucide-svelte'],
					utils: ['axios', 'zod']
				}
			}
		}
	}
});
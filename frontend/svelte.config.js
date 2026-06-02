/**
 * Lý do chọn giải pháp:
 * - Theo kỷ luật V60.0: Mọi logic phải đặt ở Backend, UI phải là Zero-Hydration hoặc CSR.
 * - Chuyển sang sử dụng adapter-static thay vì adapter-auto/adapter-node:
 *   Tránh chạy tiến trình Node.js (tốn RAM), giao trọn gói static folder cho Caddy.
 * - Cấu hình fallback "index.html" phục vụ app dưới dạng SPA.
 * - Bật precompress tối ưu Network-I/O từ xa.
 */
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		inlineStyleThreshold: 1048576,
		adapter: adapter({
			pages: 'dist',
			assets: 'dist',
			fallback: 'index.html',
			precompress: true,
			strict: true
		})
	}
};

export default config;

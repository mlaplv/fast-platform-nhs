/**
 * SvelteKit SSR Configuration (adapter-node)
 * - Node.js SSR server cho storefront (SEO/LCP tối ưu)
 * - Admin zone vẫn chạy SPA mode (ssr=false trong admin layout)
 * - precompress bật sẵn gzip/brotli cho static assets
 */
import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	preprocess: vitePreprocess(),
	kit: {
		inlineStyleThreshold: 1048576,
		adapter: adapter({
			out: 'build',
			precompress: true
		})
	}
};

export default config;

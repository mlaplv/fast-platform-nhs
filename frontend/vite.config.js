import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [tailwindcss(), sveltekit()],
	server: {
		allowedHosts: true
	},
	optimizeDeps: {
		include: ['lucide-svelte', 'idb-keyval', 'clsx', 'tailwind-merge']
	}
});

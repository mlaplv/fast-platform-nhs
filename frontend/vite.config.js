import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import { ViteMinifyPlugin } from 'vite-plugin-minify';

export default defineConfig(({ command, mode }) => {
	const isWatch = command === 'serve' || mode === 'development';

	return {
		envDir: '../',
		plugins: [
			tailwindcss(),
			sveltekit(),
			/* Elite V2.2: HTML Minifier — production only, script-safe */
			...(!isWatch ? [ViteMinifyPlugin({
				minifyJS: false,
				minifyCSS: true,
				removeComments: true,
				collapseBooleanAttributes: true,
				removeRedundantAttributes: true,
				removeScriptTypeAttributes: true,
				removeStyleLinkTypeAttributes: true,
				useShortDoctype: true,
			})] : []),
		],
		server: {
			allowedHosts: true,
			watch: {
				usePolling: false,
				ignored: ['**/node_modules/**', '**/.svelte-kit/**', '**/.git/**']
			}
		},
		optimizeDeps: {
			include: ['idb-keyval', 'clsx', 'tailwind-merge'],
			exclude: ['@ricky0123/vad-web', '@lucide/svelte']
		},
		ssr: {
			external: ['@ricky0123/vad-web']
		},
		esbuild: {
			pure: ['console.log', 'console.debug', 'console.info']
		},
		build: {
			emptyOutDir: !isWatch,
		}
	};
});

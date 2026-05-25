import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';
import { ViteMinifyPlugin } from 'vite-plugin-minify';
import path from 'path';
import { fileURLToPath } from 'url';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Giải quyết đường dẫn vật lý thực tế cho pnpm symlink để fast-glob tìm thấy file
function getPhysicalPath(relativePath, globPattern = '') {
	const symlinkPath = path.resolve(__dirname, relativePath);
	try {
		const realDir = fs.realpathSync(symlinkPath);
		return path.join(realDir, globPattern).replace(/\\/g, '/');
	} catch (e) {
		console.warn(`[ViteConfig] Failed to resolve physical path for ${relativePath}:`, e);
		return path.join(symlinkPath, globPattern).replace(/\\/g, '/');
	}
}

const isWatch = process.argv.includes('--watch') || process.argv.includes('-w') || process.argv.includes('watch');

export default defineConfig({
	envDir: '../',
	define: {
		global: 'window',
	},
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
		viteStaticCopy({
			targets: [
				{
					src: getPhysicalPath('node_modules/@ricky0123/vad-web/dist', '*.onnx'),
					dest: 'vad'
				},
				{
					src: getPhysicalPath('node_modules/@ricky0123/vad-web/dist', 'vad.worklet.bundle.min.js'),
					dest: 'vad'
				},
				{
					src: getPhysicalPath('node_modules/onnxruntime-web/dist', '*.wasm'),
					dest: 'wasm'
				},
				{
					src: getPhysicalPath('node_modules/onnxruntime-web/dist', '*.mjs'),
					dest: 'wasm'
				}
			]
		})
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
	build: {
		emptyOutDir: !isWatch,
		commonjsOptions: {
			include: [/node_modules/],
			dynamicRequireTargets: [
				getPhysicalPath('node_modules/onnxruntime-web/dist', '*.wasm'),
				getPhysicalPath('node_modules/onnxruntime-web/dist', '*.mjs'),
				getPhysicalPath('node_modules/@ricky0123/vad-web/dist', '*.wasm')
			]
		}
	}
});

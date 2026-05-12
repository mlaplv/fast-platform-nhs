import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
	define: {
		global: 'window',
	},
	plugins: [
		tailwindcss(), 
		sveltekit(),
		viteStaticCopy({
			targets: [
				{
					src: 'node_modules/@ricky0123/vad-web/dist/*.onnx',
					dest: 'vad'
				},
				{
					src: 'node_modules/@ricky0123/vad-web/dist/vad.worklet.bundle.min.js',
					dest: 'vad'
				},
				{
					src: 'node_modules/onnxruntime-web/dist/*.wasm',
					dest: 'wasm'
				},
				{
					src: 'node_modules/onnxruntime-web/dist/*.mjs',
					dest: 'wasm'
				}
			]
		})
	],
	server: {
		allowedHosts: true
	},
	optimizeDeps: {
		include: ['idb-keyval', 'clsx', 'tailwind-merge'],
		exclude: ['@ricky0123/vad-web']
	},
	ssr: {
		external: ['@ricky0123/vad-web']
	},
	build: {
		commonjsOptions: {
			include: [/node_modules/],
			dynamicRequireTargets: [
				'node_modules/onnxruntime-web/dist/*.wasm',
				'node_modules/onnxruntime-web/dist/*.mjs',
				'node_modules/@ricky0123/vad-web/dist/*.wasm'
			]
		}
	}
});

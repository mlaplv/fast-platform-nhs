import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export default defineConfig({
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
					dest: 'vad'
				},
				{
					src: 'node_modules/onnxruntime-web/dist/*.mjs',
					dest: 'vad'
				}
			]
		})
	],
	server: {
		allowedHosts: true
	},
	optimizeDeps: {
		include: ['idb-keyval', 'clsx', 'tailwind-merge', '@ricky0123/vad-web', 'onnxruntime-web']
	}
});

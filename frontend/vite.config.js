import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';
import { viteStaticCopy } from 'vite-plugin-static-copy';
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

export default defineConfig({
	envDir: '../',
	define: {
		global: 'window',
	},
	plugins: [
		tailwindcss(), 
		sveltekit(),
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

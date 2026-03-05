import tailwindcss from "@tailwindcss/vite";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
// @ts-ignore
import fs from "node:fs";
import process from "node:process";

// ── Auto-detect package versions for dashboard display ──
function getVersion(path: string, dep: string) {
  try {
    const pkg = JSON.parse(fs.readFileSync(path, "utf-8"));
    const version = pkg.dependencies?.[dep] || pkg.devDependencies?.[dep] || "";
    return version.replace(/^[^\d]+/, ""); // remove ^ or ~
  } catch {
    return "unknown";
  }
}

function getPythonDepVersion(path: string, dep: string) {
  try {
    const content = fs.readFileSync(path, "utf-8");
    // Matches: "litestar", "litestar>=2.0", "litestar==2.0", "litestar[standard]>=2.0", "litestar~=2.0"
    const regex = new RegExp(
      `"${dep}(?:\\[.*?\\])?(?:>=|==|~=|^=|\\s*~=|\\s*>=)?([\\d\\.]*)"`,
    );
    const match = content.match(regex);
    if (match && match[1]) return match[1];
    return "latest";
  } catch {
    return "unknown";
  }
}

function getDockerfilePythonVersion(path: string) {
  try {
    const content = fs.readFileSync(path, "utf-8");
    const match = content.match(/FROM\s+python:([\d\.]*)/i);
    return match ? match[1] : "unknown";
  } catch {
    return "unknown";
  }
}

function getCaddyVersion(path: string) {
  try {
    const content = fs.readFileSync(path, "utf-8");
    const match = content.match(/image:\s+caddy:([\d\.]*)/i);
    return match ? match[1] : "2.x";
  } catch {
    return "2.x";
  }
}

const svelteVersion = getVersion("./package.json", "svelte") || "5.x";
const twVersion = getVersion("./package.json", "tailwindcss") || "4.x";
const sqlalchemyVersion = getPythonDepVersion(
  "../../apps/api-gateway/pyproject.toml",
  "sqlalchemy",
);
const alembicVersion = getPythonDepVersion(
  "../../apps/api-gateway/pyproject.toml",
  "alembic",
);
const litestarVersion = getPythonDepVersion(
  "../../apps/api-gateway/pyproject.toml",
  "litestar",
);
const pydanticAiVersion = getPythonDepVersion(
  "../../apps/api-gateway/pyproject.toml",
  "pydantic-ai",
);
const litellmVersion = getPythonDepVersion(
  "../../apps/api-gateway/pyproject.toml",
  "litellm",
);
const pythonVersion = getDockerfilePythonVersion(
  "../../apps/api-gateway/Dockerfile.dev",
);
const caddyVersion = getCaddyVersion("../../docker-compose.yml");

export default defineConfig({
  define: {
    __APP_VERSIONS__: JSON.stringify({
      svelte: svelteVersion,
      tailwind: twVersion,
      sqlalchemy: sqlalchemyVersion,
      alembic: alembicVersion,
      litestar: litestarVersion,
      pydantic_ai: pydanticAiVersion,
      litellm: litellmVersion,
      python: pythonVersion,
      caddy: caddyVersion,
    }),
  },
  plugins: [tailwindcss(), sveltekit()],
  server: {
    host: true,
    port: 5173,
    allowedHosts: [
      process.env.APP_DOMAIN || "smartshop.test",
      process.env.ADMIN_DOMAIN || "admin.smartshop.test",
    ],
    proxy: {
      "/api": {
        // @ts-ignore
        target: process.env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000",
        changeOrigin: true,
      },
    },
  },
  optimizeDeps: {
    include: ["lucide-svelte"],
  },
});

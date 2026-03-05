import tailwindcss from "@tailwindcss/vite";
import { sveltekit } from "@sveltejs/kit/vite";
import { defineConfig } from "vite";
// @ts-ignore
import fs from "node:fs";
import process from "node:process";

// ── Auto-detect package versions for dashboard display ──
// ── Auto-detect package versions for dashboard display ──
const ROOT_DIR = "../../";

function getLockfileVersion(dep: string) {
  try {
    const lockPath = fs.existsSync("./pnpm-lock.yaml")
      ? "./pnpm-lock.yaml"
      : ROOT_DIR + "pnpm-lock.yaml";
    if (!fs.existsSync(lockPath)) return null;

    const content = fs.readFileSync(lockPath, "utf-8");
    // Standard pnpm-lock v6/v9 format for importers
    const regex = new RegExp(
      `apps/ui-core:[\\s\\S]*?${dep}:[\\s\\S]*?version: (\\d+\\.\\d+\\.\\d+)`,
      "i",
    );
    const match = content.match(regex);
    if (match && match[1]) return match[1];

    // Fallback for packages outside importers
    const pkgRegex = new RegExp(
      `packages:[\\s\\S]*?/${dep}@(\\d+\\.\\d+\\.\\d+)`,
      "i",
    );
    const pkgMatch = content.match(pkgRegex);
    return pkgMatch ? pkgMatch[1] : null;
  } catch {
    return null;
  }
}

function getVersion(path: string, dep: string, fallback: string) {
  try {
    const lockVersion = getLockfileVersion(dep);
    if (lockVersion) return lockVersion;

    if (fs.existsSync(path)) {
      const pkg = JSON.parse(fs.readFileSync(path, "utf-8"));
      const version =
        pkg.dependencies?.[dep] || pkg.devDependencies?.[dep] || "";
      const cleaned = version.replace(/^[^\d]+/, "");
      if (cleaned && cleaned !== "latest") return cleaned;
    }
    return fallback;
  } catch {
    return fallback;
  }
}

function getPythonDepVersion(
  path: string,
  dep: string,
  stableFallback: string,
) {
  try {
    if (fs.existsSync(path)) {
      const content = fs.readFileSync(path, "utf-8");
      const regex = new RegExp(
        `"${dep}(?:\\[.*?\\])?(?:>=|==|~=|^=|\\s*~=|\\s*>=)?([\\d\\.]*)"`,
      );
      const match = content.match(regex);
      if (match && match[1] && match[1].length > 1) return match[1];
    }
    return stableFallback;
  } catch {
    return stableFallback;
  }
}

function getDockerfilePythonVersion(path: string) {
  try {
    if (fs.existsSync(path)) {
      const content = fs.readFileSync(path, "utf-8");
      const match = content.match(/FROM\s+python:([\d\.]*)/i);
      return match ? match[1] : "3.14";
    }
    return "3.14";
  } catch {
    return "3.14";
  }
}

function getCaddyVersion(path: string) {
  try {
    if (fs.existsSync(path)) {
      const content = fs.readFileSync(path, "utf-8");
      const match = content.match(/image:\s+caddy:([\d\.]*)/i);
      return match ? match[1] : "2.x";
    }
    return "2.x";
  } catch {
    return "2.x";
  }
}

const svelteVersion = getVersion("./package.json", "svelte", "5.53.7");
const twVersion = getVersion("./package.json", "tailwindcss", "4.2.1");
const sqlalchemyVersion = getPythonDepVersion(
  "../api-gateway/pyproject.toml",
  "sqlalchemy",
  "2.0.48",
);
const alembicVersion = getPythonDepVersion(
  "../api-gateway/pyproject.toml",
  "alembic",
  "1.18.4",
);
const litestarVersion = getPythonDepVersion(
  "../api-gateway/pyproject.toml",
  "litestar",
  "2.21.0",
);
const pydanticAiVersion = getPythonDepVersion(
  "../api-gateway/pyproject.toml",
  "pydantic-ai",
  "1.66.0",
);
const litellmVersion = getPythonDepVersion(
  "../api-gateway/pyproject.toml",
  "litellm",
  "1.82.0",
);
const prismaVersion = getVersion("./package.json", "@prisma/client", "6.4.1");
const pythonVersion = getDockerfilePythonVersion(
  "../api-gateway/Dockerfile.dev",
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
      prisma: prismaVersion,
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

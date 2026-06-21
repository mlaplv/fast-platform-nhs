# ── Stage 1: Build ──────────────────────────────────────────────────────────
# Installs ALL deps (including devDeps) and compiles SvelteKit inside Docker.
# Docker layer cache means only changed source files trigger a rebuild.
FROM node:22-alpine AS builder

WORKDIR /app/frontend

RUN corepack enable

# Copy lockfiles first — maximizes cache hit when only src files change
COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
RUN pnpm install --frozen-lockfile

# Copy source and build
COPY . .
RUN pnpm run build

# ── Stage 2: Runtime ─────────────────────────────────────────────────────────
# Only prod deps + the compiled output from stage 1.
FROM node:22-alpine AS runtime

WORKDIR /app/frontend

RUN corepack enable

COPY package.json pnpm-lock.yaml pnpm-workspace.yaml .npmrc ./
RUN pnpm install --prod --frozen-lockfile

# Copy only the built output from builder stage
COPY --from=builder /app/frontend/build ./build

EXPOSE 3000
ENV PORT=3000
ENV NODE_ENV=production

CMD ["node", "build/index.js"]

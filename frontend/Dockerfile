# Production Dockerfile for SvelteKit SSR storefront (Pre-built mode)
FROM node:22-alpine

WORKDIR /app/frontend

RUN corepack enable

COPY package.json pnpm-lock.yaml ./

# Install only production dependencies
RUN pnpm install --prod --frozen-lockfile

# Copy the precompiled build folder
COPY build ./build

EXPOSE 3000
ENV PORT=3000
ENV NODE_ENV=production

# Start SvelteKit server
CMD ["node", "build/index.js"]

FROM node:24-slim

# curl is used by the Docker healthcheck in infra/docker-compose.yml — the slim image
# doesn't ship it, and without it the healthcheck command itself fails (not the app).
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY package.json ./
# --legacy-peer-deps: the Nuxt module ecosystem's peer-dep ranges lag behind actual
# releases (e.g. @tailwindcss/vite@4.3.3 vs. @nuxtjs/i18n's transitive esbuild/vite
# peers) — a real conflict npm's strict resolver won't auto-resolve, not a version
# pinned wrong. Packages are pinned exactly above, so this doesn't add version drift.
RUN npm install --legacy-peer-deps

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

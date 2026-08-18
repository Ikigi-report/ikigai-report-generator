FROM node:22-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    chromium \
    fonts-dejavu-core \
    fonts-noto-core \
    pandoc \
    python3 \
    python3-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN python3 -m pip install --break-system-packages -r report-kit/requirements.txt \
    && npm install -g corepack@latest \
    && corepack pnpm install \
    && corepack pnpm run build

ENV NODE_ENV=production
ENV BROWSER_BIN=/usr/bin/chromium

CMD ["node", "dist/index.js"]

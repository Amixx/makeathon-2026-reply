## ── Stage 1: build the frontend ──────────────────────────────────────────────
FROM node:22-slim AS frontend-build
WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ .
ENV VITE_AGENT_URL=""
RUN npm run build

## ── Stage 2: backend + serve frontend dist ──────────────────────────────────
FROM mcr.microsoft.com/playwright/python:v1.52.0-noble

WORKDIR /app/backend

RUN apt-get update && apt-get install -y --no-install-recommends nodejs npm && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN npm install -g @modelcontextprotocol/inspector
RUN playwright install chromium

COPY backend/ /app/backend
COPY --from=frontend-build /build/dist /app/frontend-dist
COPY prototype/ /app/prototype

EXPOSE 8000

CMD ["python", "launch_public.py"]

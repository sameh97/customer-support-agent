# ── Build stage ───────────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install deps first (cached layer — only re-runs if requirements.txt changes)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# ── Frontend build stage ──────────────────────────────────────────────────────
FROM node:22-slim AS frontend

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build


# ── Runtime stage ─────────────────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy source code
COPY . .

# Built React app — FastAPI serves it at /
COPY --from=frontend /frontend/dist ./frontend/dist

# data/docs and data/chroma_db are mounted as volumes at runtime
# so they persist across container restarts and rebuilds
RUN mkdir -p data/docs data/chroma_db

EXPOSE 8000

# Apply DB migrations, then start the API
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn src.api:app --host 0.0.0.0 --port 8000"]
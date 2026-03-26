FROM node:20-alpine AS frontend-build

WORKDIR /app/frontend

# Install dependencies first for better layer caching
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend ./
RUN npm run build


FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY --from=frontend-build /app/frontend/dist ./frontend/dist

# FastAPI serves the React app from `frontend/dist` (see backend/app.py).
EXPOSE 10000
CMD ["sh", "-c", "uvicorn backend.app:app --host 0.0.0.0 --port ${PORT:-10000}"]


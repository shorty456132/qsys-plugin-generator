# Stage 1: Build Vue frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* ./frontend/
RUN cd frontend && npm ci
COPY frontend/ ./frontend/
RUN cd frontend && npm run build
# Build output lands at /app/static/dist (vite outDir: ../static/dist)

# Stage 2: Python application
FROM python:3.12-slim
WORKDIR /app

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY server.py database.py compile.py ./
COPY prompts/ ./prompts/
COPY documents/ ./documents/

# Copy built frontend from stage 1
COPY --from=frontend-build /app/static/dist ./static/dist

EXPOSE 8080

# 120s timeout needed for Claude API calls with tool loops (can take 30-60s)
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080", "--workers", "2", "--threads", "4", "--timeout", "120"]

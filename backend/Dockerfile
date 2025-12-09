# Stage 1: Build Frontend
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
# Check if package-lock.json exists, if not, it will be skipped by Copy but npm install might generate it.
# Ideally we copy both if they exist.
# Assuming standard structure.
RUN npm install
COPY frontend/ ./
RUN npm run build  # Generates /dist folder (vite default)

# Stage 2: Python Runtime
FROM python:3.11-slim
WORKDIR /app
# Install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Copy Backend Code
COPY backend/ .
# Copy Built Frontend Assets from Stage 1
COPY --from=frontend-build /app/frontend/dist /app/static

# Env Vars defaults
ENV SQLITE_DB_PATH=/data/schwab.db

# Security: Run as non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Command: Run FastAPI
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

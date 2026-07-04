# =============================================================================
# Dockerfile – MaxWeather API (multi-stage)
# =============================================================================
# Stage 1 (base)  – install prod deps into a clean image
# Stage 2 (test)  – run pytest; Docker build fails if any test fails
# Stage 3 (final) – slim runtime image, non-root user
# =============================================================================

# ---- Stage 1: Base ----
FROM python:3.12-slim AS base

WORKDIR /app

# Install prod dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Stage 2: Test ----
FROM base AS test

COPY requirements-dev.txt pytest.ini ./
RUN pip install --no-cache-dir -r requirements-dev.txt

COPY app/ ./app/
COPY tests/ ./tests/

# Tests MUST pass for the build to succeed
RUN OPENWEATHER_API_KEY=test pytest tests/ -v --tb=short

# ---- Stage 3: Final runtime ----
FROM base AS final

COPY app/ ./app/

# Create non-root user
RUN adduser --disabled-password --gecos "" --uid 1001 appuser
USER appuser

EXPOSE 8000

# Uvicorn with 2 workers; adjust via K8s resource limits
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

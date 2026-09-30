# ==============================================================================
# FLOODY SHIELD — Predict • Protect • Preserve
# Multi-Source Satellite AI Early Warning Microservice (SIH PS-26192)
# ==============================================================================
FROM python:3.11-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on

WORKDIR /app

# Install system dependencies for geospatial packages (GDAL, GEOS, PROJ)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python scientific & microservice dependencies
RUN pip install --no-cache-dir \
    torch --index-url https://download.pytorch.org/whl/cpu \
    numpy \
    pandas \
    scipy \
    scikit-learn \
    lightgbm \
    xgboost \
    shapely \
    networkx \
    tifffile \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    httpx \
    folium \
    joblib

# Copy source repository
COPY . /app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]

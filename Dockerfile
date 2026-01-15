# =============================================================================
# Multi-stage Dockerfile for Dynamic Research Assistant
# =============================================================================
# Stage 1: Builder - Install dependencies
# Stage 2: Production - Minimal runtime image
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production
# -----------------------------------------------------------------------------
FROM python:3.11-slim AS production

WORKDIR /app

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    API_HOST=0.0.0.0 \
    API_PORT=8000

# Health check for the API
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 7860 8000

# Create startup script with proper health checking
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "Starting FastAPI backend..."\n\
uvicorn main:app --host 0.0.0.0 --port 8000 &\n\
API_PID=$!\n\
\n\
# Wait for API to be ready\n\
echo "Waiting for API to be ready..."\n\
for i in {1..30}; do\n\
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then\n\
        echo "API is ready!"\n\
        break\n\
    fi\n\
    echo "Waiting... ($i/30)"\n\
    sleep 1\n\
done\n\
\n\
echo "Starting Streamlit frontend..."\n\
streamlit run app.py \\\n\
    --server.port=7860 \\\n\
    --server.address=0.0.0.0 \\\n\
    --server.headless=true \\\n\
    --browser.gatherUsageStats=false\n' > /app/start.sh && chmod +x /app/start.sh

CMD ["./start.sh"]

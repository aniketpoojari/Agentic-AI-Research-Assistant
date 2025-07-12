# Multi-stage build for production
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Set environment variables BEFORE copying packages
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV PATH="/root/.local/bin:$PATH"

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create startup script with explicit PATH
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Ensure PATH includes local bin\n\
export PATH="/root/.local/bin:$PATH"\n\
\n\
# Verify commands are available\n\
which uvicorn || echo "uvicorn not found in PATH: $PATH"\n\
which streamlit || echo "streamlit not found in PATH: $PATH"\n\
\n\
cleanup() {\n\
  echo "Shutting down services..."\n\
  kill $API_PID 2>/dev/null || true\n\
  exit 0\n\
}\n\
\n\
trap cleanup SIGTERM SIGINT\n\
\n\
echo "Starting FastAPI server..."\n\
/root/.local/bin/uvicorn main:app --host 0.0.0.0 --port 8000 &\n\
API_PID=$!\n\
\n\
echo "Waiting for API to start..."\n\
for i in {1..30}; do\n\
  if curl -f http://localhost:8000/health >/dev/null 2>&1; then\n\
    echo "API is ready!"\n\
    break\n\
  fi\n\
  sleep 1\n\
done\n\
\n\
echo "Starting Streamlit app..."\n\
/root/.local/bin/streamlit run app.py \\\n\
  --server.port=7860 \\\n\
  --server.address=0.0.0.0 \\\n\
  --server.headless=true \\\n\
  --server.enableCORS=false \\\n\
  --server.enableXsrfProtection=false\n' > start.sh && chmod +x start.sh

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:7860/_stcore/health || exit 1

CMD ["./start.sh"]

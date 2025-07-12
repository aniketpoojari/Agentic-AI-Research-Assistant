# Multi-stage build for production
FROM python:3.11-slim as builder

# Set working directory
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

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONPATH=/app
ENV PATH=/root/.local/bin:$PATH

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder stage
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY . .

# Create optimized startup script with proper error handling
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Function to handle shutdown\n\
cleanup() {\n\
    echo "Shutting down services..."\n\
    kill $API_PID 2>/dev/null || true\n\
    exit 0\n\
}\n\
\n\
# Set up signal handlers\n\
trap cleanup SIGTERM SIGINT\n\
\n\
# Start FastAPI server in background\n\
echo "Starting FastAPI server..."\n\
python main.py &\n\
API_PID=$!\n\
\n\
# Wait for API to be ready\n\
echo "Waiting for API to start..."\n\
for i in {1..30}; do\n\
    if curl -f http://localhost:8000/health >/dev/null 2>&1; then\n\
        echo "API is ready!"\n\
        break\n\
    fi\n\
    sleep 1\n\
done\n\
\n\
# Start Streamlit app\n\
echo "Starting Streamlit app..."\n\
streamlit run app.py \\\n\
    --server.port=7860 \\\n\
    --server.address=0.0.0.0 \\\n\
    --server.headless=true \\\n\
    --server.enableCORS=false \\\n\
    --server.enableXsrfProtection=false\n\
' > start.sh && chmod +x start.sh

# Expose port 7860 (HuggingFace Spaces default)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:7860/_stcore/health || exit 1

# Run the startup script
CMD ["./start.sh"]

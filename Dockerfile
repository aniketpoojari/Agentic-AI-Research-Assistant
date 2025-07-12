FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create simple startup script
RUN echo '#!/bin/bash\n\
set -e\n\
uvicorn main:app --host 0.0.0.0 --port 8000 &\n\
sleep 5\n\
streamlit run app.py --server.port=7860 --server.address=0.0.0.0 --server.headless=true\n' > start.sh && chmod +x start.sh

EXPOSE 7860

CMD ["./start.sh"]

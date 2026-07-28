FROM python:3.11-slim

# System deps (for scipy/numpy native extensions)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgomp1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer-cached unless requirements change)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY . .

# HF Spaces requires port 7860
ENV HOST=0.0.0.0
ENV PORT=7860

# Download models from HF Hub at build time if HF_MODEL_REPO is set.
# If the secret is not available at build time, download_models.py
# is called again at runtime (first request to /health triggers it via lifespan).
RUN python download_models.py || echo "Model download skipped at build time — will retry at startup"

EXPOSE 7860
CMD ["python", "run.py"]

# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set HuggingFace cache directory to persist model in Docker image
ENV HF_HOME=/app/.cache/huggingface
ENV TRANSFORMERS_CACHE=/app/.cache/huggingface/transformers
ENV CLOUD_RUN_ENV=true

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
  build-essential \
  curl \
  && rm -rf /var/lib/apt/lists/*

# Copy requirements first for Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Download spaCy model
RUN python -m spacy download en_core_web_sm

# Copy application code
COPY . .

# Pre-download ONNX emotion model to avoid first-request timeout
# This will cache in /app/.cache/huggingface which is baked into the image
RUN python -c "from optimum.onnxruntime import ORTModelForSequenceClassification; from transformers import AutoTokenizer; model_id = 'SamLowe/roberta-base-go_emotions-onnx'; ORTModelForSequenceClassification.from_pretrained(model_id); AutoTokenizer.from_pretrained(model_id); print('GoEmotions ONNX model cached')"

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (Cloud Run will override with PORT env var)
EXPOSE 8080

# Run the application
# Cloud Run injects PORT env var; FastAPI must read it
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1

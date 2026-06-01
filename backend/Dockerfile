FROM python:3.11-slim

# Force root execution and prevent interactive stalls
USER root
ENV DEBIAN_FRONTEND=noninteractive

# Optimized System dependencies with retry fallbacks
RUN apt-get clean && \
    apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libmagic1 \
    tesseract-ocr \
    tesseract-ocr-eng \
    poppler-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Non-root user setup (Create dirs BEFORE dropping privileges)
RUN useradd -m -u 1000 omnisynth && \
    mkdir -p /app/logs /app/uploads /app/data/faiss_index && \
    chown -R omnisynth:omnisynth /app

USER omnisynth

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

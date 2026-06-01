FROM python:3.11-slim

USER root
ENV DEBIAN_FRONTEND=noninteractive

# ← ADD THIS BLOCK
RUN echo 'Acquire::Retries "5";' > /etc/apt/apt.conf.d/80retries && \
    echo 'Acquire::http::Timeout "120";' >> /etc/apt/apt.conf.d/80retries

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libmagic1 \
        tesseract-ocr \
        tesseract-ocr-eng \
        poppler-utils \
        libgl1 \
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

# Setup directories and permissions before dropping down to low privileges
RUN mkdir -p /app/logs /app/uploads /app/data/faiss_index && \
    useradd -m -u 1000 omnisynth && \
    chown -R omnisynth:omnisynth /app

USER omnisynth

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

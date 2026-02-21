# syntax=docker/dockerfile:1

FROM python:3.12-slim-bookworm
SHELL ["/bin/bash", "-c"]

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create working directory
RUN mkdir -p /app
WORKDIR /app

# Install system dependencies required for numpy, pandas, tables, and Django
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libhdf5-dev \
    libpq-dev \
    pkg-config \
    chromium \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p staticfiles data

# Expose port
EXPOSE 80

# Expose port and run Gunicorn with Dash app
CMD ["gunicorn", "--workers=4", "--threads=2", "--timeout=120", "-b", "0.0.0.0:80", "--no-control-socket", "app:server"]

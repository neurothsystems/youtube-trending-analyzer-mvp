# Multi-stage Dockerfile for YouTube Trending Analyzer MVP Backend
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user
RUN groupadd -r yttrends && useradd -r -g yttrends yttrends

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Set work directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for logs and data
RUN mkdir -p /app/logs /app/data && \
    chown -R yttrends:yttrends /app

# Switch to non-root user
USER yttrends

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/mvp/health/live')"

# Default command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Development stage
FROM base as development
ENV DEBUG=true
ENV ENVIRONMENT=development

# Install development dependencies
COPY requirements-dev.txt* ./
RUN pip install --no-cache-dir -r requirements-dev.txt 2>/dev/null || echo "No dev requirements"

# Enable hot reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
ENV DEBUG=false
ENV ENVIRONMENT=production

# Optimize Python
ENV PYTHONOPTIMIZE=1

# Use gunicorn for production
RUN pip install --no-cache-dir gunicorn[gthread]

CMD ["gunicorn", "app.main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "30", "--keep-alive", "2", "--max-requests", "1000", "--max-requests-jitter", "100"]
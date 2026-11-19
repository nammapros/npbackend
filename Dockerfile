FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user
RUN useradd --system --uid 10001 --create-home app

# Copy application code
COPY . .

# Set ownership
RUN chown -R app:app /app

USER app

EXPOSE 8080

# Run migrations, bootstrap admin (if configured), and start Gunicorn
CMD ["sh", "-c", "python manage.py bootstrap_admin || true; exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers ${GUNICORN_WORKERS:-2} --threads ${GUNICORN_THREADS:-4} --timeout ${GUNICORN_TIMEOUT:-60} --graceful-timeout 30 --access-logfile - --error-logfile -"]

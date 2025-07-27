# --- Build Stage ---
# Use an official Python runtime as a parent image
FROM python:3.11-slim as builder

# Set the working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file
COPY requirements.txt .

# Install dependencies using pip into a wheelhouse
RUN pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# --- Final Stage ---
# Use a slim, non-builder image for the final container
FROM python:3.11-slim as final

# Set the working directory
WORKDIR /app

# Set environment variables for production
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production
ENV PORT=8080

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy the wheels from the builder stage
COPY --from=builder /app/wheels /wheels

# Install the dependencies from the wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

# Copy the application source code
COPY . .

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Expose the port the app runs on
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/api/v1/health/live')" || exit 1

# Optimized command for Cloud Run - fewer workers for better memory usage
CMD ["gunicorn", "--workers=1", "--threads=4", "--worker-class=uvicorn.workers.UvicornWorker", "--bind=0.0.0.0:8080", "--timeout=300", "--keep-alive=2", "--max-requests=1000", "--max-requests-jitter=50", "main:app"]

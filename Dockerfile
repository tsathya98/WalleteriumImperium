# --- Build Stage ---
# Use an official Python runtime as a parent image
FROM python:3.11-slim as builder

# Set the working directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies required for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends build-essential

# Install poetry
RUN pip install poetry

# Copy only the files needed for dependency installation
COPY poetry.lock pyproject.toml ./

# Install dependencies without installing the project itself
# --no-root prevents installing the project, and --no-dev excludes dev dependencies
RUN poetry install --no-root --no-dev

# --- Final Stage ---
# Use a slim, non-builder image for the final container
FROM python:3.11-slim as final

# Set the working directory
WORKDIR /app

# Copy the virtual environment from the builder stage
COPY --from=builder /app/.venv ./.venv

# Activate the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application source code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# The command to run the application using uvicorn
# Gunicorn is a production-grade server, and UvicornWorker allows it to run our async app
CMD ["gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080", "main:app"] 
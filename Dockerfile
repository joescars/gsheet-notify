FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install system dependencies 
RUN apt-get update && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Create non-root user (optional but recommended)
RUN useradd -m appuser

RUN chown -R appuser:appuser /app

# Copy application source
COPY . .
#COPY .env .

USER appuser

# Expose the Flask port
EXPOSE 5588

# Run the existing script directly (no code modifications)
#CMD ["python", "run.py"]
CMD ["waitress-serve", "--listen=0.0.0.0:5588", "wsgi:app"]

# BYTE Wars Backend Dockerfile
# Builds the FastAPI battle engine service.

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies needed for asyncpg
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run FastAPI with uvicorn, reload enabled for development
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

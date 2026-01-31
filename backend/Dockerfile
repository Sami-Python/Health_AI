FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# We will mount the database file from the host for now (Hybrid approach)
# Cloud Run expects the container to listen on $PORT (default 8080)
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}

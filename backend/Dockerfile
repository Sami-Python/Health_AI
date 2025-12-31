FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# We will mount the database file from the host for now (Hybrid approach)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

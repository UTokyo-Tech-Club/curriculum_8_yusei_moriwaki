FROM --platform=linux/amd64 python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Use PORT environment variable from Cloud Run, default to 8080
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
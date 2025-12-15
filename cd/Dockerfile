FROM --platform=linux/amd64 python:3.8

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8080

# PORT環境変数が設定されている場合はそれを使用、なければ8080を使用
CMD uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080}

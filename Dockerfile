FROM python:3.11-slim

ENV PYTHONUNBUFFERED=True

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir --default-timeout=1000 --retries=10 --upgrade pip && \
    pip install --no-cache-dir --default-timeout=1000 --retries=10 -r requirements.txt

COPY . .

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005", "--reload"]

FROM python:3.11-slim

WORKDIR /app

# Устанавливаем PostgreSQL клиент для pg_dump
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Делаем скрипт запуска исполняемым
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"] 
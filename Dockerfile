FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Делаем скрипт запуска исполняемым
RUN chmod +x /app/start.sh

CMD ["/app/start.sh"] 
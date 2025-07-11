FROM python:3.11-slim

WORKDIR /app

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Установка московского часового пояса
ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Копируем backend, db и config.py из корня проекта
COPY web/backend/ /app/
COPY db /app/db
COPY config.py /app/config.py

# Установка Python зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Открытие порта
EXPOSE 8000

# Отладочная команда для проверки файлов
RUN ls -la /app/

# Команда запуска
CMD ["python", "/app/run.py"] 
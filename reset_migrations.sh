#!/bin/bash

echo "Resetting migration state..."
echo "This will mark all migrations as applied without actually running them."

# Устанавливаем переменную окружения для базы данных
export DB_DSN=postgresql+psycopg2://pkonline:pkonline@db:5432/pkonline

# Отмечаем все миграции как примененные
docker-compose run --rm -e DB_DSN=$DB_DSN bot python -m alembic stamp head

echo "Migration state reset complete!" 
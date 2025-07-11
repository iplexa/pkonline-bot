#!/bin/bash

echo "🚀 Запуск PK Online Bot с внешней БД"
echo "=================================="

# Проверяем наличие необходимых переменных
if [ -z "$EXTERNAL_DB_HOST" ]; then
    echo "❌ Ошибка: EXTERNAL_DB_HOST не установлен"
    exit 1
fi

if [ -z "$EXTERNAL_DB_USER" ]; then
    echo "❌ Ошибка: EXTERNAL_DB_USER не установлен"
    exit 1
fi

if [ -z "$EXTERNAL_DB_PASSWORD" ]; then
    echo "❌ Ошибка: EXTERNAL_DB_PASSWORD не установлен"
    exit 1
fi

if [ -z "$EXTERNAL_DB_NAME" ]; then
    echo "❌ Ошибка: EXTERNAL_DB_NAME не установлен"
    exit 1
fi

echo "✅ Все необходимые переменные окружения установлены"
echo "📊 Подключение к БД: $EXTERNAL_DB_HOST:$EXTERNAL_DB_PORT/$EXTERNAL_DB_NAME"

# Ждем подключения к БД
echo "⏳ Проверяем подключение к БД..."
until pg_isready -h $EXTERNAL_DB_HOST -p $EXTERNAL_DB_PORT -U $EXTERNAL_DB_USER; do
    echo "⏳ БД недоступна, ждем..."
    sleep 2
done

echo "✅ БД доступна"

echo "🔄 Применяем миграции..."
python -m alembic upgrade head || {
    echo "⚠️ Миграции не применились, но продолжаем..."
}

echo "🤖 Запускаем бота..."
python bot.py --external-db \
    --db-host $EXTERNAL_DB_HOST \
    --db-port $EXTERNAL_DB_PORT \
    --db-name $EXTERNAL_DB_NAME \
    --db-user $EXTERNAL_DB_USER \
    --db-password $EXTERNAL_DB_PASSWORD \
    ${EXTERNAL_DB_SSL:+--db-ssl} 
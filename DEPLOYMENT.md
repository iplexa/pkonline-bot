# 🚀 Развертывание PK Online Bot

## 📋 Обзор

PK Online Bot поддерживает работу как с локальной PostgreSQL БД (для разработки), так и с внешней БД (для продакшена).

## 🏗️ Архитектура

### Локальная разработка
- PostgreSQL в Docker контейнере
- Бот подключается к локальной БД
- Все данные хранятся в Docker volume

### Продакшен
- Внешняя PostgreSQL БД (например, AWS RDS, Google Cloud SQL, etc.)
- Бот подключается к внешней БД через SSL
- Поддержка бэкапов через админский интерфейс

## 🛠️ Установка и запуск

### 1. Локальная разработка

```bash
# Клонируем репозиторий
git clone <repository-url>
cd pkonline-bot

# Создаем .env файл
cp env.production.example .env
# Редактируем .env с вашими настройками

# Запускаем
docker-compose up -d
```

### 2. Продакшен с внешней БД

```bash
# Клонируем репозиторий
git clone <repository-url>
cd pkonline-bot

# Создаем .env файл для продакшена
cp env.production.example .env
# Редактируем .env с настройками внешней БД

# Запускаем с внешней БД
docker-compose -f docker-compose.prod.yml up -d
```

## ⚙️ Конфигурация

### Переменные окружения

#### Основные настройки
- `BOT_TOKEN` - токен Telegram бота
- `ADMIN_CHAT_ID` - ID админского чата
- `ADMIN_USER_ID` - ID администратора

#### Настройки БД
- `USE_EXTERNAL_DB` - использовать внешнюю БД (true/false)
- `EXTERNAL_DB_HOST` - хост внешней БД
- `EXTERNAL_DB_PORT` - порт БД (по умолчанию 5432)
- `EXTERNAL_DB_NAME` - имя БД
- `EXTERNAL_DB_USER` - пользователь БД
- `EXTERNAL_DB_PASSWORD` - пароль БД
- `EXTERNAL_DB_SSL` - использовать SSL (true/false)

#### Настройки логирования
- `GENERAL_CHAT_ID` - ID общего чата для логов
- `ADMIN_LOG_CHAT_ID` - ID админского чата для ошибок
- `THREAD_*` - ID тредов для разных типов событий

### Пример .env файла для продакшена

```env
# Настройки бота
BOT_TOKEN=your-telegram-bot-token
ADMIN_CHAT_ID=123456789
ADMIN_USER_ID=123456789

# Настройки внешней БД
USE_EXTERNAL_DB=true
EXTERNAL_DB_HOST=your-db-host.com
EXTERNAL_DB_PORT=5432
EXTERNAL_DB_NAME=pkonline_prod
EXTERNAL_DB_USER=your_user
EXTERNAL_DB_PASSWORD=your_password
EXTERNAL_DB_SSL=true

# Настройки чатов
GENERAL_CHAT_ID=0
ADMIN_LOG_CHAT_ID=0
```

## 🔧 Команды запуска

### С флагами командной строки

```bash
# Локальная БД
python bot.py

# Внешняя БД
python bot.py --external-db \
    --db-host your-host.com \
    --db-port 5432 \
    --db-name your_db \
    --db-user your_user \
    --db-password your_password \
    --db-ssl
```

### Через Docker

```bash
# Локальная разработка
docker-compose up -d

# Продакшен
docker-compose -f docker-compose.prod.yml up -d
```

## 💾 Бэкапы

### Создание бэкапа через админский интерфейс

1. Зайдите в админское меню бота
2. Выберите "📋 Управление очередями"
3. Нажмите "💾 Создать бэкап БД"
4. Получите SQL файл с бэкапом

### Создание бэкапа вручную

```bash
# Подключение к внешней БД
pg_dump -h your-host.com -p 5432 -U your_user -d your_db > backup.sql

# Восстановление из бэкапа
psql -h your-host.com -p 5432 -U your_user -d your_db < backup.sql
```

## 🔍 Мониторинг

### Логи

```bash
# Просмотр логов бота
docker-compose logs -f bot

# Просмотр логов БД (локальная)
docker-compose logs -f db
```

### Статус

```bash
# Статус контейнеров
docker-compose ps

# Проверка подключения к БД
docker-compose exec bot pg_isready -h $EXTERNAL_DB_HOST -p $EXTERNAL_DB_PORT -U $EXTERNAL_DB_USER
```

## 🚨 Устранение неполадок

### Проблемы с подключением к БД

1. Проверьте настройки подключения в .env
2. Убедитесь, что БД доступна с хоста
3. Проверьте SSL настройки
4. Проверьте права доступа пользователя

### Проблемы с бэкапами

1. Убедитесь, что pg_dump установлен в контейнере
2. Проверьте права доступа к БД
3. Проверьте свободное место на диске

### Проблемы с миграциями

```bash
# Принудительное применение миграций
docker-compose exec bot python -m alembic upgrade head

# Сброс миграций (осторожно!)
docker-compose exec bot python -m alembic downgrade base
```

## 📊 Отчеты

### Доступные отчеты

- 📊 Полный отчет - статистика за день
- ⏰ Отчет по рабочему времени - время работы сотрудников
- 📋 Отчет по заявлениям - статистика по очередям
- 📮 Экспорт просроченных заявлений почты - заявления, ждущие ответа более 3 дней

### Получение отчетов

1. Зайдите в админское меню
2. Выберите "📊 Отчеты"
3. Выберите нужный тип отчета

## 🔐 Безопасность

### Рекомендации

1. Используйте SSL для подключения к внешней БД
2. Ограничьте доступ к БД по IP
3. Используйте сложные пароли
4. Регулярно обновляйте зависимости
5. Создавайте бэкапы

### Переменные окружения

- Никогда не коммитьте .env файлы в git
- Используйте секреты в продакшене
- Ротация паролей БД 
# 🐳 Сравнение Docker Compose файлов

## 📋 Обзор

Данный документ сравнивает два файла Docker Compose:
- `docker-compose.yml` - для локальной разработки
- `docker-compose.prod.yml` - для продакшена

## 🔍 Основные различия

| Аспект | `docker-compose.yml` | `docker-compose.prod.yml` |
|--------|---------------------|---------------------------|
| **Назначение** | Локальная разработка | Продакшен |
| **Количество сервисов** | 2 (db + bot) | 1 (только bot) |
| **База данных** | Локальная PostgreSQL | Внешняя БД |
| **Команда запуска** | `start.sh` | `start_external_db.sh` |
| **Настройка БД** | `USE_EXTERNAL_DB: false` | `USE_EXTERNAL_DB: true` |

## 🗄️ База данных

### `docker-compose.yml` (Локальная БД)
```yaml
services:
  db:
    image: postgres:16
    restart: always
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_HOST_AUTH_METHOD: md5
    ports:
      - "5432:5432"  # Порт для внешнего доступа
    volumes:
      - pgdata:/var/lib/postgresql/data
      - ./postgresql.conf:/etc/postgresql/postgresql.conf:ro
      - ./pg_hba.conf:/etc/postgresql/pg_hba.conf:ro
    command: postgres -c config_file=/etc/postgresql/postgresql.conf -c hba_file=/etc/postgresql/pg_hba.conf

  bot:
    depends_on:
      - db  # Зависимость от локальной БД
```

### `docker-compose.prod.yml` (Внешняя БД)
```yaml
services:
  bot:
    # Нет сервиса БД - используется внешняя
    environment:
      USE_EXTERNAL_DB: true  # Принудительно внешняя БД
      EXTERNAL_DB_HOST: ${EXTERNAL_DB_HOST}
      EXTERNAL_DB_PORT: ${EXTERNAL_DB_PORT:-5432}
      EXTERNAL_DB_NAME: ${EXTERNAL_DB_NAME}
      EXTERNAL_DB_USER: ${EXTERNAL_DB_USER}
      EXTERNAL_DB_PASSWORD: ${EXTERNAL_DB_PASSWORD}
      EXTERNAL_DB_SSL: ${EXTERNAL_DB_SSL:-false}
```

## 🚀 Команды запуска

### `docker-compose.yml`
```yaml
bot:
  command: ["bash", "start.sh"]
```
- Использует `start.sh` - скрипт для локальной разработки
- Ждет готовности локальной БД
- Применяет миграции к локальной БД

### `docker-compose.prod.yml`
```yaml
bot:
  command: ["bash", "start_external_db.sh"]
```
- Использует `start_external_db.sh` - скрипт для продакшена
- Проверяет подключение к внешней БД
- Применяет миграции к внешней БД

## 🔧 Переменные окружения

### Общие переменные
Оба файла используют одинаковые переменные для:
- `BOT_TOKEN` - токен Telegram бота
- `ADMIN_CHAT_ID`, `ADMIN_USER_ID` - админские настройки
- `THREAD_*` - настройки тредов для логирования

### Различия в настройках БД

#### `docker-compose.yml`
```yaml
environment:
  USE_EXTERNAL_DB: ${USE_EXTERNAL_DB:-false}  # По умолчанию локальная
  DB_DSN: ${DB_DSN}  # DSN для локальной БД
  # Внешние настройки БД (опционально)
  EXTERNAL_DB_HOST: ${EXTERNAL_DB_HOST}
  EXTERNAL_DB_PORT: ${EXTERNAL_DB_PORT:-5432}
  # ... остальные внешние настройки
```

#### `docker-compose.prod.yml`
```yaml
environment:
  USE_EXTERNAL_DB: true  # Принудительно внешняя БД
  # Только внешние настройки БД
  EXTERNAL_DB_HOST: ${EXTERNAL_DB_HOST}
  EXTERNAL_DB_PORT: ${EXTERNAL_DB_PORT:-5432}
  EXTERNAL_DB_NAME: ${EXTERNAL_DB_NAME}
  EXTERNAL_DB_USER: ${EXTERNAL_DB_USER}
  EXTERNAL_DB_PASSWORD: ${EXTERNAL_DB_PASSWORD}
  EXTERNAL_DB_SSL: ${EXTERNAL_DB_SSL:-false}
```

## 💾 Volumes

### `docker-compose.yml`
```yaml
volumes:
  pgdata:  # Именованный volume для локальной БД
    driver: local

services:
  db:
    volumes:
      - pgdata:/var/lib/postgresql/data  # Данные БД
      - ./postgresql.conf:/etc/postgresql/postgresql.conf:ro  # Конфигурация
      - ./pg_hba.conf:/etc/postgresql/pg_hba.conf:ro  # Аутентификация

  bot:
    volumes:
      - .:/app  # Монтирование кода для разработки
```

### `docker-compose.prod.yml`
```yaml
services:
  bot:
    volumes:
      - .:/app  # Только код приложения
    # Нет volumes для БД - используется внешняя
```

## 🔗 Зависимости

### `docker-compose.yml`
```yaml
bot:
  depends_on:
    - db  # Бот ждет запуска локальной БД
```

### `docker-compose.prod.yml`
```yaml
bot:
  # Нет depends_on - нет локальной БД
```

## 🛠️ Использование

### Локальная разработка
```bash
# Запуск с локальной БД
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot
docker-compose logs -f db

# Остановка
docker-compose down
```

### Продакшен
```bash
# Запуск с внешней БД
docker-compose -f docker-compose.prod.yml up -d

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f bot

# Остановка
docker-compose -f docker-compose.prod.yml down
```

## 🔒 Безопасность

### Локальная разработка
- Простые пароли (для удобства)
- SSL отключен
- Доступ к БД с любого IP (0.0.0.0/0)
- Порт 5432 открыт для внешних клиентов

### Продакшен
- Сложные пароли (через переменные окружения)
- SSL включен (если настроен)
- Доступ к БД только с разрешенных IP
- Нет локальной БД (данные на внешнем сервере)

## 📊 Преимущества каждого подхода

### Локальная разработка (`docker-compose.yml`)
✅ **Преимущества:**
- Полный контроль над БД
- Быстрый запуск и остановка
- Возможность сброса данных
- Отладка на уровне БД
- Внешний доступ к БД (pgAdmin, DBeaver)

❌ **Недостатки:**
- Данные не синхронизированы с продакшеном
- Нужно настраивать локальную БД

### Продакшен (`docker-compose.prod.yml`)
✅ **Преимущества:**
- Использует продакшен БД
- Меньше ресурсов (нет локальной БД)
- Простота развертывания
- Данные синхронизированы

❌ **Недостатки:**
- Зависимость от внешней БД
- Нет локального доступа к БД
- Сложнее отладка

## 🔄 Миграция между средами

### Из разработки в продакшен
1. Настройте переменные окружения для внешней БД
2. Примените миграции к продакшен БД
3. Запустите с `docker-compose.prod.yml`

### Из продакшена в разработку
1. Создайте бэкап продакшен БД
2. Восстановите в локальную БД
3. Запустите с обычным `docker-compose.yml`

## 📝 Рекомендации

### Для разработчиков
- Используйте `docker-compose.yml` для локальной работы
- Создавайте бэкапы перед крупными изменениями
- Тестируйте на локальной БД перед продакшеном

### Для продакшена
- Используйте `docker-compose.prod.yml`
- Настройте мониторинг внешней БД
- Регулярно создавайте бэкапы
- Используйте SSL для подключения к БД 
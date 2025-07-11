# 🗄️ Подключение к базе данных

## 📋 Обзор

Данный документ описывает, как подключиться к базе данных PostgreSQL из внешних программ (pgAdmin, DBeaver, etc.) для разработки и администрирования.

## 🔧 Настройка подключения

### Параметры подключения

| Параметр | Значение |
|----------|----------|
| **Хост** | `localhost` или `127.0.0.1` |
| **Порт** | `5432` |
| **База данных** | `pkonline` (или значение из `POSTGRES_DB`) |
| **Пользователь** | `pkonline` (или значение из `POSTGRES_USER`) |
| **Пароль** | `pkonline` (или значение из `POSTGRES_PASSWORD`) |
| **SSL** | `Отключен` (для локальной разработки) |

### Переменные окружения

Убедитесь, что в файле `.env` установлены правильные значения:

```env
POSTGRES_DB=pkonline
POSTGRES_USER=pkonline
POSTGRES_PASSWORD=pkonline
```

## 🛠️ Подключение через pgAdmin

### 1. Установка pgAdmin
- Скачайте pgAdmin с [официального сайта](https://www.pgadmin.org/download/)
- Или используйте веб-версию: `docker run -p 5050:80 dpage/pgadmin4`

### 2. Создание подключения
1. Запустите pgAdmin
2. Правый клик на "Servers" → "Register" → "Server..."
3. Заполните параметры:

**General:**
- Name: `PK Online Bot Local`

**Connection:**
- Host name/address: `localhost`
- Port: `5432`
- Maintenance database: `pkonline`
- Username: `pkonline`
- Password: `pkonline`
- Save password: ✅

### 3. Тестирование подключения
- Нажмите "Save" и проверьте подключение
- В случае ошибки проверьте, что контейнеры запущены: `docker-compose ps`

## 🛠️ Подключение через DBeaver

### 1. Установка DBeaver
- Скачайте DBeaver с [официального сайта](https://dbeaver.io/download/)
- Или используйте версию Community (бесплатная)

### 2. Создание подключения
1. Запустите DBeaver
2. Нажмите "New Database Connection" (значок вилки)
3. Выберите "PostgreSQL"
4. Заполните параметры:

**Main:**
- Server Host: `localhost`
- Port: `5432`
- Database: `pkonline`
- Username: `pkonline`
- Password: `pkonline`

**Driver properties:**
- ssl: `false`
- sslmode: `disable`

### 3. Тестирование подключения
- Нажмите "Test Connection" для проверки
- При успехе нажмите "Finish"

## 🔍 Полезные SQL запросы

### Просмотр структуры БД
```sql
-- Список всех таблиц
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public';

-- Структура таблицы
\d+ table_name

-- Список пользователей
SELECT usename, usesysid FROM pg_user;
```

### Мониторинг активности
```sql
-- Активные подключения
SELECT pid, usename, application_name, client_addr, state 
FROM pg_stat_activity 
WHERE state = 'active';

-- Статистика по таблицам
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables;
```

### Работа с данными бота
```sql
-- Сотрудники
SELECT * FROM employees;

-- Заявления
SELECT * FROM applications ORDER BY submitted_at DESC LIMIT 10;

-- Рабочие дни
SELECT e.fio, wd.date, wd.start_time, wd.end_time, wd.total_work_time 
FROM work_days wd 
JOIN employees e ON wd.employee_id = e.id 
ORDER BY wd.date DESC LIMIT 10;
```

## 🚨 Устранение неполадок

### Ошибка подключения
```
FATAL: no pg_hba.conf entry for host "127.0.0.1", user "pkonline", database "pkonline", SSL off
```

**Решение:**
1. Проверьте, что контейнеры запущены: `docker-compose ps`
2. Перезапустите БД: `docker-compose restart db`
3. Проверьте логи: `docker-compose logs db`

### Ошибка аутентификации
```
FATAL: password authentication failed for user "pkonline"
```

**Решение:**
1. Проверьте пароль в `.env` файле
2. Пересоздайте контейнер БД: `docker-compose down && docker-compose up -d`
3. Проверьте переменные окружения: `docker-compose exec db env | grep POSTGRES`

### Порт занят
```
Error: bind: address already in use
```

**Решение:**
1. Проверьте, что порт 5432 не занят: `netstat -tulpn | grep 5432`
2. Остановите другие экземпляры PostgreSQL
3. Измените порт в `docker-compose.yml`:
   ```yaml
   ports:
     - "5433:5432"  # Внешний порт 5433
   ```

## 🔒 Безопасность

### Для продакшена
1. **Измените пароли** на сложные
2. **Включите SSL** в `postgresql.conf`:
   ```conf
   ssl = on
   ssl_cert_file = '/path/to/server.crt'
   ssl_key_file = '/path/to/server.key'
   ```
3. **Ограничьте доступ** в `pg_hba.conf`:
   ```conf
   host    all             all             192.168.1.0/24         md5
   ```

### Для разработки
- Используйте простые пароли (как в примерах)
- SSL отключен для упрощения
- Доступ разрешен с любого IP (`0.0.0.0/0`)

## 📊 Мониторинг через SQL

### Создание представлений для мониторинга
```sql
-- Представление для статистики заявлений
CREATE VIEW applications_stats AS
SELECT 
    queue_type,
    status,
    COUNT(*) as count,
    MIN(submitted_at) as first_app,
    MAX(submitted_at) as last_app
FROM applications 
GROUP BY queue_type, status;

-- Представление для статистики сотрудников
CREATE VIEW employees_stats AS
SELECT 
    e.fio,
    COUNT(a.id) as applications_processed,
    COUNT(wd.id) as work_days,
    SUM(wd.total_work_time) as total_hours
FROM employees e
LEFT JOIN applications a ON e.id = a.processed_by_id
LEFT JOIN work_days wd ON e.id = wd.employee_id
GROUP BY e.id, e.fio;
```

## 🛠️ Полезные команды Docker

```bash
# Проверка статуса БД
docker-compose exec db pg_isready -U pkonline

# Подключение к БД через psql
docker-compose exec db psql -U pkonline -d pkonline

# Создание бэкапа
docker-compose exec db pg_dump -U pkonline pkonline > backup.sql

# Восстановление из бэкапа
docker-compose exec -T db psql -U pkonline pkonline < backup.sql

# Просмотр логов БД
docker-compose logs -f db
```

## 📞 Поддержка

При проблемах с подключением:
1. Проверьте статус контейнеров: `docker-compose ps`
2. Просмотрите логи БД: `docker-compose logs db`
3. Проверьте настройки в `.env` файле
4. Убедитесь, что порт 5432 не занят другими процессами 
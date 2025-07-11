# 🐳 Управление данными в Docker

## 📋 Обзор

Данный документ описывает, как правильно управлять данными базы данных при работе с Docker Compose, чтобы избежать потери данных при пересборке контейнеров.

## 💾 Текущая конфигурация

### Локальная разработка (`docker-compose.yml`)
```yaml
services:
  db:
    image: postgres:16
    volumes:
      - pgdata:/var/lib/postgresql/data  # Именованный volume

volumes:
  pgdata:  # Именованный volume для сохранения данных
```

### Продакшен (`docker-compose.prod.yml`)
```yaml
services:
  bot:
    # Использует внешнюю БД, данные не хранятся локально
```

## ✅ Что уже настроено правильно

1. **Именованный volume `pgdata`** - данные БД сохраняются между пересборками
2. **Внешняя БД для продакшена** - данные хранятся на внешнем сервере
3. **Отделение данных от кода** - volume монтируется только для данных БД

## 🔧 Команды для управления данными

### Просмотр volumes
```bash
# Список всех volumes
docker volume ls

# Информация о конкретном volume
docker volume inspect pkonline-bot_pgdata
```

### Резервное копирование данных
```bash
# Создание бэкапа БД
docker-compose exec db pg_dump -U pkonline pkonline > backup_$(date +%Y%m%d_%H%M%S).sql

# Создание бэкапа через админ-панель бота
# (используйте кнопку "💾 Создать бэкап БД" в админ-меню)
```

### Восстановление данных
```bash
# Восстановление из SQL файла
docker-compose exec -T db psql -U pkonline pkonline < backup_file.sql
```

### Управление volumes
```bash
# Остановка контейнеров (данные сохраняются)
docker-compose down

# Остановка и удаление volumes (ВНИМАНИЕ: данные будут потеряны!)
docker-compose down -v

# Только пересборка образа (данные сохраняются)
docker-compose build --no-cache bot

# Полная пересборка (данные сохраняются)
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 🚨 Важные моменты

### ✅ Безопасные операции (данные сохраняются)
- `docker-compose build --no-cache`
- `docker-compose down` (без флага `-v`)
- `docker-compose up -d`
- Перезапуск отдельных сервисов

### ⚠️ Опасные операции (данные могут быть потеряны)
- `docker-compose down -v` (удаляет volumes)
- `docker volume rm pkonline-bot_pgdata` (удаляет volume)
- `docker system prune -a --volumes` (удаляет все неиспользуемые volumes)

## 🔄 Миграции и обновления

### Безопасное обновление
```bash
# 1. Создаем бэкап
docker-compose exec db pg_dump -U pkonline pkonline > backup_before_update.sql

# 2. Останавливаем контейнеры
docker-compose down

# 3. Пересобираем образ
docker-compose build --no-cache

# 4. Запускаем с применением миграций
docker-compose up -d

# 5. Проверяем, что все работает
docker-compose logs -f bot
```

### Принудительное применение миграций
```bash
# Если миграции не применились автоматически
docker-compose exec bot python -m alembic upgrade head
```

## 📊 Мониторинг использования диска

### Размер volume
```bash
# Просмотр размера volume
docker system df -v | grep pkonline-bot_pgdata
```

### Очистка неиспользуемых ресурсов
```bash
# Очистка неиспользуемых образов и контейнеров (НЕ volumes!)
docker system prune

# Очистка ВСЕГО, включая volumes (ОПАСНО!)
docker system prune -a --volumes
```

## 🛡️ Рекомендации по безопасности

### Регулярные бэкапы
1. **Автоматические бэкапы** через админ-панель бота
2. **Ручные бэкапы** перед крупными обновлениями
3. **Хранение бэкапов** в отдельном месте

### Проверка целостности
```bash
# Проверка подключения к БД
docker-compose exec db pg_isready -U pkonline

# Проверка размера БД
docker-compose exec db psql -U pkonline -c "SELECT pg_size_pretty(pg_database_size('pkonline'));"
```

## 🔧 Дополнительные настройки

### Настройка размера volume
```yaml
# В docker-compose.yml можно добавить ограничения
volumes:
  pgdata:
    driver_opts:
      type: none
      device: /path/to/custom/storage
      o: bind
```

### Настройка прав доступа
```bash
# Изменение прав на volume (если нужно)
sudo chown -R 999:999 /var/lib/docker/volumes/pkonline-bot_pgdata
```

## 📝 Чек-лист перед обновлением

- [ ] Создан бэкап БД
- [ ] Проверена работоспособность текущей версии
- [ ] Прочитаны изменения в новой версии
- [ ] Подготовлен план отката
- [ ] Выполнено обновление в тестовой среде (если возможно)

## 🆘 Восстановление после проблем

### Если данные потеряны
```bash
# 1. Остановить контейнеры
docker-compose down

# 2. Восстановить из бэкапа
docker-compose up -d db
docker-compose exec -T db psql -U pkonline pkonline < backup_file.sql

# 3. Запустить бота
docker-compose up -d bot
```

### Если volume поврежден
```bash
# 1. Создать новый volume
docker volume create pkonline-bot_pgdata_new

# 2. Восстановить данные
docker run --rm -v pkonline-bot_pgdata_new:/var/lib/postgresql/data -v $(pwd):/backup postgres:16 bash -c "cd /var/lib/postgresql && pg_restore -U pkonline -d pkonline /backup/backup_file.sql"

# 3. Обновить docker-compose.yml для использования нового volume
```

## 📞 Поддержка

При возникновении проблем с данными:
1. Не паникуйте - данные в именованном volume сохраняются
2. Создайте бэкап текущего состояния
3. Проверьте логи: `docker-compose logs db`
4. Обратитесь к документации PostgreSQL 
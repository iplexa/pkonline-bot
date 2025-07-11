# PK Online Web Interface

Веб-интерфейс для системы мониторинга заявлений PK Online Bot.

## Структура проекта

```
web/
├── backend/          # FastAPI бэкенд
│   ├── app/         # Основной код приложения
│   │   ├── config.py      # Конфигурация
│   │   ├── models.py      # Pydantic модели
│   │   ├── auth.py        # Аутентификация
│   │   ├── database.py    # Работа с БД
│   │   ├── services.py    # Бизнес-логика
│   │   └── routers/       # API роутеры
│   ├── main.py      # Точка входа
│   ├── run.py       # Скрипт запуска
│   └── requirements.txt
└── frontend/        # React фронтенд
    ├── src/
    │   ├── components/    # React компоненты
    │   ├── contexts/      # React контексты
    │   └── ...
    ├── public/
    └── package.json
```

## Функциональность

### Блоки дашборда:

1. **Сотрудники** - статус всех сотрудников:
   - На рабочем месте / На перерыве / Не работает
   - Текущая задача (если работает)
   - Время работы/перерыва

2. **Последние заявления** - последние 10 обработанных заявлений:
   - ID заявления и ФИО
   - Тип очереди (ЛК, ЕПГУ, Почта, Проблемные)
   - Статус обработки
   - Сотрудник-обработчик

3. **Статистика очередей** - количество заявлений по статусам:
   - В очереди
   - В обработке
   - Принято
   - Отклонено
   - Проблемные

## Установка и запуск

### Вариант 1: Docker Compose (рекомендуется)

1. **Запуск всего стека (бот + веб-интерфейс):**
   ```bash
   # Из корневой папки проекта
   docker-compose up -d
   ```

2. **Запуск только веб-интерфейса:**
   ```bash
   # Из корневой папки проекта
   start_web.bat
   ```

3. **Запуск в режиме разработки (без Nginx):**
   ```bash
   start_web_dev.bat
   ```

4. **Остановка веб-сервисов:**
   ```bash
   stop_web.bat
   ```

**Доступные сервисы:**
- Веб-интерфейс (prod): http://localhost:3000
- Веб-интерфейс (dev): http://localhost:3001
- API документация: http://localhost:8000/docs
- База данных: localhost:5432

### Вариант 2: Локальная разработка

#### Бэкенд (FastAPI)

1. Перейдите в папку backend:
```bash
cd web/backend
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Запустите сервер:
```bash
python run.py
```

Сервер будет доступен по адресу: http://localhost:8000
API документация: http://localhost:8000/docs

#### Фронтенд (React)

1. Перейдите в папку frontend:
```bash
cd web/frontend
```

2. Установите зависимости:
```bash
npm install
```

3. Запустите приложение:
```bash
npm start
```

Приложение будет доступно по адресу: http://localhost:3000

## Аутентификация

- **Логин**: используйте tg_id сотрудника из базы данных
- **Пароль**: для простоты используется тот же tg_id (в продакшене нужно изменить)
- **Админы**: могут регистрировать новых пользователей

## API Endpoints

### Аутентификация
- `POST /auth/login` - вход в систему
- `POST /auth/register` - регистрация (только для админов)

### Дашборд
- `GET /dashboard/employees/status` - статус сотрудников
- `GET /dashboard/applications/recent` - последние заявления
- `GET /dashboard/queues/statistics` - статистика очередей

## Настройка

Основные настройки находятся в `backend/app/config.py`:

- `SECRET_KEY` - ключ для JWT токенов
- `CORS_ORIGINS` - разрешенные домены для CORS
- `ACCESS_TOKEN_EXPIRE_MINUTES` - время жизни токена

## Docker

### Структура контейнеров:
- **web-backend**: FastAPI приложение на Python 3.11
- **web-frontend**: React приложение с Nginx
- **db**: PostgreSQL (используется существующая БД)

### Переменные окружения:
```bash
# Настройки веб-интерфейса
WEB_SECRET_KEY=your-secret-key-change-in-production
WEB_DEBUG=false

# Настройки БД (наследуются от основного проекта)
DB_DSN=postgresql+asyncpg://user:password@db:5432/pkonline
USE_EXTERNAL_DB=false
```

### Команды Docker:
```bash
# Запуск всех сервисов
docker-compose up -d

# Запуск только веб-сервисов
docker-compose up -d web-backend web-frontend

# Просмотр логов
docker-compose logs -f web-backend
docker-compose logs -f web-frontend

# Остановка веб-сервисов
docker-compose stop web-backend web-frontend

# Пересборка образов
docker-compose build --no-cache web-backend web-frontend

# Очистка и пересборка
docker-compose down
docker system prune -f
docker-compose up -d --build
```

### Решение проблем:

1. **Ошибка npm ci**: Запустите `web/generate-lockfile.bat` для создания package-lock.json
2. **Проблемы с путями**: Убедитесь, что запускаете из корневой директории проекта
3. **Конфликты портов**: Остановите другие сервисы на портах 3000 и 8000

## Разработка

### Структура бэкенда:
- **Модульная архитектура** с разделением ответственности
- **Сервисный слой** для бизнес-логики
- **Роутеры** для API эндпоинтов
- **Pydantic модели** для валидации данных

### Структура фронтенда:
- **React Hooks** для управления состоянием
- **Context API** для аутентификации
- **Bootstrap** для UI компонентов
- **Axios** для HTTP запросов 
# Система логирования в Telegram

## Обзор

Система логирования разделена на два чата:

1. **Общий чат** (супергруппа) - для всех событий с разделением по тредам
2. **Админский чат** - для ошибок и технических логов

## Настройка

### 1. Создание общего чата (супергруппа)

1. Создайте новую супергруппу в Telegram
2. Добавьте бота в группу
3. Сделайте бота администратором группы
4. Включите треды в настройках группы
5. Создайте треды для каждого типа событий (см. список ниже)

### 2. Создание админского чата

1. Создайте обычный чат с ботом
2. Этот чат будет использоваться для ошибок и технических логов

### 3. Настройка через админку

1. Зайдите в админ-меню бота
2. Выберите "⚙️ Настройка чатов"
3. Настройте общий чат и админский чат
4. Настройте треды для каждого типа событий

### 4. Настройка через переменные окружения

Альтернативно можно настроить через переменные окружения:

```bash
# Основные чаты
GENERAL_CHAT_ID=-1001234567890
ADMIN_LOG_CHAT_ID=123456789

# ID тредов в общем чате
THREAD_WORK_TIME=1
THREAD_LK_PROCESSING=2
THREAD_LK_PROBLEM=3
THREAD_EPGU_ACCEPTED=4
THREAD_EPGU_MAIL_QUEUE=5
THREAD_EPGU_PROBLEM=6
THREAD_MAIL_CONFIRMED=7
THREAD_MAIL_REJECTED=8
THREAD_PROBLEM_SOLVED=9
THREAD_PROBLEM_SOLVED_QUEUE=10
THREAD_PROBLEM_IN_PROGRESS=11
THREAD_QUEUE_UPDATED=12
THREAD_ESCALATION=13
```

## Типы событий и треды

### ⏰ Рабочее время
- **Тред**: `work_time`
- **События**:
  - Начало рабочего дня
  - Окончание рабочего дня
  - Начало перерыва
  - Окончание перерыва

### 📋 ЛК - Обработка
- **Тред**: `lk_processing`
- **События**:
  - Заявление принято
  - Заявление отклонено

### ⚠️ ЛК - Проблема
- **Тред**: `lk_problem`
- **События**:
  - Заявление помечено как проблемное

### ✅ ЕПГУ - Принято
- **Тред**: `epgu_accepted`
- **События**:
  - Заявление принято

### 📮 ЕПГУ - Отправлено в очередь почты
- **Тред**: `epgu_mail_queue`
- **События**:
  - Заявление отправлено на подпись
  - Заявление отправлено на подпись и запрос сканов
  - Заявление отправлено на получение сканов

### ⚠️ ЕПГУ - Проблема
- **Тред**: `epgu_problem`
- **События**:
  - Заявление помечено как проблемное

### ✅ Почта - Подтверждено
- **Тред**: `mail_confirmed`
- **События**:
  - Заявление подтверждено

### ❌ Почта - Отклонено
- **Тред**: `mail_rejected`
- **События**:
  - Заявление отклонено

### ✅ Разбор проблем - Исправлено
- **Тред**: `problem_solved`
- **События**:
  - Проблема исправлена

### 🔄 Разбор проблем - Исправлено отправлено в очередь
- **Тред**: `problem_solved_queue`
- **События**:
  - Проблема исправлена и заявление отправлено в очередь

### 🔄 Разбор проблем - Процесс решения запущен
- **Тред**: `problem_in_progress`
- **События**:
  - Процесс решения проблемы запущен

### 📊 Очереди - Обновлен список заявлений
- **Тред**: `queue_updated`
- **События**:
  - Обновлен список заявлений в очереди

### 🚨 Эскалация
- **Тред**: `escalation`
- **События**:
  - Эскалация заявления

## Получение ID чата и тредов

### ID чата
1. Добавьте @userinfobot в нужный чат
2. Отправьте любое сообщение
3. Бот покажет ID чата

### ID треда
1. Создайте тред в супергруппе
2. Отправьте сообщение в тред
3. Перешлите это сообщение @userinfobot
4. В ответе будет указан `message_thread_id` - это ID треда

## Формат сообщений

Все сообщения отправляются в формате HTML с эмодзи для лучшей читаемости:

```
✅ ЛК: Заявление принято
👤 Иван Иванов
📋 ID: 12345
👨‍💼 Петров Петр Петрович
```

## Обработка ошибок

Все ошибки логируются в админский чат с полным стектрейсом:

```
🚨 ОШИБКА [2024-01-15 14:30:25]

Описание ошибки

<code>Полный стектрейс</code>
```

## Технические детали

- Система автоматически перезагружает конфигурацию при изменении файла `chat_config.json`
- Если тред не настроен, сообщения не отправляются (без ошибок)
- Если админский чат не настроен, ошибки выводятся в консоль
- Все логирование происходит асинхронно и не блокирует основной поток 
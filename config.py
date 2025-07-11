import os
import json
import argparse

# Парсим аргументы командной строки
parser = argparse.ArgumentParser(description='PK Online Bot')
parser.add_argument('--external-db', action='store_true', help='Использовать внешнюю БД вместо локальной')
parser.add_argument('--db-host', type=str, help='Хост внешней БД')
parser.add_argument('--db-port', type=int, default=5432, help='Порт внешней БД')
parser.add_argument('--db-name', type=str, help='Имя БД')
parser.add_argument('--db-user', type=str, help='Пользователь БД')
parser.add_argument('--db-password', type=str, help='Пароль БД')
parser.add_argument('--db-ssl', action='store_true', help='Использовать SSL для подключения к БД')

# Парсим аргументы только если они переданы
args, unknown = parser.parse_known_args()

BOT_TOKEN = os.getenv("BOT_TOKEN", "your-telegram-bot-token")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))  # id чата для логов/уведомлений
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "123456789"))  # id администратора 

# Настройка подключения к БД
def get_db_dsn():
    # Если указан флаг внешней БД или переменная окружения
    if args.external_db or os.getenv("USE_EXTERNAL_DB", "").lower() in ["true", "1", "yes"]:
        # Приоритет аргументам командной строки, затем переменным окружения
        db_host = args.db_host or os.getenv("EXTERNAL_DB_HOST", "localhost")
        db_port = args.db_port or int(os.getenv("EXTERNAL_DB_PORT", "5432"))
        db_name = args.db_name or os.getenv("EXTERNAL_DB_NAME", "pkonline")
        db_user = args.db_user or os.getenv("EXTERNAL_DB_USER", "user")
        db_password = args.db_password or os.getenv("EXTERNAL_DB_PASSWORD", "password")
        
        # Формируем DSN для внешней БД
        dsn = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
        
        # Добавляем SSL если указан
        if args.db_ssl or os.getenv("EXTERNAL_DB_SSL", "").lower() in ["true", "1", "yes"]:
            dsn += "?sslmode=require"
        
        return dsn
    else:
        # Используем локальную БД
        return os.getenv("DB_DSN", "postgresql+asyncpg://user:password@localhost:5432/pkonline")

DB_DSN = get_db_dsn()

# Загружаем настройки чатов из файла
def load_chat_config():
    config_file = "chat_config.json"
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            pass
    return {}

chat_config = load_chat_config()

# Настройки чатов для логирования
GENERAL_CHAT_ID = chat_config.get("GENERAL_CHAT_ID", int(os.getenv("GENERAL_CHAT_ID", "0")))  # ID общего чата (супергруппа)
ADMIN_LOG_CHAT_ID = chat_config.get("ADMIN_LOG_CHAT_ID", int(os.getenv("ADMIN_LOG_CHAT_ID", "0")))  # ID админского чата для ошибок

# ID тредов в общем чате
DEFAULT_THREAD_IDS = {
    "work_time": int(os.getenv("THREAD_WORK_TIME", "0")),  # Рабочее время
    "lk_processing": int(os.getenv("THREAD_LK_PROCESSING", "0")),  # ЛК - Обработка
    "lk_problem": int(os.getenv("THREAD_LK_PROBLEM", "0")),  # ЛК - Проблема
    "epgu_accepted": int(os.getenv("THREAD_EPGU_ACCEPTED", "0")),  # ЕПГУ - Принято
    "epgu_mail_queue": int(os.getenv("THREAD_EPGU_MAIL_QUEUE", "0")),  # ЕПГУ - Отправлено в очередь почты
    "epgu_problem": int(os.getenv("THREAD_EPGU_PROBLEM", "0")),  # ЕПГУ - проблема
    "mail_confirmed": int(os.getenv("THREAD_MAIL_CONFIRMED", "0")),  # Почта - Подтверждено
    "mail_rejected": int(os.getenv("THREAD_MAIL_REJECTED", "0")),  # Почта - Отклонено
    "problem_solved": int(os.getenv("THREAD_PROBLEM_SOLVED", "0")),  # Разбор проблем - Исправлено
    "problem_solved_queue": int(os.getenv("THREAD_PROBLEM_SOLVED_QUEUE", "0")),  # Разбор проблем - Исправлено отправлено в очередь
    "problem_in_progress": int(os.getenv("THREAD_PROBLEM_IN_PROGRESS", "0")),  # Разбор проблем - процесс решения запущен
    "queue_updated": int(os.getenv("THREAD_QUEUE_UPDATED", "0")),  # Очереди - Обновлен список заявлений
    "escalation": int(os.getenv("THREAD_ESCALATION", "0")),  # Эскалация
}

# Объединяем настройки из файла с дефолтными
THREAD_IDS = DEFAULT_THREAD_IDS.copy()
if "THREAD_IDS" in chat_config:
    THREAD_IDS.update(chat_config["THREAD_IDS"]) 
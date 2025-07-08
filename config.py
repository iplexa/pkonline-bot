import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "your-telegram-bot-token")
DB_DSN = os.getenv("DB_DSN", "postgresql+asyncpg://user:password@localhost:5432/pkonline")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))  # id чата для логов/уведомлений 
import sys
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Добавляем путь к родительской директории для импорта модулей бота
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from db.session import get_session as get_bot_session

# Используем существующую сессию из бота
async def get_session():
    async for session in get_bot_session():
        yield session 
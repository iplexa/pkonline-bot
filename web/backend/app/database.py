import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Добавляем путь к родительской директории для импорта модулей бота
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from app.config import DATABASE_URL

# Создаем синхронный движок
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Получить сессию базы данных"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 
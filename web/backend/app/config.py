import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Основные настройки
    app_name: str = "PK Online Web Interface"
    version: str = "1.0.0"
    debug: bool = False
    
    # Настройки базы данных
    use_external_db: bool = False
    db_dsn: str = ""
    external_db_host: str = ""
    external_db_port: int = 5432
    external_db_name: str = ""
    external_db_user: str = ""
    external_db_password: str = ""
    external_db_ssl: bool = False
    
    @property
    def database_url(self) -> str:
        """Формирует URL для подключения к базе данных"""
        if self.use_external_db and self.db_dsn:
            return self.db_dsn
        elif self.use_external_db:
            # Формируем DSN из отдельных параметров
            ssl_mode = "?sslmode=require" if self.external_db_ssl else ""
            return f"postgresql://{self.external_db_user}:{self.external_db_password}@{self.external_db_host}:{self.external_db_port}/{self.external_db_name}{ssl_mode}"
        else:
            # Локальная база данных
            return f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'postgres')}@db:5432/{os.getenv('POSTGRES_DB', 'pkonline')}"
    
    # Настройки безопасности
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS настройки
    cors_origins: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://web-frontend:80"
    ]
    
    # Настройки сервера
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        env_prefix = "WEB_"

settings = Settings()

# Для обратной совместимости
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
DATABASE_URL = settings.database_url 
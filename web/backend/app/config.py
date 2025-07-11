import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # Основные настройки
    app_name: str = "PK Online Web Interface"
    version: str = "1.0.0"
    debug: bool = False
    
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
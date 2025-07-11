from datetime import datetime, timedelta
from typing import Optional
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from .config import settings
from .models import UserLogin, UserCreate, Token
from .database import get_session
from db.models import Employee

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Employee:
    """Получение текущего пользователя из токена"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    async for session in get_session():
        stmt = select(Employee).where(Employee.tg_id == username)
        result = await session.execute(stmt)
        user = result.scalars().first()
        if user is None:
            raise credentials_exception
        return user

async def get_current_admin_user(current_user: Employee = Depends(get_current_user)) -> Employee:
    """Проверка прав администратора"""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user

async def authenticate_user(username: str, password: str) -> Optional[Employee]:
    """Аутентификация пользователя"""
    async for session in get_session():
        stmt = select(Employee).where(Employee.tg_id == username)
        result = await session.execute(stmt)
        user = result.scalars().first()
        
        if not user:
            return None
        
        # Для простоты используем tg_id как пароль (в продакшене нужно хешировать)
        if password != user.tg_id:
            return None
        
        return user

async def create_user(user_data: UserCreate) -> Employee:
    """Создание нового пользователя"""
    async for session in get_session():
        # Проверяем, существует ли пользователь
        stmt = select(Employee).where(Employee.tg_id == user_data.username)
        result = await session.execute(stmt)
        existing_user = result.scalars().first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists"
            )
        
        # Создаем нового пользователя
        new_user = Employee(
            tg_id=user_data.username,
            fio=user_data.fio,
            is_admin=user_data.is_admin
        )
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user 
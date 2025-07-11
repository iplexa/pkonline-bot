from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer

from ..models import UserLogin, UserCreate, Token
from ..auth import authenticate_user, create_user, get_current_admin_user, create_access_token
from ..config import settings

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    """Вход в систему"""
    user = await authenticate_user(user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.tg_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=Token)
async def register(user_data: UserCreate, current_user = Depends(get_current_admin_user)):
    """Регистрация нового пользователя (только для админов)"""
    new_user = await create_user(user_data)
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": new_user.tg_id}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"} 
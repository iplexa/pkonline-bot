from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
import jwt
from app.database import get_db
from app.config import settings
from app.auth import get_current_user, get_current_admin_user
from db.models import Employee
from pydantic import BaseModel

router = APIRouter(prefix="/auth", tags=["auth"])

class LoginRequest(BaseModel):
    fio: str
    password: str

class RegisterRequest(BaseModel):
    tg_id: str
    fio: str

class SetPasswordRequest(BaseModel):
    employee_id: int
    new_password: str

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt

@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Вход в систему по ФИО и паролю (plain)"""
    employee = db.query(Employee).filter(Employee.fio == request.fio).first()
    if not employee or employee.password != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверные ФИО или пароль"
        )
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={"sub": str(employee.id)}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": employee.id,
            "fio": employee.fio,
            "is_admin": employee.is_admin
        }
    }

@router.get("/me")
def get_current_user_info(current_user: Employee = Depends(get_current_user)):
    """Получить информацию о текущем пользователе"""
    return {
        "id": current_user.id,
        "fio": current_user.fio,
        "tg_id": current_user.tg_id,
        "is_admin": current_user.is_admin
    }

@router.post("/register")
def register_admin(request: RegisterRequest, db: Session = Depends(get_db)):
    """Регистрация администратора (только для первого пользователя)"""
    # Проверяем, есть ли уже сотрудники в системе
    existing_employees = db.query(Employee).count()
    
    if existing_employees > 0:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Регистрация новых пользователей отключена"
        )
    
    # Создаем первого администратора
    employee = Employee(
        tg_id=request.tg_id,
        fio=request.fio,
        is_admin=True
    )
    
    db.add(employee)
    db.commit()
    db.refresh(employee)
    
    return {"message": "Администратор успешно зарегистрирован", "employee_id": employee.id}

@router.post("/set_password")
def set_employee_password(request: SetPasswordRequest, db: Session = Depends(get_db), current_admin = Depends(get_current_admin_user)):
    employee = db.query(Employee).filter(Employee.id == request.employee_id).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Сотрудник не найден")
    employee.password = request.new_password
    db.commit()
    return {"message": f"Пароль для {employee.fio} обновлен"} 
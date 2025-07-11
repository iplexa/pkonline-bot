from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Модели аутентификации
class UserLogin(BaseModel):
    username: str
    password: str

class UserCreate(BaseModel):
    username: str
    password: str
    fio: str
    is_admin: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str

# Модели данных
class EmployeeStatus(BaseModel):
    id: int
    fio: str
    is_admin: bool
    status: str
    current_task: Optional[str] = None
    start_time: Optional[datetime] = None
    work_duration: Optional[str] = None

class ApplicationInfo(BaseModel):
    id: int
    fio: str
    queue_type: str
    status: str
    processed_by_fio: Optional[str] = None
    submitted_at: datetime
    processed_at: Optional[datetime] = None

class QueueStatistics(BaseModel):
    queue_type: str
    total: int
    queued: int
    in_progress: int
    accepted: int
    rejected: int
    problem: int 
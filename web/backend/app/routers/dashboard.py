from fastapi import APIRouter, Depends
from typing import List

from ..models import EmployeeStatus, ApplicationInfo, QueueStatistics
from ..auth import get_current_user
from ..services import EmployeeService, ApplicationService, QueueService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/employees/status", response_model=List[EmployeeStatus])
async def get_employees_status(current_user = Depends(get_current_user)):
    """Получение статуса всех сотрудников"""
    return await EmployeeService.get_employees_status()

@router.get("/applications/recent", response_model=List[ApplicationInfo])
async def get_recent_applications(current_user = Depends(get_current_user)):
    """Получение последних обработанных заявлений"""
    return await ApplicationService.get_recent_applications()

@router.get("/queues/statistics", response_model=List[QueueStatistics])
async def get_queue_statistics(current_user = Depends(get_current_user)):
    """Получение статистики по очередям"""
    return await QueueService.get_queue_statistics() 
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.dashboard_service import DashboardService
from app.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/employees/status")
def get_employees_status(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить статус всех сотрудников"""
    service = DashboardService(db)
    return service.get_employees_status()

@router.get("/applications/recent")
def get_recent_applications(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить последние 10 обработанных заявлений"""
    service = DashboardService(db)
    return service.get_recent_applications()

@router.get("/queues/statistics")
def get_queue_statistics(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить статистику по всем очередям"""
    service = DashboardService(db)
    return service.get_queue_statistics()

@router.get("/queues/{queue_type}/applications")
def get_queue_applications(
    queue_type: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить все заявления из конкретной очереди"""
    service = DashboardService(db)
    return service.get_queue_applications(queue_type)



@router.get("/charts/lk")
def get_lk_chart(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить данные для круговой диаграммы ЛК"""
    service = DashboardService(db)
    return service.get_lk_chart_data()

@router.get("/charts/epgu")
def get_epgu_chart(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить данные для круговой диаграммы ЕПГУ"""
    service = DashboardService(db)
    return service.get_epgu_chart_data() 
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.services.dashboard_service import DashboardService
from app.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/employees/status")
def get_employees_status(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить статус всех сотрудников"""
    service = DashboardService(db)
    return service.get_employees_status()

@router.post("/employees/status/refresh")
def refresh_employees_status(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Принудительно обновить статус сотрудников (очистить кэш)"""
    service = DashboardService(db)
    service.clear_cache()
    return {"message": "Кэш очищен, данные будут обновлены при следующем запросе"}

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

@router.get("/full_report")
def get_full_report(
    date: str = Query(None, description="Дата отчета в формате YYYY-MM-DD"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Получить полный отчет по всем сотрудникам за выбранную дату (или за сегодня)"""
    service = DashboardService(db)
    report_date = None
    if date:
        try:
            report_date = datetime.strptime(date, "%Y-%m-%d").date()
        except Exception:
            raise HTTPException(status_code=400, detail="Некорректный формат даты. Используйте YYYY-MM-DD.")
    return service.get_full_report_by_date(report_date) 
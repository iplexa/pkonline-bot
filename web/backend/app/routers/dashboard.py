from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from app.database import get_db
from app.services.dashboard_service import DashboardService
from app.auth import get_current_user, get_current_admin_user
from datetime import datetime
from db.models import ApplicationStatusEnum, Application, WorkDay

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

@router.post("/queues/{queue_type}/next")
def assign_next_application(
    queue_type: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Взять следующее заявление из очереди (назначить себе и перевести в обработку)"""
    service = DashboardService(db)
    app = service.assign_next_application(queue_type, current_user.id)
    if not app:
        raise HTTPException(status_code=404, detail="Нет доступных заявлений в очереди")
    return app

@router.get("/queues/{queue_type}/search")
def search_applications(
    queue_type: str,
    fio: str = Query(..., description="ФИО или email для поиска"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Поиск заявлений по ФИО (или email для epgu_mail)"""
    service = DashboardService(db)
    return service.search_applications(queue_type, fio)

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

class ApplicationProcessRequest(BaseModel):
    action: str  # accept, reject, to_mail, to_problem, confirm_scans, confirm_signature
    reason: Optional[str] = None
    # Для некоторых действий могут понадобиться дополнительные поля

@router.patch("/applications/{app_id}/process")
def process_application(
    app_id: int,
    request: ApplicationProcessRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Обработать заявление ЕПГУ или Почты (принять, отклонить, перевести, подтвердить сканы/подпись, проблемные)"""
    service = DashboardService(db)
    app = db.query(Application).filter(Application.id == app_id).first()
    if not app:
        raise HTTPException(status_code=404, detail="Заявление не найдено")
    # Проверка прав доступа (по аналогии с ботом)
    if app.queue_type.startswith("epgu") and not current_user.has_access("epgu"):
        raise HTTPException(status_code=403, detail="Нет доступа к ЕПГУ очереди")
    if app.queue_type == "epgu_mail" and not current_user.has_access("mail"):
        raise HTTPException(status_code=403, detail="Нет доступа к очереди почты")
    # Действия
    if request.action == "accept":
        service.accept_application(app, current_user.id)
    elif request.action == "reject":
        if not request.reason:
            raise HTTPException(status_code=400, detail="Нужна причина отклонения")
        service.reject_application(app, current_user.id, request.reason)
    elif request.action == "to_mail":
        service.move_to_mail_queue(app, current_user.id)
    elif request.action == "to_problem":
        if not request.reason:
            raise HTTPException(status_code=400, detail="Нужна причина для проблемного")
        service.move_to_problem_queue(app, current_user.id, request.reason)
    elif request.action == "confirm_scans":
        service.confirm_scans(app, current_user.id)
    elif request.action == "confirm_signature":
        service.confirm_signature(app, current_user.id)
    else:
        raise HTTPException(status_code=400, detail="Неизвестное действие")
    db.commit()
    return {"success": True}

@router.patch("/workday/{workday_id}/applications_processed")
def update_applications_processed(
    workday_id: int,
    applications_processed: int = Body(..., embed=True),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin_user)
):
    """Изменить количество обработанных заявлений для рабочего дня (только для админов)"""
    workday = db.query(WorkDay).filter(WorkDay.id == workday_id).first()
    if not workday:
        raise HTTPException(status_code=404, detail="Рабочий день не найден")
    workday.applications_processed = applications_processed
    db.commit()
    return {"success": True, "workday_id": workday_id, "applications_processed": applications_processed} 
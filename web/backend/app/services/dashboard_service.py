from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import pytz
from db.models import Employee, Application, WorkDay, ApplicationStatusEnum
from typing import List, Dict, Any

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        self.today = datetime.now(self.moscow_tz).date()

    def get_employees_status(self) -> List[Dict[str, Any]]:
        """Получить статус всех сотрудников"""
        employees = self.db.query(Employee).all()
        result = []
        
        for employee in employees:
            # Найти текущий рабочий день
            work_day = self.db.query(WorkDay).filter(
                and_(
                    WorkDay.employee_id == employee.id,
                    WorkDay.date == self.today
                )
            ).first()
            
            status = "Не работает"
            current_task = None
            work_duration = None
            start_time = None
            
            if work_day:
                if work_day.start_time and not work_day.end_time:
                    if work_day.break_start_time and not work_day.break_end_time:
                        status = "На перерыве"
                    else:
                        status = "На рабочем месте"
                        
                        # Вычислить время работы
                        if work_day.break_start_time and work_day.break_end_time:
                            # Учитываем перерыв
                            work_time = (work_day.break_start_time - work_day.start_time) + \
                                       (datetime.now(self.moscow_tz) - work_day.break_end_time)
                        else:
                            work_time = datetime.now(self.moscow_tz) - work_day.start_time
                        
                        hours = int(work_time.total_seconds() // 3600)
                        minutes = int((work_time.total_seconds() % 3600) // 60)
                        work_duration = f"{hours:02d}:{minutes:02d}"
                        
                elif work_day.end_time:
                    status = "Рабочий день завершен"
                    
                start_time = work_day.start_time
                
                # Получить текущую задачу (последнее заявление в обработке)
                current_application = self.db.query(Application).filter(
                    and_(
                        Application.processed_by == employee.id,
                        Application.status == ApplicationStatusEnum.IN_PROGRESS
                    )
                ).order_by(Application.processed_at.desc()).first()
                
                if current_application:
                    current_task = f"Заявление #{current_application.id} ({current_application.fio})"
            
            result.append({
                "id": employee.id,
                "fio": employee.fio,
                "status": status,
                "current_task": current_task,
                "work_duration": work_duration,
                "start_time": start_time,
                "is_admin": employee.is_admin
            })
        
        return result

    def get_recent_applications(self) -> List[Dict[str, Any]]:
        """Получить последние 10 обработанных заявлений"""
        applications = self.db.query(Application).filter(
            Application.status.in_([ApplicationStatusEnum.ACCEPTED, ApplicationStatusEnum.REJECTED, ApplicationStatusEnum.PROBLEM])
        ).order_by(Application.processed_at.desc()).limit(10).all()
        
        result = []
        for app in applications:
            processed_by = None
            if app.processed_by:
                employee = self.db.query(Employee).filter(Employee.id == app.processed_by).first()
                processed_by = employee.fio if employee else None
            
            result.append({
                "id": app.id,
                "fio": app.fio,
                "queue_type": app.queue_type,
                "status": app.status.value,
                "submitted_at": app.submitted_at,
                "processed_at": app.processed_at,
                "processed_by_fio": processed_by
            })
        
        return result

    def get_queue_statistics(self) -> List[Dict[str, Any]]:
        """Получить статистику по всем очередям"""
        queue_types = ['lk', 'epgu', 'epgu_mail', 'epgu_problem']
        result = []
        
        for queue_type in queue_types:
            # Общее количество
            total = self.db.query(func.count(Application.id)).filter(
                Application.queue_type == queue_type
            ).scalar()
            
            # В очереди
            queued = self.db.query(func.count(Application.id)).filter(
                and_(
                    Application.queue_type == queue_type,
                    Application.status == ApplicationStatusEnum.QUEUED
                )
            ).scalar()
            
            # В обработке
            in_progress = self.db.query(func.count(Application.id)).filter(
                and_(
                    Application.queue_type == queue_type,
                    Application.status == ApplicationStatusEnum.IN_PROGRESS
                )
            ).scalar()
            
            # Принято
            accepted = self.db.query(func.count(Application.id)).filter(
                and_(
                    Application.queue_type == queue_type,
                    Application.status == ApplicationStatusEnum.ACCEPTED
                )
            ).scalar()
            
            # Отклонено
            rejected = self.db.query(func.count(Application.id)).filter(
                and_(
                    Application.queue_type == queue_type,
                    Application.status == ApplicationStatusEnum.REJECTED
                )
            ).scalar()
            
            # Проблемные
            problem = self.db.query(func.count(Application.id)).filter(
                and_(
                    Application.queue_type == queue_type,
                    Application.status == ApplicationStatusEnum.PROBLEM
                )
            ).scalar()
            
            result.append({
                "queue_type": queue_type,
                "total": total,
                "queued": queued,
                "in_progress": in_progress,
                "accepted": accepted,
                "rejected": rejected,
                "problem": problem
            })
        
        return result

    def get_queue_applications(self, queue_type: str) -> List[Dict[str, Any]]:
        """Получить все заявления из конкретной очереди"""
        applications = self.db.query(Application).filter(
            Application.queue_type == queue_type
        ).order_by(Application.submitted_at.desc()).all()
        
        result = []
        for app in applications:
            processed_by = None
            if app.processed_by:
                employee = self.db.query(Employee).filter(Employee.id == app.processed_by).first()
                processed_by = employee.fio if employee else None
            
            result.append({
                "id": app.id,
                "fio": app.fio,
                "queue_type": app.queue_type,
                "status": app.status.value,
                "submitted_at": app.submitted_at,
                "processed_at": app.processed_at,
                "processed_by_fio": processed_by,
                "is_priority": app.is_priority if hasattr(app, 'is_priority') else False
            })
        
        return result 
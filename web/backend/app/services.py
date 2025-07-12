from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
import pytz

from db.models import Employee, Application, WorkDay, WorkDayStatusEnum, ApplicationStatusEnum

def get_moscow_date():
    """Получить текущую дату в московском времени"""
    # Используем локальное время контейнера, которое настроено на Москву
    return datetime.now().date()

def get_moscow_now():
    """Получить текущее время в московском времени"""
    # Используем локальное время контейнера, которое настроено на Москву
    return datetime.now()

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        self.today = datetime.now(self.moscow_tz).date()

    def get_employees_status(self) -> List[dict]:
        """Получить статус всех сотрудников"""
        employees = self.db.query(Employee).all()
        result = []
        
        print(f"DEBUG: Сегодняшняя дата: {self.today}")
        
        for employee in employees:
            # Найти текущий рабочий день
            work_day = self.db.query(WorkDay).filter(
                and_(
                    WorkDay.employee_id == employee.id,
                    WorkDay.date == self.today
                )
            ).first()
            
            print(f"DEBUG: Сотрудник {employee.fio} (ID: {employee.id})")
            print(f"DEBUG: Рабочий день найден: {work_day is not None}")
            
            if work_day:
                print(f"DEBUG: start_time: {work_day.start_time}")
                print(f"DEBUG: end_time: {work_day.end_time}")
                print(f"DEBUG: breaks: {work_day.breaks}")
            
            status = "Не работает"
            current_task = None
            work_duration = None
            start_time = None
            last_processed = None
            
            if work_day and work_day.start_time:
                if not work_day.end_time:
                    # Проверяем, есть ли активный перерыв
                    active_break = None
                    if work_day.breaks:
                        active_break = next((b for b in work_day.breaks if b.start_time and not b.end_time), None)
                    
                    if active_break:
                        status = "На перерыве"
                        # Время перерыва
                        break_time = datetime.now(self.moscow_tz) - active_break.start_time
                        break_hours = int(break_time.total_seconds() // 3600)
                        break_minutes = int((break_time.total_seconds() % 3600) // 60)
                        work_duration = f"Перерыв: {break_hours:02d}:{break_minutes:02d}"
                    else:
                        status = "На рабочем месте"
                        # Вычислить время работы
                        work_time = datetime.now(self.moscow_tz) - work_day.start_time
                        hours = int(work_time.total_seconds() // 3600)
                        minutes = int((work_time.total_seconds() % 3600) // 60)
                        work_duration = f"{hours:02d}:{minutes:02d}"
                    
                elif work_day.end_time:
                    status = "Рабочий день завершен"
                    # Время работы за день
                    work_time = work_day.end_time - work_day.start_time
                    hours = int(work_time.total_seconds() // 3600)
                    minutes = int((work_time.total_seconds() % 3600) // 60)
                    work_duration = f"{hours:02d}:{minutes:02d}"
                    
                start_time = work_day.start_time
                
                # Получить текущую задачу (последнее заявление в обработке)
                current_application = self.db.query(Application).filter(
                    and_(
                        Application.processed_by_id == employee.id,
                        Application.status == ApplicationStatusEnum.IN_PROGRESS
                    )
                ).order_by(Application.processed_at.desc()).first()
                
                if current_application:
                    current_task = f"Заявление #{current_application.id} ({current_application.fio})"
                
                # Получить последнее обработанное заявление
                last_processed_app = self.db.query(Application).filter(
                    and_(
                        Application.processed_by_id == employee.id,
                        Application.status.in_([ApplicationStatusEnum.ACCEPTED, ApplicationStatusEnum.REJECTED, ApplicationStatusEnum.PROBLEM])
                    )
                ).order_by(Application.processed_at.desc()).first()
                
                if last_processed_app:
                    last_processed = f"#{last_processed_app.id} ({last_processed_app.fio}) - {last_processed_app.status.value}"
            
            print(f"DEBUG: Итоговый статус: {status}")
            
            result.append({
                "id": employee.id,
                "fio": employee.fio,
                "status": status,
                "current_task": current_task,
                "work_duration": work_duration,
                "start_time": start_time,
                "last_processed": last_processed,
                "is_admin": employee.is_admin
            })
        
        return result

    def get_recent_applications(self) -> List[dict]:
        """Получить последние 10 обработанных заявлений"""
        applications = self.db.query(Application).filter(
            Application.status.in_([ApplicationStatusEnum.ACCEPTED, ApplicationStatusEnum.REJECTED, ApplicationStatusEnum.PROBLEM])
        ).order_by(Application.processed_at.desc()).limit(10).all()
        
        result = []
        for app in applications:
            processed_by = None
            if app.processed_by_id:
                employee = self.db.query(Employee).filter(Employee.id == app.processed_by_id).first()
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

    def get_queue_statistics(self) -> List[dict]:
        """Получить статистику по всем очередям"""
        queue_types = ['lk', 'lk_problem', 'epgu', 'epgu_mail', 'epgu_problem']
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
            
            # Названия очередей для отображения
            queue_names = {
                'lk': 'Личный кабинет',
                'lk_problem': 'ЛК - Проблемы',
                'epgu': 'ЕПГУ',
                'epgu_mail': 'ЕПГУ - Почта',
                'epgu_problem': 'ЕПГУ - Проблемы'
            }
            
            result.append({
                "queue_type": queue_type,
                "queue_name": queue_names.get(queue_type, queue_type),
                "total": total,
                "queued": queued,
                "in_progress": in_progress,
                "accepted": accepted,
                "rejected": rejected,
                "problem": problem
            })
        
        return result

    def get_queue_applications(self, queue_type: str) -> List[dict]:
        """Получить все заявления из конкретной очереди"""
        applications = self.db.query(Application).filter(
            Application.queue_type == queue_type
        ).order_by(Application.submitted_at.desc()).all()
        
        result = []
        for app in applications:
            processed_by = None
            if app.processed_by_id:
                employee = self.db.query(Employee).filter(Employee.id == app.processed_by_id).first()
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

    def get_lk_chart_data(self) -> dict:
        """Получить данные для круговой диаграммы ЛК"""
        # ЛК - в очереди
        lk_queued = self.db.query(func.count(Application.id)).filter(
            and_(
                Application.queue_type.in_(['lk', 'lk_problem']),
                Application.status == ApplicationStatusEnum.QUEUED
            )
        ).scalar()
        
        # ЛК - принято
        lk_accepted = self.db.query(func.count(Application.id)).filter(
            and_(
                Application.queue_type.in_(['lk', 'lk_problem']),
                Application.status == ApplicationStatusEnum.ACCEPTED
            )
        ).scalar()
        
        return {
            "labels": ["В очереди", "Принято"],
            "data": [lk_queued, lk_accepted],
            "colors": ["#ffc107", "#28a745"]
        }

    def get_epgu_chart_data(self) -> dict:
        """Получить данные для круговой диаграммы ЕПГУ"""
        # ЕПГУ - в очереди
        epgu_queued = self.db.query(func.count(Application.id)).filter(
            and_(
                Application.queue_type.in_(['epgu', 'epgu_mail', 'epgu_problem']),
                Application.status == ApplicationStatusEnum.QUEUED
            )
        ).scalar()
        
        # ЕПГУ почта - всего
        epgu_mail_total = self.db.query(func.count(Application.id)).filter(
            Application.queue_type == 'epgu_mail'
        ).scalar()
        
        # Сумма принято ЕПГУ и ЕПГУ почта
        epgu_accepted = self.db.query(func.count(Application.id)).filter(
            and_(
                Application.queue_type.in_(['epgu', 'epgu_mail', 'epgu_problem']),
                Application.status == ApplicationStatusEnum.ACCEPTED
            )
        ).scalar()
        
        return {
            "labels": ["ЕПГУ в очереди", "ЕПГУ почта всего", "Сумма принято ЕПГУ"],
            "data": [epgu_queued, epgu_mail_total, epgu_accepted],
            "colors": ["#ffc107", "#6f42c1", "#28a745"]
        } 
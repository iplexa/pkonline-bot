from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
import pytz
from db.models import Employee, Application, WorkDay, ApplicationStatusEnum, WorkDayStatusEnum
from typing import List, Dict, Any
import time

def get_moscow_date():
    """Получить текущую дату в московском времени"""
    # Используем московское время
    moscow_tz = pytz.timezone('Europe/Moscow')
    return datetime.now(moscow_tz).date()

def get_moscow_now():
    """Получить текущее время в московском времени"""
    # Используем московское время
    moscow_tz = pytz.timezone('Europe/Moscow')
    return datetime.now(moscow_tz).replace(tzinfo=None)

class DashboardService:
    def __init__(self, db: Session):
        self.db = db
        self.moscow_tz = pytz.timezone('Europe/Moscow')
        self.today = datetime.now(self.moscow_tz).date()
        # Кэш для данных сотрудников (5 секунд)
        self._employees_cache = None
        self._employees_cache_time = 0
        self._cache_duration = 5

    def _is_cache_valid(self):
        """Проверить, действителен ли кэш"""
        return (self._employees_cache is not None and 
                time.time() - self._employees_cache_time < self._cache_duration)

    def clear_cache(self):
        """Очистить кэш"""
        self._employees_cache = None
        self._employees_cache_time = 0

    def get_employees_status(self) -> List[Dict[str, Any]]:
        """Получить статус всех сотрудников"""
        # Проверяем кэш
        if self._is_cache_valid():
            return self._employees_cache
        
        employees = self.db.query(Employee).all()
        result = []
        
        print(f"DEBUG: Total employees found: {len(employees)}")
        
        for emp in employees:
            # Получаем текущий рабочий день в московском времени
            today = get_moscow_date()
            today_start = datetime.combine(today, datetime.min.time())
            today_end = datetime.combine(today, datetime.max.time())
            
            # Также проверяем вчерашний день, если сегодня нет активного рабочего дня
            yesterday = today - timedelta(days=1)
            yesterday_start = datetime.combine(yesterday, datetime.min.time())
            yesterday_end = datetime.combine(yesterday, datetime.max.time())
            
            # Проверим все рабочие дни этого сотрудника для отладки
            all_work_days = self.db.query(WorkDay).filter(WorkDay.employee_id == emp.id).all()
            print(f"DEBUG: Employee {emp.fio} (ID: {emp.id}) - All work days: {len(all_work_days)}")
            for wd in all_work_days:
                print(f"  - Work day: ID={wd.id}, date={wd.date}, start_time={wd.start_time}, end_time={wd.end_time}, status={wd.status}")
            
            # Сначала ищем активный рабочий день за сегодня
            work_day = self.db.query(WorkDay).filter(
                and_(
                    WorkDay.employee_id == emp.id,
                    WorkDay.date >= today_start,
                    WorkDay.date <= today_end,
                    WorkDay.end_time.is_(None)  # Только активные дни
                )
            ).first()
            
            # Если нет активного дня за сегодня, ищем завершенный день за сегодня
            if not work_day:
                work_day = self.db.query(WorkDay).filter(
                    and_(
                        WorkDay.employee_id == emp.id,
                        WorkDay.date >= today_start,
                        WorkDay.date <= today_end,
                        WorkDay.end_time.is_not(None)  # Только завершенные дни
                    )
                ).first()
            
            # Если нет дня за сегодня, ищем активный день за вчера
            if not work_day:
                work_day = self.db.query(WorkDay).filter(
                    and_(
                        WorkDay.employee_id == emp.id,
                        WorkDay.date >= yesterday_start,
                        WorkDay.date <= yesterday_end,
                        WorkDay.end_time.is_(None)  # Только активные дни
                    )
                ).first()
            
            # Отладочная информация
            print(f"DEBUG: Employee {emp.fio} (ID: {emp.id})")
            if work_day:
                print(f"  - Work day found: ID={work_day.id}, date={work_day.date}, start_time={work_day.start_time}, end_time={work_day.end_time}, status={work_day.status}")
            else:
                print(f"  - No work day found")
            
            # Дополнительная отладка для понимания логики
            print(f"  - Today: {today}")
            print(f"  - Yesterday: {yesterday}")
            print(f"  - Today range: {today_start} - {today_end}")
            
            status = "Не работает"
            current_task = None
            start_time = None
            work_duration = None
            
            if work_day:  # Если есть рабочий день
                print(f"  - Processing work day: end_time={work_day.end_time}, status={work_day.status}")
                if work_day.start_time:  # И он начат
                    if work_day.end_time:  # Если рабочий день завершен
                        print(f"  - Work day is finished (has end_time)")
                        status = "Рабочий день завершен"
                        start_time = work_day.start_time
                        if work_day.total_work_time:
                            hours = work_day.total_work_time // 3600
                            minutes = (work_day.total_work_time % 3600) // 60
                            work_duration = f"{hours:02d}:{minutes:02d}"
                    elif work_day.status == WorkDayStatusEnum.ACTIVE:
                        print(f"  - Work day is active")
                        status = "На рабочем месте"
                        start_time = work_day.start_time
                        if start_time:
                            duration = get_moscow_now() - start_time
                            work_duration = f"{duration.seconds // 3600:02d}:{(duration.seconds % 3600) // 60:02d}"
                    elif work_day.status == WorkDayStatusEnum.PAUSED:
                        print(f"  - Work day is paused")
                        status = "На перерыве"
                        start_time = work_day.start_time
                        if start_time:
                            duration = get_moscow_now() - start_time
                            work_duration = f"{duration.seconds // 3600:02d}:{(duration.seconds % 3600) // 60:02d}"
                    elif work_day.status == WorkDayStatusEnum.FINISHED:
                        print(f"  - Work day is finished (status)")
                        status = "Рабочий день завершен"
                        start_time = work_day.start_time
                        if work_day.total_work_time:
                            hours = work_day.total_work_time // 3600
                            minutes = (work_day.total_work_time % 3600) // 60
                            work_duration = f"{hours:02d}:{minutes:02d}"
                else:
                    print(f"  - Work day has no start_time")
            else:
                print(f"  - No work day found for employee")
                
                # Проверяем, есть ли активная задача
                current_app = self.db.query(Application).filter(
                    and_(
                        Application.processed_by_id == emp.id,
                        Application.status == ApplicationStatusEnum.IN_PROGRESS
                    )
                ).first()
                if current_app:
                    current_task = f"Заявление {current_app.id} ({current_app.fio}) - {current_app.queue_type}"
            
            # Получить текущую задачу (если сотрудник работает)
            if not current_task and work_day and work_day.start_time and not work_day.end_time:
                current_app = self.db.query(Application).filter(
                    and_(
                        Application.processed_by_id == emp.id,
                        Application.status == ApplicationStatusEnum.IN_PROGRESS
                    )
                ).first()
                if current_app:
                    current_task = f"Заявление {current_app.id} ({current_app.fio}) - {current_app.queue_type}"
            
            result.append({
                "id": emp.id,
                "fio": emp.fio or emp.tg_id,
                "is_admin": emp.is_admin,
                "status": status,
                "current_task": current_task,
                "start_time": start_time,
                "work_duration": work_duration
            })
        
        # Сохраняем в кэш
        self._employees_cache = result
        self._employees_cache_time = time.time()
        
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
                processed_by = app.processed_by.fio if app.processed_by else None
            
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
                processed_by = app.processed_by.fio if app.processed_by else None
            
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

    def get_lk_chart_data(self) -> Dict[str, Any]:
        """Получить данные для круговой диаграммы ЛК"""
        # Получаем статистику по ЛК
        total = self.db.query(func.count(Application.id)).filter(
            Application.queue_type == 'lk'
        ).scalar()
        
        queued = self.db.query(func.count(Application.id)).filter(
            and_(
                Application.queue_type == 'lk',
                Application.status == ApplicationStatusEnum.QUEUED
            )
        ).scalar()
        
        in_progress = self.db.query(func.count(Application.id)).filter(
            and_(
                Application.queue_type == 'lk',
                Application.status == ApplicationStatusEnum.IN_PROGRESS
            )
        ).scalar()
        
        completed = self.db.query(func.count(Application.id)).filter(
            and_(
                Application.queue_type == 'lk',
                Application.status.in_([ApplicationStatusEnum.ACCEPTED, ApplicationStatusEnum.REJECTED])
            )
        ).scalar()
        
        return {
            "labels": ["В очереди", "В обработке", "Завершено"],
            "data": [queued, in_progress, completed],
            "total": total
        }

    def get_epgu_chart_data(self) -> Dict[str, Any]:
        """Получить данные для круговой диаграммы ЕПГУ"""
        # Получаем статистику по ЕПГУ
        total = self.db.query(func.count(Application.id)).filter(
            Application.queue_type == 'epgu'
        ).scalar()
        
        queued = self.db.query(func.count(Application.id)).filter(
            and_(
                Application.queue_type == 'epgu',
                Application.status == ApplicationStatusEnum.QUEUED
            )
        ).scalar()
        
        in_progress = self.db.query(func.count(Application.id)).filter(
            and_(
                Application.queue_type == 'epgu',
                Application.status == ApplicationStatusEnum.IN_PROGRESS
            )
        ).scalar()
        
        completed = self.db.query(func.count(Application.id)).filter(
            and_(
                Application.queue_type == 'epgu',
                Application.status.in_([ApplicationStatusEnum.ACCEPTED, ApplicationStatusEnum.REJECTED])
            )
        ).scalar()
        
        return {
            "labels": ["В очереди", "В обработке", "Завершено"],
            "data": [queued, in_progress, completed],
            "total": total
        }

    def get_full_report_by_date(self, report_date: datetime.date = None) -> list:
        """Получить полный отчет по всем сотрудникам за день (рабочее время, перерывы, заявления)"""
        if not report_date:
            report_date = get_moscow_date()
        today_start = datetime.combine(report_date, datetime.min.time())
        today_end = datetime.combine(report_date, datetime.max.time())
        work_days = self.db.query(WorkDay).filter(
            WorkDay.date >= today_start,
            WorkDay.date <= today_end
        ).all()
        reports = []
        for work_day in work_days:
            # Пересчитываем время для активных дней
            total_work_time = work_day.total_work_time
            total_break_time = work_day.total_break_time
            if work_day.status in [WorkDayStatusEnum.ACTIVE, WorkDayStatusEnum.PAUSED] and work_day.start_time and not work_day.end_time:
                current_time = get_moscow_now()
                # Проверяем активный перерыв
                active_break = next((b for b in work_day.breaks if b.end_time is None), None)
                if active_break and active_break.start_time:
                    total_break_time += int((current_time - active_break.start_time).total_seconds())
                elapsed_seconds = int((current_time - work_day.start_time).total_seconds())
                total_work_time = elapsed_seconds - total_break_time
            report = {
                "employee_fio": work_day.employee.fio if work_day.employee else None,
                "employee_tg_id": work_day.employee.tg_id if work_day.employee else None,
                "date": work_day.date.date() if work_day.date else None,
                "start_time": work_day.start_time,
                "end_time": work_day.end_time,
                "total_work_time": total_work_time,
                "total_break_time": total_break_time,
                "applications_processed": work_day.applications_processed,
                "status": work_day.status.value,
                "breaks": [
                    {
                        "start_time": b.start_time,
                        "end_time": b.end_time,
                        "duration": b.duration
                    } for b in getattr(work_day, 'breaks', [])
                ]
            }
            reports.append(report)
        return reports 

    def accept_application(self, app, employee_id):
        app.status = ApplicationStatusEnum.ACCEPTED
        app.processed_by_id = employee_id
        app.processed_at = get_moscow_now()
        # Для ЕПГУ: epgu_action, epgu_processor_id
        if hasattr(app, 'epgu_action'):
            app.epgu_action = 'ACCEPTED'
            app.epgu_processor_id = employee_id
        app.scans_confirmed = True
        app.signature_confirmed = True

    def reject_application(self, app, employee_id, reason):
        app.status = ApplicationStatusEnum.REJECTED
        app.status_reason = reason
        app.processed_by_id = employee_id
        app.processed_at = get_moscow_now()
        if hasattr(app, 'epgu_action'):
            app.epgu_action = 'REJECTED'
            app.epgu_processor_id = employee_id

    def move_to_mail_queue(self, app, employee_id):
        app.queue_type = 'epgu_mail'
        app.status = ApplicationStatusEnum.QUEUED
        app.processed_by_id = employee_id
        app.processed_at = get_moscow_now()
        app.epgu_action = 'HAS_SCANS'
        app.epgu_processor_id = employee_id
        app.needs_scans = False
        app.needs_signature = True
        app.scans_confirmed = True
        app.signature_confirmed = False
        app.taken_at = None

    def move_to_problem_queue(self, app, employee_id, reason):
        app.status = ApplicationStatusEnum.PROBLEM
        app.status_reason = reason
        app.queue_type = app.queue_type + '_problem' if not app.queue_type.endswith('_problem') else app.queue_type
        app.processed_by_id = employee_id
        app.processed_at = get_moscow_now()

    def confirm_scans(self, app, employee_id):
        app.scans_confirmed = True
        # Если нужна подпись и не подтверждена — не принимаем
        if getattr(app, 'needs_signature', False) and not getattr(app, 'signature_confirmed', False):
            return
        # Если всё подтверждено — принять
        self.accept_application(app, employee_id)

    def confirm_signature(self, app, employee_id):
        app.signature_confirmed = True
        # Если нужны сканы и не подтверждены — не принимаем
        if getattr(app, 'needs_scans', False) and not getattr(app, 'scans_confirmed', False):
            return
        # Если всё подтверждено — принять
        self.accept_application(app, employee_id) 

    def assign_next_application(self, queue_type, employee_id):
        # Аналогично get_next_application из crud.py
        app = self.db.query(Application).filter(
            Application.queue_type == queue_type,
            Application.status == ApplicationStatusEnum.QUEUED
        ).order_by(
            Application.is_priority.desc(),
            Application.submitted_at.asc()
        ).first()
        if app:
            app.status = ApplicationStatusEnum.IN_PROGRESS
            app.processed_by_id = employee_id
            app.taken_at = get_moscow_now()
            self.db.commit()
        return app

    def search_applications(self, queue_type, fio_or_email):
        # Для epgu_mail поддерживаем поиск по email
        q = self.db.query(Application).filter(Application.queue_type == queue_type)
        if queue_type == 'epgu_mail' and ('@' in fio_or_email and '.' in fio_or_email):
            q = q.filter(Application.email.ilike(f"%{fio_or_email}%"))
        else:
            q = q.filter(Application.fio.ilike(f"%{fio_or_email}%"))
        return [
            {
                "id": app.id,
                "fio": app.fio,
                "queue_type": app.queue_type,
                "status": app.status.value,
                "submitted_at": app.submitted_at,
                "processed_at": app.processed_at,
                "processed_by_fio": app.processed_by.fio if app.processed_by else None,
                "is_priority": app.is_priority if hasattr(app, 'is_priority') else False
            }
            for app in q.order_by(Application.submitted_at.desc()).all()
        ] 
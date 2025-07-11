from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
import pytz

from .database import get_session
from .models import EmployeeStatus, ApplicationInfo, QueueStatistics
from db.models import Employee, Application, WorkDay, WorkDayStatusEnum, ApplicationStatusEnum

def get_moscow_date():
    """Получить текущую дату в московском времени"""
    # Используем локальное время контейнера, которое настроено на Москву
    return datetime.now().date()

def get_moscow_now():
    """Получить текущее время в московском времени"""
    # Используем локальное время контейнера, которое настроено на Москву
    return datetime.now()

class EmployeeService:
    """Сервис для работы с сотрудниками"""
    
    @staticmethod
    async def get_employees_status() -> List[EmployeeStatus]:
        """Получение статуса всех сотрудников"""
        async for session in get_session():
            # Получаем всех сотрудников
            stmt = select(Employee).options(selectinload(Employee.work_days))
            result = await session.execute(stmt)
            employees = result.scalars().all()
            
            employee_statuses = []
            for emp in employees:
                # Получаем текущий рабочий день в московском времени
                today = get_moscow_date()
                today_start = datetime.combine(today, datetime.min.time())
                today_end = datetime.combine(today, datetime.max.time())
                
                # Также проверяем вчерашний день, если сегодня нет активного рабочего дня
                yesterday = today - timedelta(days=1)
                yesterday_start = datetime.combine(yesterday, datetime.min.time())
                yesterday_end = datetime.combine(yesterday, datetime.max.time())
                
                # Сначала ищем активный рабочий день за сегодня
                stmt = select(WorkDay).where(
                    and_(
                        WorkDay.employee_id == emp.id,
                        WorkDay.date >= today_start,
                        WorkDay.date <= today_end,
                        WorkDay.end_time.is_(None)  # Только активные дни
                    )
                ).options(selectinload(WorkDay.breaks))
                result = await session.execute(stmt)
                work_day = result.scalars().first()
                
                # Если нет активного дня за сегодня, ищем завершенный день за сегодня
                if not work_day:
                    stmt = select(WorkDay).where(
                        and_(
                            WorkDay.employee_id == emp.id,
                            WorkDay.date >= today_start,
                            WorkDay.date <= today_end,
                            WorkDay.end_time.is_not(None)  # Только завершенные дни
                        )
                    ).options(selectinload(WorkDay.breaks))
                    result = await session.execute(stmt)
                    work_day = result.scalars().first()
                
                # Если нет дня за сегодня, ищем активный день за вчера
                if not work_day:
                    stmt = select(WorkDay).where(
                        and_(
                            WorkDay.employee_id == emp.id,
                            WorkDay.date >= yesterday_start,
                            WorkDay.date <= yesterday_end,
                            WorkDay.end_time.is_(None)  # Только активные дни
                        )
                    ).options(selectinload(WorkDay.breaks))
                    result = await session.execute(stmt)
                    work_day = result.scalars().first()
                
                # Отладочная информация
                print(f"DEBUG: Employee {emp.fio} (ID: {emp.id})")
                if work_day:
                    print(f"  - Work day found: ID={work_day.id}, date={work_day.date}, start_time={work_day.start_time}, end_time={work_day.end_time}, status={work_day.status}")
                else:
                    print(f"  - No work day found")
                
                # Дополнительная отладка для понимания логики
                print(f"  - Today: {today}")
                print(f"  - Yesterday: {yesterday}")
                
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
                    stmt = select(Application).where(
                        and_(
                            Application.processed_by_id == emp.id,
                            Application.status == ApplicationStatusEnum.IN_PROGRESS
                        )
                    )
                    result = await session.execute(stmt)
                    current_app = result.scalars().first()
                    if current_app:
                        current_task = f"Заявление {current_app.id} ({current_app.fio}) - {current_app.queue_type}"
                
                employee_statuses.append(EmployeeStatus(
                    id=emp.id,
                    fio=emp.fio or emp.tg_id,
                    is_admin=emp.is_admin,
                    status=status,
                    current_task=current_task,
                    start_time=start_time,
                    work_duration=work_duration
                ))
            
            return employee_statuses

class ApplicationService:
    """Сервис для работы с заявлениями"""
    
    @staticmethod
    async def get_recent_applications(limit: int = 10) -> List[ApplicationInfo]:
        """Получение последних обработанных заявлений"""
        async for session in get_session():
            # Получаем последние обработанные заявления
            stmt = select(Application).where(
                Application.status.in_([
                    ApplicationStatusEnum.ACCEPTED,
                    ApplicationStatusEnum.REJECTED,
                    ApplicationStatusEnum.PROBLEM
                ])
            ).options(selectinload(Application.processed_by)).order_by(
                Application.processed_at.desc()
            ).limit(limit)
            
            result = await session.execute(stmt)
            applications = result.scalars().all()
            
            return [
                ApplicationInfo(
                    id=app.id,
                    fio=app.fio,
                    queue_type=app.queue_type,
                    status=app.status.value,
                    processed_by_fio=app.processed_by.fio if app.processed_by else None,
                    submitted_at=app.submitted_at,
                    processed_at=app.processed_at
                )
                for app in applications
            ]

class QueueService:
    """Сервис для работы с очередями"""
    
    @staticmethod
    async def get_queue_statistics() -> List[QueueStatistics]:
        """Получение статистики по очередям"""
        async for session in get_session():
            # Получаем статистику по очередям
            queue_types = ['lk', 'epgu', 'epgu_mail', 'epgu_problem']
            statistics = []
            
            for queue_type in queue_types:
                stmt = select(Application).where(Application.queue_type == queue_type)
                result = await session.execute(stmt)
                apps = result.scalars().all()
                
                total = len(apps)
                queued = len([app for app in apps if app.status == ApplicationStatusEnum.QUEUED])
                in_progress = len([app for app in apps if app.status == ApplicationStatusEnum.IN_PROGRESS])
                accepted = len([app for app in apps if app.status == ApplicationStatusEnum.ACCEPTED])
                rejected = len([app for app in apps if app.status == ApplicationStatusEnum.REJECTED])
                problem = len([app for app in apps if app.status == ApplicationStatusEnum.PROBLEM])
                
                statistics.append(QueueStatistics(
                    queue_type=queue_type,
                    total=total,
                    queued=queued,
                    in_progress=in_progress,
                    accepted=accepted,
                    rejected=rejected,
                    problem=problem
                ))
            
            return statistics 
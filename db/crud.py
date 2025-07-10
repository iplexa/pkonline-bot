from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from .models import Application, ApplicationStatusEnum, Employee, Group, WorkDay, WorkBreak, WorkDayStatusEnum
from datetime import datetime, timedelta, date
from .session import get_session
import aiohttp
import tempfile
from utils.excel import parse_lk_applications_from_excel, parse_epgu_applications_from_excel
import pytz
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Московский часовой пояс
MSK_TZ = pytz.timezone('Europe/Moscow')

def get_moscow_now():
    """Получить текущее время в московском часовом поясе"""
    return datetime.now(MSK_TZ).replace(tzinfo=None)

def get_moscow_date():
    """Получить текущую дату в московском часовом поясе"""
    return get_moscow_now().date()

async def cleanup_expired_applications():
    """Возвращает в очередь заявления, которые в обработке больше часа"""
    async for session in get_session():
        one_hour_ago = datetime.now() - timedelta(hours=1)
        # Сначала получаем заявления, которые будут возвращены
        expired_stmt = select(Application).where(
            Application.status == ApplicationStatusEnum.IN_PROGRESS,
            Application.taken_at < one_hour_ago
        ).options(selectinload(Application.processed_by))
        expired_result = await session.execute(expired_stmt)
        expired_apps = expired_result.scalars().all()
        
        # Возвращаем заявления в очередь
        stmt = update(Application).where(
            Application.status == ApplicationStatusEnum.IN_PROGRESS,
            Application.taken_at < one_hour_ago
        ).values(
            status=ApplicationStatusEnum.QUEUED,
            processed_by_id=None,
            taken_at=None
        )
        await session.execute(stmt)
        await session.commit()
        
        # Возвращаем информацию о возвращённых заявлениях
        return [
            {
                "app_id": app.id,
                "fio": app.fio,
                "queue_type": app.queue_type,
                "employee_tg_id": app.processed_by.tg_id if app.processed_by else None,
                "employee_fio": app.processed_by.fio if app.processed_by else None
            }
            for app in expired_apps
        ]

async def get_next_application(queue_type: str, employee_id: int = None, bot=None):
    async for session in get_session():
        # Сначала очищаем просроченные заявления
        expired_apps = await cleanup_expired_applications()
        
        # Отправляем уведомления о возвращённых заявлениях
        if expired_apps and bot:
            from config import ADMIN_CHAT_ID
            for app_info in expired_apps:
                # Уведомление в админ-чат
                admin_msg = f"⚠️ Заявление {app_info['app_id']} ({app_info['fio']}) возвращено в очередь {app_info['queue_type']} по истечении времени"
                if app_info['employee_fio']:
                    admin_msg += f"\nСотрудник: {app_info['employee_fio']}"
                await bot.send_message(ADMIN_CHAT_ID, admin_msg)
                
                # Уведомление сотруднику
                if app_info['employee_tg_id']:
                    try:
                        employee_msg = f"⚠️ Заявление {app_info['app_id']} ({app_info['fio']}) возвращено в очередь по истечении времени обработки (1 час)"
                        await bot.send_message(app_info['employee_tg_id'], employee_msg)
                    except Exception:
                        pass  # Игнорируем ошибки отправки сотруднику
        
        stmt = select(Application).where(
            Application.queue_type == queue_type,
            Application.status == ApplicationStatusEnum.QUEUED
        ).order_by(
            Application.is_priority.desc(),
            Application.submitted_at.asc()
        )
        result = await session.execute(stmt)
        app = result.scalars().first()
        if app and employee_id:
            # Сразу блокируем заявление за сотрудником
            app.status = ApplicationStatusEnum.IN_PROGRESS
            app.processed_by_id = employee_id
            app.taken_at = datetime.now()
            await session.commit()
        return app

async def update_application_status(app_id: int, status: ApplicationStatusEnum, reason: str = None, employee_id: int = None):
    async for session in get_session():
        stmt = update(Application).where(Application.id == app_id).values(
            status=status,
            status_reason=reason,
            processed_by_id=employee_id
        )
        await session.execute(stmt)
        await session.commit()

async def add_application(fio: str, submitted_at: datetime, queue_type: str, is_priority: bool = False):
    async for session in get_session():
        app = Application(fio=fio, submitted_at=submitted_at, queue_type=queue_type, is_priority=is_priority)
        session.add(app)
        await session.commit()
        return app

async def set_priority(fio: str, queue_type: str):
    async for session in get_session():
        stmt = update(Application).where(
            Application.fio == fio,
            Application.queue_type == queue_type
        ).values(is_priority=True)
        await session.execute(stmt)
        await session.commit()

async def find_application_by_fio(fio: str, queue_type: str):
    async for session in get_session():
        stmt = select(Application).where(
            Application.fio == fio,
            Application.queue_type == queue_type
        )
        result = await session.execute(stmt)
        return result.scalars().all()

async def get_employee_by_tg_id(tg_id: str):
    async for session in get_session():
        stmt = select(Employee).where(Employee.tg_id == str(tg_id)).options(selectinload(Employee.groups))
        result = await session.execute(stmt)
        return result.scalars().first()

async def employee_has_group(tg_id: str, group_name: str):
    async for session in get_session():
        stmt = select(Employee).where(Employee.tg_id == tg_id).options(selectinload(Employee.groups))
        result = await session.execute(stmt)
        emp = result.scalars().first()
        if not emp or not emp.groups:
            return False
        return any(g.name == group_name for g in emp.groups)

async def is_admin(tg_id: str):
    emp = await get_employee_by_tg_id(tg_id)
    return emp.is_admin if emp else False

async def has_access(tg_id: str, group_name: str):
    """
    Проверяет, есть ли у пользователя доступ к группе.
    Админы имеют доступ ко всем группам.
    """
    emp = await get_employee_by_tg_id(tg_id)
    if not emp:
        return False
    
    # Админы имеют доступ ко всем группам
    if emp.is_admin:
        return True
    
    # Обычные пользователи проверяются по группам
    if not emp.groups:
        return False
    return any(g.name == group_name for g in emp.groups)

async def add_employee(tg_id: str, fio: str, is_admin_flag: bool = False):
    async for session in get_session():
        emp = Employee(tg_id=tg_id, fio=fio, is_admin=is_admin_flag)
        session.add(emp)
        await session.commit()
        return emp

async def remove_employee(tg_id: str):
    async for session in get_session():
        emp = await get_employee_by_tg_id(tg_id)
        if emp:
            await session.delete(emp)
            await session.commit()

async def add_group_to_employee(tg_id: str, group_name: str):
    async for session in get_session():
        emp_result = await session.execute(select(Employee).where(Employee.tg_id == tg_id).options(selectinload(Employee.groups)))
        emp = emp_result.scalars().first()
        if not emp:
            return False
        group_result = await session.execute(select(Group).where(Group.name == group_name))
        group = group_result.scalars().first()
        if not group:
            group = Group(name=group_name)
            session.add(group)
            await session.commit()
        if group not in emp.groups:
            emp.groups.append(group)
            session.add(emp)
            await session.commit()
        return True

async def remove_group_from_employee(tg_id: str, group_name: str):
    async for session in get_session():
        emp = await get_employee_by_tg_id(tg_id)
        if not emp:
            return False
        group = await session.execute(select(Group).where(Group.name == group_name))
        group = group.scalars().first()
        if group and group in emp.groups:
            emp.groups.remove(group)
            await session.commit()
        return True

async def list_employees_with_groups():
    async for session in get_session():
        stmt = select(Employee).options(selectinload(Employee.groups))
        result = await session.execute(stmt)
        employees = result.scalars().all()
        return [
            {
                "tg_id": e.tg_id,
                "fio": e.fio,
                "is_admin": e.is_admin,
                "groups": [g.name for g in e.groups]
            }
            for e in employees
        ]

async def get_applications_by_queue_type(queue_type: str):
    async for session in get_session():
        stmt = select(Application).where(Application.queue_type == queue_type).order_by(Application.submitted_at.asc())
        result = await session.execute(stmt)
        return result.scalars().all()

async def clear_queue_by_type(queue_type: str):
    async for session in get_session():
        await session.execute(
            Application.__table__.delete().where(Application.queue_type == queue_type)
        )
        await session.commit()

async def import_applications_from_excel(file_path, queue_type: str):
    import os
    from utils.excel import parse_lk_applications_from_excel, parse_epgu_applications_from_excel
    if queue_type == "lk":
        applications = parse_lk_applications_from_excel(file_path)
    elif queue_type == "epgu":
        applications = parse_epgu_applications_from_excel(file_path)
    else:
        applications = []
    logger = logging.getLogger("epgu_import")
    logger.info(f"Импорт заявлений: очередь={queue_type}, всего строк в файле: {len(applications)}")
    added = 0
    skipped = 0
    skipped_details = []
    async for session in get_session():
        if queue_type == "epgu":
            # Получить все (fio, submitted_at) уже в базе для epgu, независимо от статуса
            existing = await session.execute(
                select(Application.fio, Application.submitted_at).where(
                    Application.queue_type == "epgu"
                )
            )
            existing_keys = set((fio, submitted_at) for fio, submitted_at in existing.fetchall())
            for app in applications:
                key = (app["fio"], app["submitted_at"])
                if key in existing_keys:
                    skipped += 1
                    skipped_details.append(f"{app['fio']} | {app['submitted_at']} (уже есть)")
                    continue
                new_app = Application(
                    fio=app["fio"],
                    submitted_at=app["submitted_at"],
                    queue_type="epgu",
                    status=ApplicationStatusEnum.QUEUED
                )
                session.add(new_app)
                added += 1
            await session.commit()
            logger.info(f"Добавлено заявлений: {added}, пропущено: {skipped}")
            if skipped_details:
                logger.info("Пропущенные строки (уже есть в базе):\n" + "\n".join(skipped_details))
        else:
            # Для ЛК проверяем только заявления в статусе QUEUED
            existing = await session.execute(
                select(Application.fio).where(
                    Application.queue_type == queue_type,
                    Application.status == ApplicationStatusEnum.QUEUED
                )
            )
            existing_fios = set(fio for (fio,) in existing.fetchall())
            for app in applications:
                if app["fio"] in existing_fios:
                    skipped += 1
                    continue
                new_app = Application(
                    fio=app["fio"],
                    submitted_at=app["submitted_at"],
                    queue_type=queue_type,
                    is_priority=app.get("priority", False),
                    status=ApplicationStatusEnum.QUEUED
                )
                session.add(new_app)
                added += 1
            await session.commit()
            logger.info(f"Добавлено заявлений: {added}, пропущено: {skipped}")
    logger.info(f"Импорт завершен: очередь={queue_type}, добавлено={added}, пропущено={skipped}")
    return added, skipped, len(applications)

async def return_application_to_queue(app_id: int):
    async for session in get_session():
        stmt = update(Application).where(Application.id == app_id).values(
            status=ApplicationStatusEnum.QUEUED,
            processed_by_id=None,
            taken_at=None
        )
        await session.execute(stmt)
        await session.commit()

async def get_current_work_day(employee_id: int):
    """Получить текущий рабочий день сотрудника"""
    async for session in get_session():
        today = get_moscow_date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        stmt = select(WorkDay).where(
            WorkDay.employee_id == employee_id,
            WorkDay.date >= today_start,
            WorkDay.date <= today_end
        ).options(selectinload(WorkDay.breaks))
        result = await session.execute(stmt)
        work_day = result.scalars().first()
        
        return work_day

async def start_work_day(employee_id: int):
    """Начать рабочий день"""
    async for session in get_session():
        today = get_moscow_date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        # Проверяем, есть ли уже рабочий день на сегодня
        stmt = select(WorkDay).where(
            WorkDay.employee_id == employee_id,
            WorkDay.date >= today_start,
            WorkDay.date <= today_end
        )
        result = await session.execute(stmt)
        existing_day = result.scalars().first()
        
        if existing_day:
            return existing_day
        
        work_day = WorkDay(
            employee_id=employee_id,
            date=get_moscow_now(),  # Сохраняем полную дату и время
            start_time=get_moscow_now(),
            status=WorkDayStatusEnum.ACTIVE
        )
        session.add(work_day)
        await session.commit()
        return work_day

async def end_work_day(employee_id: int):
    """Завершить рабочий день"""
    async for session in get_session():
        work_day = await get_current_work_day(employee_id)
        if not work_day:
            return None
        
        work_day.end_time = get_moscow_now()
        work_day.status = WorkDayStatusEnum.FINISHED
        
        # Завершаем активный перерыв, если есть
        active_break = await get_active_break(work_day.id)
        if active_break:
            active_break.end_time = get_moscow_now()
            active_break.duration = int((active_break.end_time - active_break.start_time).total_seconds())
            work_day.total_break_time += active_break.duration
        
        # Обновляем общее время работы
        if work_day.start_time:
            total_work_seconds = int((work_day.end_time - work_day.start_time).total_seconds()) - work_day.total_break_time
            work_day.total_work_time = max(0, total_work_seconds)
        
        await session.commit()
        return work_day

async def start_break(employee_id: int):
    """Начать перерыв"""
    async for session in get_session():
        work_day = await get_current_work_day(employee_id)
        if not work_day:
            return None
        
        # Проверяем, нет ли уже активного перерыва
        active_break = await get_active_break(work_day.id)
        if active_break:
            return None
        
        # Обновляем общее время работы до начала перерыва
        if work_day.start_time and work_day.status.value == "active":
            current_time = get_moscow_now()
            elapsed_seconds = int((current_time - work_day.start_time).total_seconds())
            work_day.total_work_time = elapsed_seconds - work_day.total_break_time
        
        # Устанавливаем статус как приостановленный
        work_day.status = WorkDayStatusEnum.PAUSED
        
        work_break = WorkBreak(
            work_day_id=work_day.id,
            start_time=get_moscow_now()
        )
        session.add(work_break)
        await session.commit()
        return work_break

async def end_break(employee_id: int):
    """Завершить перерыв"""
    async for session in get_session():
        work_day = await get_current_work_day(employee_id)
        if not work_day:
            return None
        active_break = await get_active_break(work_day.id)
        if not active_break:
            return None
        active_break.end_time = get_moscow_now()
        active_break.duration = int((active_break.end_time - active_break.start_time).total_seconds())
        work_day.total_break_time += active_break.duration
        # Пересчитываем total_work_time после завершения перерыва
        if work_day.start_time and work_day.status.value == "paused":
            current_time = get_moscow_now()
            elapsed_seconds = int((current_time - work_day.start_time).total_seconds())
            work_day.total_work_time = elapsed_seconds - work_day.total_break_time
        # Возвращаем статус как активный
        work_day.status = WorkDayStatusEnum.ACTIVE
        await session.commit()
        return active_break

async def get_active_break(work_day_id: int):
    """Получить активный перерыв для рабочего дня"""
    async for session in get_session():
        stmt = select(WorkBreak).where(
            WorkBreak.work_day_id == work_day_id,
            WorkBreak.end_time.is_(None)
        )
        result = await session.execute(stmt)
        return result.scalars().first()

async def increment_processed_applications(employee_id: int):
    """Увеличить счетчик обработанных заявлений"""
    async for session in get_session():
        today = get_moscow_date()
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        logger.info(f"Увеличиваем счетчик для employee_id={employee_id}, дата={today}")
        
        # Получаем рабочий день в текущей сессии
        stmt = select(WorkDay).where(
            WorkDay.employee_id == employee_id,
            WorkDay.date >= today_start,
            WorkDay.date <= today_end
        )
        result = await session.execute(stmt)
        work_day = result.scalars().first()
        
        if work_day:
            old_count = work_day.applications_processed
            work_day.applications_processed += 1
            await session.commit()
            logger.info(f"Счетчик увеличен: {old_count} -> {work_day.applications_processed} для work_day_id={work_day.id}")
            return True
        else:
            # Если нет рабочего дня, создаем его автоматически
            work_day = WorkDay(
                employee_id=employee_id,
                date=get_moscow_now(),
                start_time=get_moscow_now(),
                status=WorkDayStatusEnum.ACTIVE,
                applications_processed=1  # Устанавливаем сразу 1
            )
            session.add(work_day)
            await session.commit()
            logger.info(f"Создан новый рабочий день с счетчиком=1 для employee_id={employee_id}, work_day_id={work_day.id}")
            return True

async def get_work_day_report(employee_id: int, report_date: date = None):
    """Получить отчет по рабочему дню"""
    async for session in get_session():
        if not report_date:
            report_date = get_moscow_date()
        
        today_start = datetime.combine(report_date, datetime.min.time())
        today_end = datetime.combine(report_date, datetime.max.time())
        
        stmt = select(WorkDay).where(
            WorkDay.employee_id == employee_id,
            WorkDay.date >= today_start,
            WorkDay.date <= today_end
        ).options(selectinload(WorkDay.breaks))
        result = await session.execute(stmt)
        work_day = result.scalars().first()
        
        if not work_day:
            return None
        
        return {
            "employee_id": work_day.employee_id,
            "date": work_day.date.date() if work_day.date else None,
            "start_time": work_day.start_time,
            "end_time": work_day.end_time,
            "total_work_time": work_day.total_work_time,
            "total_break_time": work_day.total_break_time,
            "applications_processed": work_day.applications_processed,
            "status": work_day.status.value,
            "breaks": [
                {
                    "start_time": break_item.start_time,
                    "end_time": break_item.end_time,
                    "duration": break_item.duration
                }
                for break_item in work_day.breaks
            ]
        }

async def get_all_work_days_report(report_date: date = None):
    """Получить отчет по всем сотрудникам за день"""
    async for session in get_session():
        if not report_date:
            report_date = get_moscow_date()
        
        today_start = datetime.combine(report_date, datetime.min.time())
        today_end = datetime.combine(report_date, datetime.max.time())
        
        stmt = select(WorkDay).where(
            WorkDay.date >= today_start,
            WorkDay.date <= today_end
        ).options(selectinload(WorkDay.employee), selectinload(WorkDay.breaks))
        result = await session.execute(stmt)
        work_days = result.scalars().all()
        
        reports = []
        for work_day in work_days:
            report = {
                "employee_fio": work_day.employee.fio,
                "employee_tg_id": work_day.employee.tg_id,
                "date": work_day.date.date() if work_day.date else None,
                "start_time": work_day.start_time,
                "end_time": work_day.end_time,
                "total_work_time": work_day.total_work_time,
                "total_break_time": work_day.total_break_time,
                "applications_processed": work_day.applications_processed,
                "status": work_day.status.value,
                "breaks": [
                    {
                        "start_time": break_item.start_time,
                        "end_time": break_item.end_time,
                        "duration": break_item.duration
                    }
                    for break_item in work_day.breaks
                ]
            }
            reports.append(report)
        
        return reports

async def get_next_epgu_application(employee_id: int = None, bot=None):
    """Получить следующее заявление из очереди ЕПГУ (не отложенное)"""
    async for session in get_session():
        # Сначала очищаем просроченные заявления
        expired_apps = await cleanup_expired_applications()
        
        # Отправляем уведомления о возвращённых заявлениях
        if expired_apps and bot:
            from config import ADMIN_CHAT_ID
            for app_info in expired_apps:
                # Уведомление в админ-чат
                admin_msg = f"⚠️ Заявление {app_info['app_id']} ({app_info['fio']}) возвращено в очередь {app_info['queue_type']} по истечении времени"
                if app_info['employee_fio']:
                    admin_msg += f"\nСотрудник: {app_info['employee_fio']}"
                await bot.send_message(ADMIN_CHAT_ID, admin_msg)
                
                # Уведомление сотруднику
                if app_info['employee_tg_id']:
                    try:
                        employee_msg = f"⚠️ Заявление {app_info['app_id']} ({app_info['fio']}) возвращено в очередь по истечении времени обработки (1 час)"
                        await bot.send_message(app_info['employee_tg_id'], employee_msg)
                    except Exception:
                        pass
        
        # Получаем заявление из очереди ЕПГУ, которое не отложено
        now = get_moscow_now()
        stmt = select(Application).where(
            Application.queue_type == "epgu",
            Application.status == ApplicationStatusEnum.QUEUED,
            (Application.postponed_until.is_(None) | (Application.postponed_until <= now))
        ).order_by(
            Application.submitted_at.asc()
        )
        result = await session.execute(stmt)
        app = result.scalars().first()
        
        if app and employee_id:
            # Сразу блокируем заявление за сотрудником
            app.status = ApplicationStatusEnum.IN_PROGRESS
            app.processed_by_id = employee_id
            app.taken_at = datetime.now()
            await session.commit()
        
        return app

async def update_application_queue_type(app_id: int, new_queue_type: str, employee_id: int = None, reason: str = None):
    """Обновить тип очереди заявления (для перемещения между очередями ЕПГУ)"""
    async for session in get_session():
        stmt = update(Application).where(Application.id == app_id).values(
            queue_type=new_queue_type,
            status=ApplicationStatusEnum.QUEUED,
            processed_by_id=employee_id,
            processed_at=get_moscow_now() if employee_id else None,
            status_reason=reason,
            taken_at=None  # Сбрасываем взятие в обработку
        )
        await session.execute(stmt)
        await session.commit()

async def postpone_application(app_id: int, employee_id: int = None):
    """Отложить заявление на сутки (для 'не дозвонились')"""
    async for session in get_session():
        from datetime import timedelta
        postponed_until = get_moscow_now() + timedelta(days=1)
        
        stmt = update(Application).where(Application.id == app_id).values(
            status=ApplicationStatusEnum.QUEUED,
            processed_by_id=employee_id,
            processed_at=get_moscow_now() if employee_id else None,
            postponed_until=postponed_until,
            taken_at=None
        )
        await session.execute(stmt)
        await session.commit()

async def get_applications_statistics_by_queue(report_date: date = None):
    """Получить статистику по заявлениям в разных очередях за день"""
    async for session in get_session():
        if not report_date:
            report_date = get_moscow_date()
        
        today_start = datetime.combine(report_date, datetime.min.time())
        today_end = datetime.combine(report_date, datetime.max.time())
        
        # Статистика по обработанным заявлениям (по processed_at)
        stmt = select(Application.queue_type, Application.processed_by_id).where(
            Application.processed_at >= today_start,
            Application.processed_at <= today_end
        ).options(selectinload(Application.processed_by))
        result = await session.execute(stmt)
        processed_apps = result.scalars().all()
        
        # Группируем по очередям
        queue_stats = {}
        for app in processed_apps:
            queue_type = app.queue_type
            if queue_type not in queue_stats:
                queue_stats[queue_type] = {
                    'total': 0,
                    'by_employee': {}
                }
            queue_stats[queue_type]['total'] += 1
            
            if app.processed_by:
                emp_fio = app.processed_by.fio or f"ID:{app.processed_by.id}"
                if emp_fio not in queue_stats[queue_type]['by_employee']:
                    queue_stats[queue_type]['by_employee'][emp_fio] = 0
                queue_stats[queue_type]['by_employee'][emp_fio] += 1
        
        return queue_stats

async def get_applications_by_fio_and_queue(fio: str, queue_type: str):
    """Получить заявления по ФИО в определенной очереди"""
    async for session in get_session():
        stmt = select(Application).where(
            Application.fio.ilike(f"%{fio}%"),
            Application.queue_type == queue_type
        ).order_by(Application.submitted_at.asc())
        result = await session.execute(stmt)
        return result.scalars().all()

async def get_problem_applications(queue_type: str):
    async for session in get_session():
        stmt = select(Application).where(
            Application.queue_type == f"{queue_type}_problem"
        ).order_by(Application.submitted_at.asc())
        result = await session.execute(stmt)
        return result.scalars().all()

async def get_application_by_id(app_id: int):
    async for session in get_session():
        stmt = select(Application).where(Application.id == app_id).options(selectinload(Application.processed_by))
        result = await session.execute(stmt)
        return result.scalars().first()

async def update_problem_status(app_id: int, status: str, comment: str = None, responsible: str = None):
    async for session in get_session():
        stmt = select(Application).where(Application.id == app_id)
        result = await session.execute(stmt)
        app = result.scalars().first()
        if not app:
            return None
        from db.models import ProblemStatusEnum
        if status == "solved":
            app.problem_status = ProblemStatusEnum.SOLVED
            app.status = ApplicationStatusEnum.ACCEPTED
            app.queue_type = app.queue_type.replace("_problem", "")
        elif status == "solved_return":
            app.problem_status = ProblemStatusEnum.SOLVED_RETURN
            app.status = ApplicationStatusEnum.QUEUED
            app.queue_type = app.queue_type.replace("_problem", "")
        elif status == "in_progress":
            app.problem_status = ProblemStatusEnum.IN_PROGRESS
            if comment:
                app.problem_comment = comment
            if responsible:
                app.problem_responsible = responsible
        else:
            app.problem_status = ProblemStatusEnum.NEW
        await session.commit()
        return app

async def search_applications_by_fio(fio: str):
    """Поиск заявлений по ФИО во всех очередях"""
    async for session in get_session():
        stmt = select(Application).where(
            Application.fio.ilike(f"%{fio}%")
        ).options(selectinload(Application.processed_by)).order_by(Application.submitted_at.desc())
        result = await session.execute(stmt)
        return result.scalars().all()

async def update_application_field(app_id: int, field: str, value):
    """Обновить любое поле заявления"""
    async for session in get_session():
        stmt = select(Application).where(Application.id == app_id)
        result = await session.execute(stmt)
        app = result.scalars().first()
        if not app:
            return False
        
        if hasattr(app, field):
            setattr(app, field, value)
            await session.commit()
            return True
        return False

async def delete_application(app_id: int):
    """Удалить заявление"""
    async for session in get_session():
        stmt = select(Application).where(Application.id == app_id)
        result = await session.execute(stmt)
        app = result.scalars().first()
        if not app:
            return False
        
        await session.delete(app)
        await session.commit()
        return True

async def get_all_employees():
    """Получить всех сотрудников для назначения ответственных"""
    async for session in get_session():
        stmt = select(Employee).order_by(Employee.fio)
        result = await session.execute(stmt)
        return result.scalars().all() 
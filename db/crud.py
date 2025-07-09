from sqlalchemy import select, update
from sqlalchemy.orm import selectinload
from .models import Application, ApplicationStatusEnum, Employee, Group
from datetime import datetime
from .session import get_session
import aiohttp
import tempfile
from utils.excel import parse_lk_applications_from_excel

async def get_next_application(queue_type: str):
    async for session in get_session():
        stmt = select(Application).where(
            Application.queue_type == queue_type,
            Application.status == ApplicationStatusEnum.QUEUED
        ).order_by(
            Application.is_priority.desc(),
            Application.submitted_at.asc()
        )
        result = await session.execute(stmt)
        return result.scalars().first()

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
        stmt = select(Employee).where(Employee.tg_id == tg_id).options(selectinload(Employee.groups))
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

async def import_applications_from_excel(document, queue_type: str):
    file = await document.download(destination_dir=None)
    import os
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
        tmp.write(file.getvalue())
        tmp_path = tmp.name
    if queue_type == "lk":
        applications = parse_lk_applications_from_excel(tmp_path)
    else:
        applications = []  # Для других очередей можно реализовать аналогично
    os.unlink(tmp_path)
    async for session in get_session():
        # Получить все ФИО уже в очереди с этим типом и статусом QUEUED
        existing = await session.execute(
            select(Application.fio).where(
                Application.queue_type == queue_type,
                Application.status == ApplicationStatusEnum.QUEUED
            )
        )
        existing_fios = set(fio for (fio,) in existing.fetchall())
        for app in applications:
            if app["fio"] in existing_fios:
                continue
            new_app = Application(
                fio=app["fio"],
                submitted_at=app["submitted_at"],
                queue_type=queue_type,
                is_priority=app.get("priority", False),
                status=ApplicationStatusEnum.QUEUED
            )
            session.add(new_app)
        await session.commit() 
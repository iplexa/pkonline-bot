from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from .models import Application, ApplicationStatusEnum, Employee, Group
from datetime import datetime

async def get_next_application(session: AsyncSession, queue_type: str):
    stmt = select(Application).where(
        Application.queue_type == queue_type,
        Application.status == ApplicationStatusEnum.QUEUED
    ).order_by(
        Application.is_priority.desc(),
        Application.submitted_at.asc()
    )
    result = await session.execute(stmt)
    return result.scalars().first()

async def update_application_status(session: AsyncSession, app_id: int, status: ApplicationStatusEnum, reason: str = None, employee_id: int = None):
    stmt = update(Application).where(Application.id == app_id).values(
        status=status,
        status_reason=reason,
        processed_by_id=employee_id
    )
    await session.execute(stmt)
    await session.commit()

async def add_application(session: AsyncSession, fio: str, submitted_at: datetime, queue_type: str, is_priority: bool = False):
    app = Application(fio=fio, submitted_at=submitted_at, queue_type=queue_type, is_priority=is_priority)
    session.add(app)
    await session.commit()
    return app

async def set_priority(session: AsyncSession, fio: str, queue_type: str):
    stmt = update(Application).where(
        Application.fio == fio,
        Application.queue_type == queue_type
    ).values(is_priority=True)
    await session.execute(stmt)
    await session.commit()

async def find_application_by_fio(session: AsyncSession, fio: str, queue_type: str):
    stmt = select(Application).where(
        Application.fio == fio,
        Application.queue_type == queue_type
    )
    result = await session.execute(stmt)
    return result.scalars().all()

async def get_employee_by_tg_id(session: AsyncSession, tg_id: str):
    stmt = select(Employee).where(Employee.tg_id == tg_id)
    result = await session.execute(stmt)
    return result.scalars().first()

async def employee_has_group(session: AsyncSession, tg_id: str, group_name: str):
    stmt = select(Employee).where(Employee.tg_id == tg_id).join(Employee.groups).where(Group.name == group_name)
    result = await session.execute(stmt)
    return result.scalars().first() is not None

async def is_admin(session: AsyncSession, tg_id: str):
    emp = await get_employee_by_tg_id(session, tg_id)
    return emp.is_admin if emp else False 

async def add_employee(session: AsyncSession, tg_id: str, fio: str, is_admin: bool = False):
    emp = Employee(tg_id=tg_id, fio=fio, is_admin=is_admin)
    session.add(emp)
    await session.commit()
    return emp

async def remove_employee(session: AsyncSession, tg_id: str):
    emp = await get_employee_by_tg_id(session, tg_id)
    if emp:
        await session.delete(emp)
        await session.commit()

async def add_group_to_employee(session: AsyncSession, tg_id: str, group_name: str):
    emp = await get_employee_by_tg_id(session, tg_id)
    if not emp:
        return False
    group = await session.execute(select(Group).where(Group.name == group_name))
    group = group.scalars().first()
    if not group:
        group = Group(name=group_name)
        session.add(group)
        await session.commit()
    if group not in emp.groups:
        emp.groups.append(group)
        await session.commit()
    return True

async def remove_group_from_employee(session: AsyncSession, tg_id: str, group_name: str):
    emp = await get_employee_by_tg_id(session, tg_id)
    if not emp:
        return False
    group = await session.execute(select(Group).where(Group.name == group_name))
    group = group.scalars().first()
    if group and group in emp.groups:
        emp.groups.remove(group)
        await session.commit()
    return True

async def list_employees_with_groups(session: AsyncSession):
    stmt = select(Employee)
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
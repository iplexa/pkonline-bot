import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_USER_ID
from handlers import common, lk, admin
from db.models import Base
from db.session import engine
from db.crud import add_employee, get_employee_by_tg_id

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def ensure_admin():
    admin = await get_employee_by_tg_id(str(ADMIN_USER_ID))
    if not admin:
        await add_employee(str(ADMIN_USER_ID), "Admin", is_admin_flag=True)

async def main():
    await create_tables()
    await ensure_admin()
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(common)
    dp.include_router(lk)
    dp.include_router(admin)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 
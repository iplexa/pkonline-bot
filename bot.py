import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, ADMIN_USER_ID
from handlers.common import router as common_router
from handlers.lk import router as lk_router
from handlers.epgu import router as epgu_router
from handlers.admin import router as admin_router
from handlers.mail import router as mail_router
from handlers.problem import router as problem_router
from db.models import Base
from db.session import engine
from db.crud import add_employee, get_employee_by_tg_id
from utils.logger import init_logger

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def ensure_admin():
    admin = await get_employee_by_tg_id(str(ADMIN_USER_ID))
    if not admin:
        await add_employee(str(ADMIN_USER_ID), "Администратор", is_admin_flag=True)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    
    # Инициализируем логгер
    init_logger(bot)
    
    # Регистрируем роутеры
    dp.include_router(common_router)
    dp.include_router(lk_router)
    dp.include_router(epgu_router)
    dp.include_router(admin_router)
    dp.include_router(mail_router)
    dp.include_router(problem_router)
    
    # Создаем таблицы
    await create_tables()
    
    # Добавляем админа если его нет
    await ensure_admin()
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 
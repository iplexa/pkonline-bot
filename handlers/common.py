from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from db.crud import get_employee_by_tg_id
from keyboards.main import main_menu_keyboard

router = Router()

@router.message(Command("start"))
@router.message(Command("help"))
async def start_handler(message: Message):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    if not emp:
        return
    is_admin = emp.is_admin
    groups = [g.name for g in emp.groups]
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard(is_admin=is_admin, groups=groups)
    )

@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp:
        return
    is_admin = emp.is_admin
    groups = [g.name for g in emp.groups]
    await callback.message.edit_text(
        "Главное меню:",
        reply_markup=main_menu_keyboard(is_admin=is_admin, groups=groups)
    ) 
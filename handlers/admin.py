from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.crud import (
    add_employee, remove_employee, add_group_to_employee, remove_group_from_employee, list_employees_with_groups, is_admin
)
from keyboards.admin import admin_menu_keyboard, group_choice_keyboard
from keyboards.main import main_menu_keyboard

router = Router()

class AdminStates(StatesGroup):
    waiting_tg_id = State()
    waiting_fio = State()
    waiting_tg_id_remove = State()
    waiting_tg_id_group = State()
    waiting_group_add = State()
    waiting_group_remove = State()

async def check_admin(user_id: int) -> bool:
    return await is_admin(str(user_id))

@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text("Админ-меню:", reply_markup=admin_menu_keyboard())

@router.callback_query(F.data == "admin_add_employee")
async def admin_add_employee(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_tg_id)
    await callback.message.edit_text("Введите Telegram ID нового сотрудника:", reply_markup=main_menu_keyboard(is_admin=True))

@router.message(AdminStates.waiting_tg_id)
async def admin_add_employee_tg_id(message: Message, state: FSMContext):
    await state.update_data(tg_id=message.text.strip())
    await state.set_state(AdminStates.waiting_fio)
    await message.answer("Введите ФИО сотрудника:", reply_markup=main_menu_keyboard(is_admin=True))

@router.message(AdminStates.waiting_fio)
async def admin_add_employee_fio(message: Message, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    fio = message.text.strip()
    await add_employee(tg_id, fio)
    await message.answer(f"Сотрудник {fio} ({tg_id}) добавлен.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.callback_query(F.data == "admin_remove_employee")
async def admin_remove_employee(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_tg_id_remove)
    await callback.message.edit_text("Введите Telegram ID сотрудника для удаления:", reply_markup=main_menu_keyboard(is_admin=True))

@router.message(AdminStates.waiting_tg_id_remove)
async def admin_remove_employee_tg_id(message: Message, state: FSMContext):
    tg_id = message.text.strip()
    await remove_employee(tg_id)
    await message.answer(f"Сотрудник {tg_id} удалён.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.callback_query(F.data == "admin_add_group")
async def admin_add_group(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_tg_id_group)
    await callback.message.edit_text("Введите Telegram ID сотрудника для назначения группы:", reply_markup=main_menu_keyboard(is_admin=True))

@router.message(AdminStates.waiting_tg_id_group)
async def admin_add_group_tg_id(message: Message, state: FSMContext):
    await state.update_data(tg_id=message.text.strip())
    await state.set_state(AdminStates.waiting_group_add)
    await message.answer("Выберите группу:", reply_markup=group_choice_keyboard())

@router.callback_query(AdminStates.waiting_group_add, F.data.startswith("group_"))
async def admin_add_group_choice(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    group = callback.data.replace("group_", "")
    await add_group_to_employee(tg_id, group)
    await callback.message.edit_text(f"Группа {group} добавлена сотруднику {tg_id}.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.callback_query(F.data == "admin_remove_group")
async def admin_remove_group(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_tg_id_group)
    await callback.message.edit_text("Введите Telegram ID сотрудника для удаления группы:", reply_markup=main_menu_keyboard(is_admin=True))

@router.message(AdminStates.waiting_tg_id_group)
async def admin_remove_group_tg_id(message: Message, state: FSMContext):
    await state.update_data(tg_id=message.text.strip())
    await state.set_state(AdminStates.waiting_group_remove)
    await message.answer("Выберите группу для удаления:", reply_markup=group_choice_keyboard())

@router.callback_query(AdminStates.waiting_group_remove, F.data.startswith("group_"))
async def admin_remove_group_choice(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    group = callback.data.replace("group_", "")
    await remove_group_from_employee(tg_id, group)
    await callback.message.edit_text(f"Группа {group} удалена у сотрудника {tg_id}.", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.callback_query(F.data == "admin_list_employees")
async def admin_list_employees(callback: CallbackQuery, state: FSMContext):
    emps = await list_employees_with_groups()
    text = "Сотрудники:\n" + "\n".join([
        f"{e['fio']} ({e['tg_id']}) {'[admin]' if e['is_admin'] else ''} — {', '.join(e['groups'])}" for e in emps
    ])
    await callback.message.edit_text(text, reply_markup=admin_menu_keyboard())
    await state.clear() 
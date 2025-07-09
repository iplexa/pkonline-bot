from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.crud import (
    add_employee, remove_employee, add_group_to_employee, remove_group_from_employee, list_employees_with_groups, is_admin, get_employee_by_tg_id
)
from keyboards.admin import admin_menu_keyboard, group_choice_keyboard
from keyboards.main import main_menu_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder

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

cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Отмена", callback_data="admin_menu")]
])

@router.callback_query(F.data == "admin_menu")
async def admin_menu(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text("Админ-меню:", reply_markup=admin_menu_keyboard())

@router.callback_query(F.data == "admin_add_employee")
async def admin_add_employee(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_tg_id)
    await callback.message.edit_text("Введите Telegram ID нового сотрудника:", reply_markup=cancel_keyboard)

@router.message(AdminStates.waiting_tg_id)
async def admin_add_employee_tg_id(message: Message, state: FSMContext):
    if message.text.strip().lower() == "отмена":
        await state.clear()
        await message.answer("Добавление отменено.", reply_markup=admin_menu_keyboard())
        return
    tg_id = message.text.strip()
    emp = await get_employee_by_tg_id(tg_id)
    if emp:
        await message.answer("Сотрудник с таким Telegram ID уже существует!", reply_markup=cancel_keyboard)
        return
    await state.update_data(tg_id=tg_id)
    await state.set_state(AdminStates.waiting_fio)
    await message.answer("Введите ФИО сотрудника:", reply_markup=cancel_keyboard)

@router.message(AdminStates.waiting_fio)
async def admin_add_employee_fio(message: Message, state: FSMContext):
    if message.text.strip().lower() == "отмена":
        await state.clear()
        await message.answer("Добавление отменено.", reply_markup=admin_menu_keyboard())
        return
    data = await state.get_data()
    tg_id = data.get("tg_id")
    fio = message.text.strip()
    try:
        await add_employee(tg_id, fio)
        await message.answer(f"Сотрудник {fio} ({tg_id}) добавлен.", reply_markup=admin_menu_keyboard())
    except Exception as e:
        await message.answer(f"Ошибка при добавлении: {e}", reply_markup=cancel_keyboard)
    await state.clear()

@router.callback_query(F.data == "admin_remove_employee")
async def admin_remove_employee(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_tg_id_remove)
    await callback.message.edit_text("Введите Telegram ID сотрудника для удаления:", reply_markup=cancel_keyboard)

@router.message(AdminStates.waiting_tg_id_remove)
async def admin_remove_employee_tg_id(message: Message, state: FSMContext):
    if message.text.strip().lower() == "отмена":
        await state.clear()
        await message.answer("Удаление отменено.", reply_markup=admin_menu_keyboard())
        return
    tg_id = message.text.strip()
    emp = await get_employee_by_tg_id(tg_id)
    if not emp:
        await message.answer("Сотрудник с таким Telegram ID не найден!", reply_markup=cancel_keyboard)
        return
    try:
        await remove_employee(tg_id)
        await message.answer(f"Сотрудник {tg_id} удалён.", reply_markup=admin_menu_keyboard())
    except Exception as e:
        await message.answer(f"Ошибка при удалении: {e}", reply_markup=cancel_keyboard)
    await state.clear()

@router.callback_query(F.data == "admin_add_group")
async def admin_add_group(callback: CallbackQuery, state: FSMContext):
    emps = await list_employees_with_groups()
    if not emps:
        await callback.message.edit_text("Нет сотрудников для назначения группы.", reply_markup=admin_menu_keyboard())
        return
    builder = InlineKeyboardBuilder()
    for e in emps:
        btn_text = f"{e['fio']} ({e['tg_id']})"
        builder.button(text=btn_text, callback_data=f"choose_emp_group_{e['tg_id']}")
    builder.button(text="Отмена", callback_data="admin_menu")
    builder.adjust(1)
    await callback.message.edit_text("Выберите сотрудника для назначения группы:", reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("choose_emp_group_"))
async def admin_add_group_choose_employee(callback: CallbackQuery, state: FSMContext):
    tg_id = callback.data.replace("choose_emp_group_", "")
    emp = await get_employee_by_tg_id(tg_id)
    if not emp:
        await callback.message.edit_text("Сотрудник не найден!", reply_markup=admin_menu_keyboard())
        await state.clear()
        return
    groups = [g.name for g in emp.groups] if emp.groups else []
    await state.update_data(tg_id=tg_id)
    await state.set_state(AdminStates.waiting_group_add)
    await callback.message.edit_text(f"Текущие группы сотрудника: {', '.join(groups) if groups else 'нет'}\nВыберите группу:", reply_markup=group_choice_keyboard())

@router.callback_query(AdminStates.waiting_group_add, F.data.startswith("group_"))
async def admin_add_group_choice(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    group = callback.data.replace("group_", "")
    emp = await get_employee_by_tg_id(tg_id)
    if not emp:
        await callback.message.edit_text("Сотрудник не найден!", reply_markup=admin_menu_keyboard())
        await state.clear()
        return
    if group in [g.name for g in emp.groups]:
        await callback.message.edit_text(f"У сотрудника уже есть группа {group}.", reply_markup=admin_menu_keyboard())
        await state.clear()
        return
    try:
        result = await add_group_to_employee(tg_id, group)
        if not result:
            await callback.message.edit_text(f"Не удалось добавить группу {group} сотруднику {tg_id}.", reply_markup=admin_menu_keyboard())
        else:
            await callback.message.edit_text(f"Группа {group} добавлена сотруднику {tg_id}.", reply_markup=admin_menu_keyboard())
    except Exception as e:
        await callback.message.edit_text(f"Ошибка при добавлении группы: {e}", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.callback_query(F.data == "admin_remove_group")
async def admin_remove_group(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_tg_id_group)
    await callback.message.edit_text("Введите Telegram ID сотрудника для удаления группы:", reply_markup=cancel_keyboard)

@router.message(AdminStates.waiting_tg_id_group)
async def admin_remove_group_tg_id(message: Message, state: FSMContext):
    if message.text.strip().lower() == "отмена":
        await state.clear()
        await message.answer("Удаление группы отменено.", reply_markup=admin_menu_keyboard())
        return
    tg_id = message.text.strip()
    emp = await get_employee_by_tg_id(tg_id)
    if not emp:
        await message.answer("Сотрудник с таким Telegram ID не найден!", reply_markup=cancel_keyboard)
        return
    groups = [g.name for g in emp.groups] if emp.groups else []
    if not groups:
        await message.answer("У сотрудника нет групп для удаления.", reply_markup=admin_menu_keyboard())
        await state.clear()
        return
    await state.update_data(tg_id=tg_id)
    await state.set_state(AdminStates.waiting_group_remove)
    await message.answer(f"Текущие группы сотрудника: {', '.join(groups)}\nВыберите группу для удаления:", reply_markup=group_choice_keyboard())

@router.callback_query(AdminStates.waiting_group_remove, F.data.startswith("group_"))
async def admin_remove_group_choice(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tg_id = data.get("tg_id")
    group = callback.data.replace("group_", "")
    emp = await get_employee_by_tg_id(tg_id)
    if not emp:
        await callback.message.edit_text("Сотрудник не найден!", reply_markup=admin_menu_keyboard())
        await state.clear()
        return
    if group not in [g.name for g in emp.groups]:
        await callback.message.edit_text(f"У сотрудника нет группы {group}.", reply_markup=admin_menu_keyboard())
        await state.clear()
        return
    try:
        await remove_group_from_employee(tg_id, group)
        await callback.message.edit_text(f"Группа {group} удалена у сотрудника {tg_id}.", reply_markup=admin_menu_keyboard())
    except Exception as e:
        await callback.message.edit_text(f"Ошибка при удалении группы: {e}", reply_markup=admin_menu_keyboard())
    await state.clear()

@router.callback_query(F.data == "admin_list_employees")
async def admin_list_employees(callback: CallbackQuery, state: FSMContext):
    emps = await list_employees_with_groups()
    if not emps:
        text = "Сотрудников не найдено."
    else:
        text = "Сотрудники:\n"
        for e in emps:
            text += f"\n<b>{e['fio']}</b> (<code>{e['tg_id']}</code>) {'[admin]' if e['is_admin'] else ''}\n"
            text += f"Группы: {', '.join(e['groups']) if e['groups'] else 'нет'}\n"
    await callback.message.edit_text(text, reply_markup=admin_menu_keyboard(), parse_mode="HTML")
    await state.clear() 
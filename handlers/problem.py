from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from db.crud import (
    get_problem_applications,
    get_employee_by_tg_id,
    has_access,
    update_problem_status,
    get_application_by_id
)
from keyboards.problem import problem_menu_keyboard, problem_list_keyboard, problem_action_keyboard, problem_status_keyboard
from keyboards.main import main_menu_keyboard
from config import ADMIN_CHAT_ID
import logging

logger = logging.getLogger(__name__)

router = Router()

class ProblemStates(StatesGroup):
    waiting_queue_type = State()
    waiting_action = State()
    waiting_comment = State()

@router.callback_query(F.data == "problem_menu")
async def problem_menu_entry(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "problem"):
        return
    await state.set_state(ProblemStates.waiting_queue_type)
    await callback.message.edit_text(
        "Выберите очередь для просмотра проблемных дел:",
        reply_markup=problem_menu_keyboard()
    )

@router.callback_query(ProblemStates.waiting_queue_type, F.data.startswith("problem_queue_"))
async def problem_queue_list(callback: CallbackQuery, state: FSMContext):
    queue_type = callback.data.replace("problem_queue_", "")
    problems = await get_problem_applications(queue_type)
    if not problems:
        await callback.message.edit_text(
            f"В очереди {queue_type} нет проблемных дел.",
            reply_markup=problem_menu_keyboard()
        )
        return
    await state.update_data(queue_type=queue_type)
    await state.set_state(ProblemStates.waiting_action)
    await callback.message.edit_text(
        "Список проблемных дел:",
        reply_markup=problem_list_keyboard(problems)
    )

@router.callback_query(ProblemStates.waiting_action, F.data.startswith("problem_app_"))
async def problem_app_action(callback: CallbackQuery, state: FSMContext):
    app_id = int(callback.data.replace("problem_app_", ""))
    app = await get_application_by_id(app_id)
    if not app:
        await callback.message.edit_text("Заявление не найдено.", reply_markup=problem_menu_keyboard())
        await state.clear()
        return
    await state.update_data(app_id=app_id)
    # Формируем подробную информацию
    text = f"<b>Проблемное дело</b>\n"
    text += f"ФИО: {app.fio}\n"
    text += f"Дата: {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"Причина: {app.status_reason or '-'}\n"
    text += f"Описание проблемы: {app.problem_comment or '-'}\n"
    text += f"Отправил: {app.processed_by.fio if app.processed_by else '-'}\n"
    text += f"Статус: {app.problem_status or 'новое'}\n"
    text += f"Ответственный: {app.problem_responsible or '-'}\n"
    await callback.message.edit_text(
        text,
        reply_markup=problem_action_keyboard(app_id),
        parse_mode="HTML"
    )

@router.callback_query(ProblemStates.waiting_action, F.data.startswith("problem_action_"))
async def problem_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    app_id = data.get("app_id")
    action = callback.data.replace("problem_action_", "")
    if action == "solved":
        await update_problem_status(app_id, "solved")
        await callback.message.edit_text("✅ Дело отмечено как решенное и отправлено как принятое.", reply_markup=problem_menu_keyboard())
        await state.clear()
        await problem_menu_entry(callback, state)
    elif action == "solved_return":
        await update_problem_status(app_id, "solved_return")
        await callback.message.edit_text("✅ Дело отмечено как решенное и возвращено в очередь.", reply_markup=problem_menu_keyboard())
        await state.clear()
        await problem_menu_entry(callback, state)
    elif action == "in_progress":
        await state.set_state(ProblemStates.waiting_comment)
        await callback.message.edit_text("Введите комментарий по процессу решения:", reply_markup=problem_status_keyboard())
    elif action == "cancel":
        await callback.message.edit_text("Дело осталось в проблемных.", reply_markup=problem_menu_keyboard())
        await state.clear()
        await problem_menu_entry(callback, state)

@router.message(ProblemStates.waiting_comment)
async def problem_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    app_id = data.get("app_id")
    comment = message.text.strip()
    await update_problem_status(app_id, "in_progress", comment=comment, responsible=message.from_user.full_name)
    await message.answer("Комментарий добавлен. Дело отмечено как 'в процессе решения'.", reply_markup=problem_menu_keyboard())
    await state.clear() 
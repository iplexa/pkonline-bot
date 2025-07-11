from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from db.crud import get_next_application, update_application_status, get_employee_by_tg_id, has_access, return_application_to_queue, increment_processed_applications, get_application_by_id, get_applications_by_fio_and_queue, escalate_application
from db.models import ApplicationStatusEnum
from keyboards.lk import lk_queue_keyboard, lk_decision_keyboard, lk_reason_keyboard, lk_escalate_keyboard
from keyboards.main import main_menu_keyboard
from config import ADMIN_CHAT_ID
from utils.logger import get_logger
import logging

logger = logging.getLogger(__name__)

router = Router()

class LKStates(StatesGroup):
    waiting_decision = State()
    waiting_reason = State()
    waiting_search_fio = State()

@router.callback_query(F.data == "lk_menu")
async def lk_menu_entry(callback: CallbackQuery, state: FSMContext):
    try:
        emp = await get_employee_by_tg_id(str(callback.from_user.id))
        if not emp or not await has_access(str(callback.from_user.id), "lk"):
            return
        await callback.message.edit_text("Очередь ЛК. Нажмите кнопку, чтобы получить заявление.", reply_markup=lk_decision_keyboard(menu=True))
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        import traceback
        print(traceback.format_exc())

@router.callback_query(F.data == "lk_next")
async def get_lk_application(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "lk"):
        return
    app = await get_next_application(queue_type="lk", employee_id=emp.id, bot=callback.bot)
    if not app:
        await callback.message.edit_text("Очередь пуста.", reply_markup=lk_queue_keyboard(menu=True))
        return
    await state.update_data(app_id=app.id)
    await callback.message.edit_text(f"Заявление: {app.fio}", reply_markup=lk_decision_keyboard(menu=False))
    await state.set_state(LKStates.waiting_decision)

@router.callback_query(LKStates.waiting_decision, F.data.in_(["accept_lk", "reject_lk", "problem_lk", "return_lk"]))
async def process_lk_decision(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "lk"):
        return
    data = await state.get_data()
    app_id = data.get("app_id")
    employee_id = emp.id if emp else None
    
    logger.info(f"Обработка решения: {callback.data} для app_id={app_id}, employee_id={employee_id}")
    
    if callback.data == "accept_lk":
        await update_application_status(app_id, ApplicationStatusEnum.ACCEPTED, employee_id=employee_id)
        result = await increment_processed_applications(employee_id)
        logger.info(f"Заявление принято: app_id={app_id}, increment_result={result}")
        await callback.message.edit_text("Заявление принято.", reply_markup=lk_queue_keyboard(menu=True))
        
        # Логируем событие
        telegram_logger = get_logger()
        if telegram_logger:
            app = await get_application_by_id(app_id)
            if app:
                await telegram_logger.log_lk_accepted(emp.fio, app_id, app.fio)
        
        await callback.bot.send_message(ADMIN_CHAT_ID, f"ЛК: {callback.from_user.full_name} принял заявление {app_id}")
        await state.clear()
    elif callback.data == "return_lk":
        await return_application_to_queue(app_id)
        await callback.message.edit_text("Заявление возвращено в очередь.", reply_markup=lk_queue_keyboard(menu=True))
        await state.clear()
    elif callback.data in ["reject_lk", "problem_lk"]:
        await state.set_state(LKStates.waiting_reason)
        await state.update_data(decision=callback.data)
        await callback.message.edit_text("Укажите причину:", reply_markup=lk_reason_keyboard())

@router.callback_query(LKStates.waiting_reason, F.data == "lk_cancel_reason")
async def cancel_lk_reason(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    app_id = data.get("app_id")
    if app_id:
        await callback.message.edit_text(
            "Выберите действие:",
            reply_markup=lk_decision_keyboard(menu=False)
        )
        await state.set_state(LKStates.waiting_decision)
    else:
        await callback.message.edit_text(
            "Действие отменено.",
            reply_markup=lk_queue_keyboard(menu=True)
        )
        await state.clear()

@router.message(LKStates.waiting_reason)
async def process_lk_reason(message: Message, state: FSMContext):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    if not emp or not await has_access(str(message.from_user.id), "lk"):
        return
    data = await state.get_data()
    app_id = data.get("app_id")
    decision = data.get("decision")
    employee_id = emp.id if emp else None
    reason = message.text
    
    logger.info(f"Обработка причины: decision={decision}, app_id={app_id}, employee_id={employee_id}")
    
    status = ApplicationStatusEnum.REJECTED if decision == "reject_lk" else ApplicationStatusEnum.PROBLEM
    await update_application_status(app_id, status, reason=reason, employee_id=employee_id)
    
    if status == ApplicationStatusEnum.REJECTED:
        result = await increment_processed_applications(employee_id)
        logger.info(f"Заявление отклонено: app_id={app_id}, increment_result={result}")
    
    status_text = "отклонено" if status == ApplicationStatusEnum.REJECTED else "помечено как проблемное"
    await message.answer(f"Заявление {status_text}. Причина: {reason}", reply_markup=lk_queue_keyboard(menu=True))
    
    # Логируем событие
    telegram_logger = get_logger()
    if telegram_logger:
        app = await get_application_by_id(app_id)
        if app:
            if status == ApplicationStatusEnum.REJECTED:
                await telegram_logger.log_lk_rejected(emp.fio, app_id, app.fio, reason)
            else:
                await telegram_logger.log_lk_problem(emp.fio, app_id, app.fio, reason)
    
    await message.bot.send_message(ADMIN_CHAT_ID, f"ЛК: {message.from_user.full_name} {status_text} заявление {app_id}. Причина: {reason}")
    await state.clear()

@router.callback_query(LKStates.waiting_decision, F.data == "main_menu")
async def block_menu_exit_during_processing(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Сначала обработайте текущее заявление!", show_alert=True)

@router.callback_query(F.data == "lk_search_fio")
async def lk_search_fio_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(LKStates.waiting_search_fio)
    await callback.message.edit_text("Введите ФИО для поиска заявлений:", reply_markup=lk_queue_keyboard(menu=True))

@router.message(LKStates.waiting_search_fio)
async def lk_search_fio_process(message: Message, state: FSMContext):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    if not emp or not await has_access(str(message.from_user.id), "lk"):
        return
    fio = message.text.strip()
    if not fio:
        await message.answer("Пожалуйста, введите ФИО.", reply_markup=lk_queue_keyboard(menu=True))
        return
    apps = await get_applications_by_fio_and_queue(fio, "lk")
    if not apps:
        await message.answer(f"Заявления для '{fio}' не найдены.", reply_markup=lk_queue_keyboard(menu=True))
        await state.clear()
        return
    for app in apps:
        text = f"📋 Заявление ЛК #{app.id}\n\n"
        text += f"👨‍💼 ФИО: {app.fio}\n"
        text += f"📅 Дата подачи: {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
        if app.is_priority:
            text += "🚨 ПРИОРИТЕТНОЕ\n"
        await message.answer(text, reply_markup=lk_escalate_keyboard(app.id, app.is_priority))
    await state.clear()

@router.callback_query(F.data.startswith("lk_escalate_"))
async def lk_escalate_handler(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "lk"):
        return
    app_id = int(callback.data.replace("lk_escalate_", ""))
    success = await escalate_application(app_id)
    if success:
        from db.crud import get_application_by_id
        app = await get_application_by_id(app_id)
        # Логирование
        logger = get_logger()
        if logger and app:
            await logger.log_escalation(app.id, app.queue_type, emp.fio, reason="Эскалация через поиск по ФИО")
        await callback.message.edit_text(f"✅ Заявление {app_id} эскалировано (приоритетное)", reply_markup=lk_queue_keyboard(menu=True))
    else:
        await callback.message.edit_text("❌ Не удалось эскалировать заявление.", reply_markup=lk_queue_keyboard(menu=True)) 
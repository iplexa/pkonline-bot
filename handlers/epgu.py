from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from db.crud import (
    get_next_epgu_application, 
    update_application_status, 
    update_application_queue_type,
    postpone_application,
    get_employee_by_tg_id, 
    has_access, 
    return_application_to_queue, 
    increment_processed_applications,
    update_application_field
)
from db.models import ApplicationStatusEnum, EPGUActionEnum
from keyboards.epgu import epgu_queue_keyboard, epgu_decision_keyboard, epgu_reason_keyboard
from keyboards.main import main_menu_keyboard
from config import ADMIN_CHAT_ID
import logging

logger = logging.getLogger(__name__)

router = Router()

class EPGUStates(StatesGroup):
    waiting_decision = State()
    waiting_reason = State()

@router.callback_query(F.data == "epgu_menu")
async def epgu_menu_entry(callback: CallbackQuery, state: FSMContext):
    try:
        emp = await get_employee_by_tg_id(str(callback.from_user.id))
        if not emp or not await has_access(str(callback.from_user.id), "epgu"):
            return
        await callback.message.edit_text("Очередь ЕПГУ. Нажмите кнопку, чтобы получить заявление.", reply_markup=epgu_queue_keyboard(menu=True))
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        import traceback
        print(traceback.format_exc())

@router.callback_query(F.data == "get_epgu_application")
async def get_epgu_application(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "epgu"):
        return
    app = await get_next_epgu_application(employee_id=emp.id, bot=callback.bot)
    if not app:
        await callback.message.edit_text("Очередь пуста.", reply_markup=epgu_queue_keyboard(menu=True))
        return
    await state.update_data(app_id=app.id)
    await callback.message.edit_text(f"Заявление: {app.fio}", reply_markup=epgu_decision_keyboard(menu=False))
    await state.set_state(EPGUStates.waiting_decision)

@router.callback_query(EPGUStates.waiting_decision, F.data.in_([
    "epgu_accept", "epgu_has_scans", "epgu_no_scans", "epgu_only_scans", "epgu_error", "return_epgu"
]))
async def process_epgu_decision(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "epgu"):
        return
    data = await state.get_data()
    app_id = data.get("app_id")
    employee_id = emp.id if emp else None

    logger.info(f"Обработка решения ЕПГУ: {callback.data} для app_id={app_id}, employee_id={employee_id}")

    if callback.data == "epgu_accept":
        # Вариант 1: Принято сразу
        await update_application_status(app_id, ApplicationStatusEnum.ACCEPTED, employee_id=employee_id)
        # Сохраняем, что обработал сотрудник ЕПГУ
        await update_application_field(app_id, "epgu_action", EPGUActionEnum.ACCEPTED.value)
        await update_application_field(app_id, "epgu_processor_id", employee_id)
        result = await increment_processed_applications(employee_id)
        logger.info(f"Заявление ЕПГУ принято: app_id={app_id}, increment_result={result}")
        await callback.message.edit_text("Заявление принято.", reply_markup=epgu_queue_keyboard(menu=True))
        await callback.bot.send_message(ADMIN_CHAT_ID, f"ЕПГУ: {callback.from_user.full_name} принял заявление {app_id}")
        await state.clear()

    elif callback.data == "epgu_has_scans":
        # Вариант 2: Есть сканы, отправляем на подпись (в очередь почты)
        await update_application_queue_type(app_id, "epgu_mail", employee_id=employee_id)
        await update_application_field(app_id, "epgu_action", EPGUActionEnum.HAS_SCANS.value)
        await update_application_field(app_id, "epgu_processor_id", employee_id)
        await update_application_field(app_id, "needs_scans", False)
        await update_application_field(app_id, "needs_signature", True)
        await update_application_field(app_id, "scans_confirmed", True)
        await update_application_field(app_id, "signature_confirmed", False)
        result = await increment_processed_applications(employee_id)
        logger.info(f"Заявление ЕПГУ отправлено на подпись (есть сканы): app_id={app_id}, increment_result={result}")
        await callback.message.edit_text("Заявление отправлено в очередь почты для подписи.", reply_markup=epgu_queue_keyboard(menu=True))
        await callback.bot.send_message(ADMIN_CHAT_ID, f"ЕПГУ: {callback.from_user.full_name} отправил заявление {app_id} на подпись (есть сканы)")
        await state.clear()

    elif callback.data == "epgu_no_scans":
        # Вариант 3: Нет сканов, отправляем на подпись и запрашиваем сканы (в очередь почты)
        await update_application_queue_type(app_id, "epgu_mail", employee_id=employee_id)
        await update_application_field(app_id, "epgu_action", EPGUActionEnum.NO_SCANS.value)
        await update_application_field(app_id, "epgu_processor_id", employee_id)
        await update_application_field(app_id, "needs_scans", True)
        await update_application_field(app_id, "needs_signature", True)
        await update_application_field(app_id, "scans_confirmed", False)
        await update_application_field(app_id, "signature_confirmed", False)
        result = await increment_processed_applications(employee_id)
        logger.info(f"Заявление ЕПГУ отправлено на подпись и запрос сканов: app_id={app_id}, increment_result={result}")
        await callback.message.edit_text("Заявление отправлено в очередь почты для подписи и запроса сканов.", reply_markup=epgu_queue_keyboard(menu=True))
        await callback.bot.send_message(ADMIN_CHAT_ID, f"ЕПГУ: {callback.from_user.full_name} отправил заявление {app_id} на подпись и запрос сканов")
        await state.clear()

    elif callback.data == "epgu_only_scans":
        # Новый вариант: нужны только сканы, подпись не требуется
        await update_application_queue_type(app_id, "epgu_mail", employee_id=employee_id)
        await update_application_field(app_id, "epgu_action", EPGUActionEnum.ONLY_SCANS.value)
        await update_application_field(app_id, "epgu_processor_id", employee_id)
        await update_application_field(app_id, "needs_scans", True)
        await update_application_field(app_id, "needs_signature", False)
        await update_application_field(app_id, "scans_confirmed", False)
        await update_application_field(app_id, "signature_confirmed", True)
        result = await increment_processed_applications(employee_id)
        logger.info(f"Заявление ЕПГУ отправлено в очередь почты (только сканы): app_id={app_id}, increment_result={result}")
        await callback.message.edit_text("Заявление отправлено в очередь почты для получения сканов (подпись не требуется).", reply_markup=epgu_queue_keyboard(menu=True))
        await callback.bot.send_message(ADMIN_CHAT_ID, f"ЕПГУ: {callback.from_user.full_name} отправил заявление {app_id} на получение сканов (без подписи)")
        await state.clear()

    elif callback.data == "epgu_error":
        # Вариант 4: Ошибка — запросить причину
        await state.set_state(EPGUStates.waiting_reason)
        await state.update_data(decision="epgu_error")
        await callback.message.edit_text("Укажите причину ошибки:", reply_markup=epgu_reason_keyboard())

    elif callback.data == "return_epgu":
        # Вернуть в очередь
        await return_application_to_queue(app_id)
        await callback.message.edit_text("Заявление возвращено в очередь.", reply_markup=epgu_queue_keyboard(menu=True))
        await state.clear()

@router.callback_query(EPGUStates.waiting_reason, F.data == "epgu_cancel_reason")
async def cancel_epgu_reason(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    app_id = data.get("app_id")
    if app_id:
        await callback.message.edit_text(
            "Выберите действие:",
            reply_markup=epgu_decision_keyboard(menu=False)
        )
        await state.set_state(EPGUStates.waiting_decision)
    else:
        await callback.message.edit_text(
            "Действие отменено.",
            reply_markup=epgu_queue_keyboard(menu=True)
        )
        await state.clear()

@router.message(EPGUStates.waiting_reason)
async def process_epgu_reason(message: Message, state: FSMContext):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    if not emp or not await has_access(str(message.from_user.id), "epgu"):
        return
    data = await state.get_data()
    app_id = data.get("app_id")
    decision = data.get("decision")
    employee_id = emp.id if emp else None
    reason = message.text
    
    logger.info(f"Обработка причины ЕПГУ: decision={decision}, app_id={app_id}, employee_id={employee_id}")
    
    if decision == "epgu_error":
        # Перевести в очередь проблем
        await update_application_queue_type(app_id, "epgu_problem", employee_id=employee_id, reason=reason)
        result = await increment_processed_applications(employee_id)
        logger.info(f"Заявление ЕПГУ помечено как проблемное: app_id={app_id}, increment_result={result}")
        
        await message.answer(f"Заявление помечено как проблемное. Причина: {reason}", reply_markup=epgu_queue_keyboard(menu=True))
        await message.bot.send_message(ADMIN_CHAT_ID, f"ЕПГУ: {message.from_user.full_name} пометил заявление {app_id} как проблемное. Причина: {reason}")
        await state.clear()

@router.callback_query(EPGUStates.waiting_decision, F.data == "main_menu")
async def block_menu_exit_during_processing(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Сначала обработайте текущее заявление!", show_alert=True) 
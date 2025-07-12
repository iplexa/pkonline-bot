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
    update_application_field,
    get_application_by_id,
    get_applications_by_fio_and_queue,
    escalate_application,
    get_moscow_now
)
from db.models import ApplicationStatusEnum, EPGUActionEnum
from keyboards.epgu import epgu_queue_keyboard, epgu_decision_keyboard, epgu_reason_keyboard, epgu_escalate_keyboard
from keyboards.main import main_menu_keyboard
from config import ADMIN_CHAT_ID
from utils.logger import get_logger
import logging

logger = logging.getLogger(__name__)

router = Router()

class EPGUStates(StatesGroup):
    waiting_decision = State()
    waiting_reason = State()
    waiting_search_fio = State()

@router.callback_query(F.data == "epgu_menu")
async def epgu_menu_entry(callback: CallbackQuery, state: FSMContext):
    try:
        emp = await get_employee_by_tg_id(str(callback.from_user.id))
        if not emp or not await has_access(str(callback.from_user.id), "epgu"):
            return
        await callback.message.edit_text("Очередь ЕПГУ. Нажмите кнопку, чтобы получить заявление.", reply_markup=epgu_decision_keyboard(menu=True))
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        import traceback
        print(traceback.format_exc())

@router.callback_query(F.data == "epgu_next")
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
    "accept_epgu", "epgu_signature", "epgu_signature_scans", "epgu_scans", "epgu_error", "return_epgu"
]))
async def process_epgu_decision(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "epgu"):
        return
    data = await state.get_data()
    app_id = data.get("app_id")
    employee_id = emp.id if emp else None

    logger.info(f"Обработка решения ЕПГУ: {callback.data} для app_id={app_id}, employee_id={employee_id}")

    if callback.data == "accept_epgu":
        # Вариант 1: Принято сразу
        await update_application_status(app_id, ApplicationStatusEnum.ACCEPTED, employee_id=employee_id)
        # Сохраняем, что обработал сотрудник ЕПГУ
        await update_application_field(app_id, "epgu_action", EPGUActionEnum.ACCEPTED.value)
        await update_application_field(app_id, "epgu_processor_id", employee_id)
        result = await increment_processed_applications(employee_id)
        logger.info(f"Заявление ЕПГУ принято: app_id={app_id}, increment_result={result}")
        await callback.message.edit_text("Заявление принято.", reply_markup=epgu_decision_keyboard(menu=True))
        
        # Логируем событие
        telegram_logger = get_logger()
        if telegram_logger:
            app = await get_application_by_id(app_id)
            if app:
                await telegram_logger.log_epgu_accepted(emp.fio, app_id, app.fio)
        
        await callback.bot.send_message(ADMIN_CHAT_ID, f"ЕПГУ: {callback.from_user.full_name} принял заявление {app_id}")
        await state.clear()

    elif callback.data == "epgu_signature":
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
        await callback.message.edit_text("Заявление отправлено в очередь почты для подписи.", reply_markup=epgu_decision_keyboard(menu=True))
        
        # Логируем событие
        telegram_logger = get_logger()
        if telegram_logger:
            app = await get_application_by_id(app_id)
            if app:
                await telegram_logger.log_epgu_mail_queue(emp.fio, app_id, app.fio, "Подпись (есть сканы)")
        
        await callback.bot.send_message(ADMIN_CHAT_ID, f"ЕПГУ: {callback.from_user.full_name} отправил заявление {app_id} на подпись (есть сканы)")
        await state.clear()

    elif callback.data == "epgu_signature_scans":
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
        await callback.message.edit_text("Заявление отправлено в очередь почты для подписи и запроса сканов.", reply_markup=epgu_decision_keyboard(menu=True))
        
        # Логируем событие
        telegram_logger = get_logger()
        if telegram_logger:
            app = await get_application_by_id(app_id)
            if app:
                await telegram_logger.log_epgu_mail_queue(emp.fio, app_id, app.fio, "Подпись и запрос сканов")
        
        await callback.bot.send_message(ADMIN_CHAT_ID, f"ЕПГУ: {callback.from_user.full_name} отправил заявление {app_id} на подпись и запрос сканов")
        await state.clear()

    elif callback.data == "epgu_scans":
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
        await callback.message.edit_text("Заявление отправлено в очередь почты для получения сканов (подпись не требуется).", reply_markup=epgu_decision_keyboard(menu=True))
        
        # Логируем событие
        telegram_logger = get_logger()
        if telegram_logger:
            app = await get_application_by_id(app_id)
            if app:
                await telegram_logger.log_epgu_mail_queue(emp.fio, app_id, app.fio, "Получение сканов")
        
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
        await callback.message.edit_text("Заявление возвращено в очередь.", reply_markup=epgu_decision_keyboard(menu=True))
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
        
        await message.answer(f"Заявление помечено как проблемное. Причина: {reason}", reply_markup=epgu_decision_keyboard(menu=True))
        
        # Логируем событие
        telegram_logger = get_logger()
        if telegram_logger:
            app = await get_application_by_id(app_id)
            if app:
                await telegram_logger.log_epgu_problem(emp.fio, app_id, app.fio, reason)
        
        await message.bot.send_message(ADMIN_CHAT_ID, f"ЕПГУ: {message.from_user.full_name} пометил заявление {app_id} как проблемное. Причина: {reason}")
        await state.clear()

@router.callback_query(EPGUStates.waiting_decision, F.data == "main_menu")
async def block_menu_exit_during_processing(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Сначала обработайте текущее заявление!", show_alert=True)

@router.callback_query(F.data == "epgu_search_fio")
async def epgu_search_fio_start(callback: CallbackQuery, state: FSMContext):
    await state.set_state(EPGUStates.waiting_search_fio)
    await callback.message.edit_text("Введите ФИО для поиска заявлений:", reply_markup=epgu_decision_keyboard(menu=True))

@router.message(EPGUStates.waiting_search_fio)
async def epgu_search_fio_process(message: Message, state: FSMContext):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    if not emp or not await has_access(str(message.from_user.id), "epgu"):
        return
    fio = message.text.strip()
    if not fio:
        await message.answer("Пожалуйста, введите ФИО.", reply_markup=epgu_decision_keyboard(menu=True))
        return
    apps = await get_applications_by_fio_and_queue(fio, "epgu")
    if not apps:
        await message.answer(f"Заявления для '{fio}' не найдены.", reply_markup=epgu_decision_keyboard(menu=True))
        await state.clear()
        return
    
    # Статус эмодзи
    status_emoji = {
        'queued': '⏳',
        'in_progress': '🔄',
        'accepted': '✅',
        'rejected': '❌',
        'problem': '⚠️'
    }
    
    for app in apps:
        text = f"🏛️ <b>Заявление ЕПГУ #{app.id}</b>\n\n"
        text += f"👨‍💼 <b>ФИО:</b> {app.fio}\n"
        text += f"📅 <b>Дата подачи:</b> {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"📊 <b>Статус:</b> {status_emoji.get(app.status.value, '❓')} {app.status.value}\n"
        if app.is_priority:
            text += "🚨 <b>ПРИОРИТЕТНОЕ</b>\n"
        if app.status_reason:
            text += f"💬 <b>Причина:</b> {app.status_reason}\n"
        text += f"🔍 <b>Поисковый запрос:</b> '{fio}'\n"
        
        await message.answer(text, reply_markup=epgu_escalate_keyboard(app.id, app.is_priority, app.status.value), parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data.startswith("epgu_escalate_"))
async def epgu_escalate_handler(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "epgu"):
        return
    app_id = int(callback.data.replace("epgu_escalate_", ""))
    success = await escalate_application(app_id)
    if success:
        from db.crud import get_application_by_id
        app = await get_application_by_id(app_id)
        # Логирование
        logger = get_logger()
        if logger and app:
            await logger.log_escalation(app.id, app.queue_type, emp.fio, reason="Эскалация через поиск по ФИО")
        await callback.message.edit_text(f"✅ Заявление {app_id} эскалировано (приоритетное)", reply_markup=epgu_decision_keyboard(menu=True))
    else:
        await callback.message.edit_text("❌ Не удалось эскалировать заявление.", reply_markup=epgu_decision_keyboard(menu=True))

@router.callback_query(F.data.startswith("epgu_process_found_"))
async def epgu_process_found_application(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "epgu"):
        return
    
    app_id = int(callback.data.replace("epgu_process_found_", ""))
    app = await get_application_by_id(app_id)
    
    if not app:
        await callback.message.edit_text("Заявление не найдено.", reply_markup=epgu_decision_keyboard(menu=True))
        return
    
    # Проверяем, что заявление в очереди ЕПГУ
    if app.queue_type != "epgu":
        await callback.message.edit_text("Это заявление не в очереди ЕПГУ.", reply_markup=epgu_decision_keyboard(menu=True))
        return
    
    # Проверяем, что заявление в очереди (не в обработке)
    if app.status != ApplicationStatusEnum.QUEUED:
        await callback.message.edit_text("Это заявление уже обрабатывается или обработано.", reply_markup=epgu_decision_keyboard(menu=True))
        return
    
    # Берем заявление в обработку
    await update_application_status(app_id, ApplicationStatusEnum.IN_PROGRESS, employee_id=emp.id)
    await update_application_field(app_id, "taken_at", get_moscow_now())
    
    # Сохраняем ID заявления в состоянии для дальнейшей обработки
    await state.update_data(app_id=app_id)
    
    # Показываем информацию о заявлении и кнопки для принятия решения
    text = f"🏛️ <b>Обработка заявления ЕПГУ</b>\n\n"
    text += f"🆔 <b>ID:</b> {app.id}\n"
    text += f"👨‍💼 <b>ФИО:</b> {app.fio}\n"
    text += f"📅 <b>Дата подачи:</b> {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
    if app.is_priority:
        text += "🚨 <b>ПРИОРИТЕТНОЕ</b>\n"
    text += f"💬 <b>Причина:</b> {app.status_reason or '-'}\n"
    
    await callback.message.edit_text(text, reply_markup=epgu_decision_keyboard(menu=False), parse_mode="HTML")
    await state.set_state(EPGUStates.waiting_decision) 
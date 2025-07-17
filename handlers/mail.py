from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db.crud import (
    get_applications_by_fio_and_queue,
    update_application_status,
    get_employee_by_tg_id, 
    has_access, 
    increment_processed_applications,
    update_application_field,
    return_application_to_queue,
    get_application_by_id,
    get_applications_by_email_and_queue
)
from db.models import ApplicationStatusEnum
from keyboards.mail import mail_menu_keyboard, mail_search_keyboard, mail_confirm_keyboard, mail_fio_search_keyboard
from keyboards.main import main_menu_keyboard
from config import ADMIN_CHAT_ID
from utils.logger import get_logger
import logging

logger = logging.getLogger(__name__)

router = Router()

class MailStates(StatesGroup):
    waiting_fio_search = State()
    waiting_confirm = State()
    waiting_fio_info = State()
    waiting_scans = State()
    waiting_signature = State()

@router.callback_query(F.data == "mail_menu")
async def mail_menu_entry(callback: CallbackQuery, state: FSMContext):
    try:
        emp = await get_employee_by_tg_id(str(callback.from_user.id))
        if not emp or not await has_access(str(callback.from_user.id), "mail"):
            return
        await callback.message.edit_text(
            "📮 Очередь почты. Здесь подтверждается подпись документов.\n\n"
            "Используйте поиск по ФИО для нахождения заявлений.",
            reply_markup=mail_menu_keyboard()
        )
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        import traceback
        print(traceback.format_exc())



@router.callback_query(F.data == "mail_search_fio")
async def mail_search_fio_start(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "mail"):
        return
    await state.set_state(MailStates.waiting_fio_search)
    await callback.message.edit_text(
        "Введите ФИО <b>или email</b> заявителя для поиска заявления в очереди почты:",
        reply_markup=mail_search_keyboard(),
        parse_mode="HTML"
    )

@router.message(MailStates.waiting_fio_search)
async def mail_search_fio_process(message: Message, state: FSMContext):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    if not emp or not await has_access(str(message.from_user.id), "mail"):
        return
    fio = message.text.strip()
    if not fio:
        await message.answer("Пожалуйста, введите ФИО или email заявителя.")
        return
    # Универсальный поиск: если email — ищем по email, иначе по ФИО
    if "@" in fio and "." in fio:
        all_applications = await get_applications_by_email_and_queue(fio, "epgu_mail")
        search_type = "email"
    else:
        all_applications = await get_applications_by_fio_and_queue(fio, "epgu_mail")
        search_type = "ФИО"
    if not all_applications:
        # Если искали по ФИО — пробуем найти похожие ФИО
        if search_type == "ФИО" and len(fio) >= 3:
            similar_apps = await get_applications_by_fio_and_queue(fio[:3], "epgu_mail")
            if similar_apps:
                unique_fios = sorted(set(app.fio for app in similar_apps))
                text = f"Заявления для '{fio}' не найдены. Возможно, вы имели в виду:\n" + '\n'.join(unique_fios)
                await message.answer(text, reply_markup=mail_menu_keyboard())
                await state.clear()
                return
        await message.answer(
            f"Заявления для '{fio}' в очереди почты не найдены.",
            reply_markup=mail_menu_keyboard()
        )
        await state.clear()
        return
    # Фильтруем только неподтвержденные заявления
    applications = [app for app in all_applications if app.status != ApplicationStatusEnum.ACCEPTED]
    if not applications:
        await message.answer(
            f"У заявителя '{fio}' все заявления уже подтверждены. Повторное подтверждение не требуется.",
            reply_markup=mail_menu_keyboard()
        )
        await state.clear()
        return
    if len(applications) == 1:
        app = applications[0]
        await state.update_data(app_id=app.id, fio=fio)
        await state.set_state(MailStates.waiting_confirm)
        # Формируем подробное описание
        doc_list = []
        if getattr(app, 'needs_signature', False):
            doc_list.append("Подпись")
        if getattr(app, 'needs_scans', False):
            doc_list.append("Сканы")
        doc_text = ", ".join(doc_list) if doc_list else "-"
        epgu_operator = getattr(app, 'epgu_processor', None)
        epgu_fio = epgu_operator.fio if epgu_operator and hasattr(epgu_operator, 'fio') else "-"
        await message.answer(
            f"📋 Найдено заявление:\n\n"
            f"ФИО: {app.fio}\n"
            f"Email: {app.email or '-'}\n"
            f"Дата подачи: {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"ID: {app.id}\n"
            f"Нужно подтвердить: {doc_text}\n"
            f"Обработал в ЕПГУ: {epgu_fio}\n\n"
            f"Подтвердите, что все необходимые документы в наличии:",
            reply_markup=mail_confirm_keyboard()
        )
    else:
        # Несколько заявлений - показываем кнопки для выбора
        text = f"📋 Найдено {len(applications)} заявлений для '{fio}' ({search_type}):\n\nВыберите нужное заявление:"
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{i+1}. {app.submitted_at.strftime('%d.%m.%Y %H:%M')} | {app.email or '-'}", callback_data=f"mail_select_{app.id}")]
                for i, app in enumerate(applications)
            ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="mail_back_to_menu")]]
        )
        await state.update_data(applications=[{"id": app.id, "fio": app.fio, "submitted_at": app.submitted_at.strftime('%d.%m.%Y %H:%M'), "email": app.email} for app in applications], fio=fio)
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("mail_select_"))
async def mail_select_callback(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "mail"):
        return
    app_id = int(callback.data.replace("mail_select_", ""))
    data = await state.get_data()
    applications = data.get("applications", [])
    fio = data.get("fio", "")
    app = next((a for a in applications if a["id"] == app_id), None)
    if not app:
        await callback.answer("Заявление не найдено.", show_alert=True)
        return
    await state.update_data(app_id=app_id, applications=None)
    await state.set_state(MailStates.waiting_confirm)
    await callback.message.edit_text(
        f"📋 Выбрано заявление:\n\n"
        f"ФИО: {app['fio']}\n"
        f"Дата подачи: {app['submitted_at']}\n"
        f"ID: {app['id']}\n\n"
        f"Подтвердите, что документы подписаны и загружены:",
        reply_markup=mail_confirm_keyboard()
    )

@router.message(MailStates.waiting_confirm)
async def mail_confirm_process(message: Message, state: FSMContext):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    if not emp or not await has_access(str(message.from_user.id), "mail"):
        return
    data = await state.get_data()
    app_id = data.get("app_id")
    fio = data.get("fio")
    # Получаем актуальное заявление
    from db.crud import get_application_by_id
    app = await get_application_by_id(app_id)
    # Если нужны сканы — сначала спрашиваем их
    if getattr(app, 'needs_scans', False) and not getattr(app, 'scans_confirmed', False):
        await state.set_state(MailStates.waiting_scans)
        await message.answer(
            f"Требуются сканы документов. Все сканы в наличии? (да/нет)",
            reply_markup=mail_confirm_keyboard()
        )
        return
    # Если нужны только подпись — спрашиваем подпись
    if getattr(app, 'needs_signature', False) and not getattr(app, 'signature_confirmed', False):
        await state.set_state(MailStates.waiting_signature)
        await message.answer(
            f"Требуется подпись. Документы подписаны? (да/нет)",
            reply_markup=mail_confirm_keyboard()
        )
        return
    # Если ничего не требуется — принимаем
    await update_application_status(app_id, ApplicationStatusEnum.ACCEPTED, employee_id=emp.id)
    await update_application_field(app_id, "scans_confirmed", True)
    await update_application_field(app_id, "signature_confirmed", True)
    result = await increment_processed_applications(emp.id)
    logger.info(f"Заявление почты подтверждено: app_id={app_id}, increment_result={result}")
    await message.answer(
        f"✅ Заявление {app_id} ({fio}) подтверждено.\nВсе необходимые документы в наличии.",
        reply_markup=mail_menu_keyboard()
    )
    await message.bot.send_message(
        ADMIN_CHAT_ID, 
        f"📮 Почта: {message.from_user.full_name} подтвердил заявление {app_id} ({fio})"
    )
    await state.clear()

@router.message(MailStates.waiting_scans)
async def mail_scans_process(message: Message, state: FSMContext):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    data = await state.get_data()
    app_id = data.get("app_id")
    fio = data.get("fio")
    answer = message.text.strip().lower()
    if answer in ["да", "есть", "подтверждаю", "готово"]:
        await update_application_field(app_id, "scans_confirmed", True)
        # Проверяем, нужна ли подпись
        from db.crud import get_application_by_id
        app = await get_application_by_id(app_id)
        if getattr(app, 'needs_signature', False) and not getattr(app, 'signature_confirmed', False):
            await state.set_state(MailStates.waiting_signature)
            await message.answer(
                f"Требуется подпись. Документы подписаны? (да/нет)",
                reply_markup=mail_confirm_keyboard()
            )
            return
        # Если подпись не нужна — завершаем
        await update_application_status(app_id, ApplicationStatusEnum.ACCEPTED, employee_id=emp.id)
        await update_application_field(app_id, "signature_confirmed", True)
        from db.crud import increment_processed_applications
        result = await increment_processed_applications(emp.id)
        logger.info(f"Заявление почты подтверждено (сканы): app_id={app_id}, increment_result={result}")
        await message.answer(
            f"✅ Заявление {app_id} ({fio}) подтверждено.\nВсе необходимые документы в наличии.",
            reply_markup=mail_menu_keyboard()
        )
        await message.bot.send_message(
            ADMIN_CHAT_ID, 
            f"📮 Почта: {message.from_user.full_name} подтвердил заявление {app_id} ({fio}) (сканы)"
        )
        await state.clear()
    else:
        # Если сканов нет — возвращаем в очередь почты
        await update_application_field(app_id, "scans_confirmed", False)
        await return_application_to_queue(app_id)
        await message.answer(
            f"❗ Сканы не подтверждены. Заявление возвращено в очередь почты.",
            reply_markup=mail_menu_keyboard()
        )
        await state.clear()

@router.message(MailStates.waiting_signature)
async def mail_signature_process(message: Message, state: FSMContext):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    data = await state.get_data()
    app_id = data.get("app_id")
    fio = data.get("fio")
    answer = message.text.strip().lower()
    if answer in ["да", "есть", "подтверждаю", "готово"]:
        await update_application_field(app_id, "signature_confirmed", True)
        # Проверяем, нужны ли сканы и подтверждены ли они
        from db.crud import get_application_by_id
        app = await get_application_by_id(app_id)
        if getattr(app, 'needs_scans', False) and not getattr(app, 'scans_confirmed', False):
            await state.set_state(MailStates.waiting_scans)
            await message.answer(
                f"Требуются сканы документов. Все сканы в наличии? (да/нет)",
                reply_markup=mail_confirm_keyboard()
            )
            return
        # Если всё подтверждено — завершаем
        await update_application_status(app_id, ApplicationStatusEnum.ACCEPTED, employee_id=emp.id)
        result = await increment_processed_applications(emp.id)
        logger.info(f"Заявление почты подтверждено (подпись): app_id={app_id}, increment_result={result}")
        await message.answer(
            f"✅ Заявление {app_id} ({fio}) подтверждено.\nВсе необходимые документы в наличии.",
            reply_markup=mail_menu_keyboard()
        )
        await message.bot.send_message(
            ADMIN_CHAT_ID, 
            f"📮 Почта: {message.from_user.full_name} подтвердил заявление {app_id} ({fio}) (подпись)"
        )
        await state.clear()
    else:
        # Если подписи нет — возвращаем в очередь почты
        await update_application_field(app_id, "signature_confirmed", False)
        await return_application_to_queue(app_id)
        await message.answer(
            f"❗ Подпись не подтверждена. Заявление возвращено в очередь почты.",
            reply_markup=mail_menu_keyboard()
        )
        await state.clear()

@router.callback_query(F.data == "mail_back_to_menu")
async def mail_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await mail_menu_entry(callback, state)

@router.callback_query(F.data == "mail_confirm_yes")
async def mail_confirm_yes_callback(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await has_access(str(callback.from_user.id), "mail"):
        return
    data = await state.get_data()
    app_id = data.get("app_id")
    fio = data.get("fio")
    if app_id:
        await update_application_status(app_id, ApplicationStatusEnum.ACCEPTED, employee_id=emp.id)
        result = await increment_processed_applications(emp.id)
        logger.info(f"Заявление почты подтверждено (кнопка): app_id={app_id}, increment_result={result}")
        await callback.message.edit_text(
            f"✅ Заявление {app_id} ({fio}) подтверждено.\nДокументы подписаны и загружены.",
            reply_markup=mail_menu_keyboard()
        )
        
        # Логируем событие
        telegram_logger = get_logger()
        if telegram_logger:
            app = await get_application_by_id(app_id)
            if app:
                await telegram_logger.log_mail_confirmed(emp.fio, app.fio)
        
        await callback.bot.send_message(
            ADMIN_CHAT_ID,
            f"📮 Почта: {callback.from_user.full_name} подтвердил подпись заявления {app_id} ({fio})"
        )
        await state.clear()
    else:
        await callback.answer("Ошибка: не выбрано заявление.", show_alert=True)

@router.message(Command("mailinfo"))
async def mail_info_handler(message: Message):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    if not emp or not await has_access(str(message.from_user.id), "mail"):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("Используйте: /mailinfo <ФИО>")
        return
    fio = args[1].strip()
    if not fio:
        await message.answer("Пожалуйста, укажите ФИО заявителя после команды.")
        return
    # Ищем заявления по ФИО во всех очередях
    queues = ["epgu_mail", "epgu", "lk", "epgu_problem", "lk_problem"]
    found = []
    for queue in queues:
        apps = await get_applications_by_fio_and_queue(fio, queue)
        found.extend(apps)
    if not found:
        await message.answer(f"Заявления для '{fio}' не найдены ни в одной очереди.")
        return
    for app in found:
        text = f"<b>Заявление</b>\n"
        text += f"ФИО: {app.fio}\n"
        text += f"Дата подачи: {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"ID: {app.id}\n"
        text += f"Очередь: {app.queue_type}\n"
        text += f"Статус: {app.status.value if app.status else '-'}\n"
        text += f"Причина: {app.status_reason or '-'}\n"
        text += f"Подтверждено: {'да' if app.status.value == 'accepted' else 'нет'}\n"
        text += f"Комментарий: {app.problem_comment or '-'}\n"
        text += f"Ответственный: {app.problem_responsible or '-'}\n"
        await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data == "mail_info_fio")
async def mail_info_fio_start(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp:
        return
    await state.set_state(MailStates.waiting_fio_info)
    await callback.message.edit_text(
        "Введите ФИО заявителя для просмотра всей информации:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
        ])
    )

@router.message(MailStates.waiting_fio_info)
async def mail_info_fio_process(message: Message, state: FSMContext):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    if not emp:
        return
    fio = message.text.strip()
    if not fio:
        await message.answer("Пожалуйста, введите ФИО заявителя.")
        return
    queues = ["epgu_mail", "epgu", "lk", "epgu_problem", "lk_problem"]
    found = []
    for queue in queues:
        apps = await get_applications_by_fio_and_queue(fio, queue)
        found.extend(apps)
    if not found:
        await message.answer(
            f"Заявления для '{fio}' не найдены ни в одной очереди.", 
            reply_markup=mail_fio_search_keyboard()
        )
        await state.clear()
        return
    
    # Формируем один большой текст для edit_text
    text = f"<b>Заявления для '{fio}':</b>\n\n"
    for app in found:
        text += f"<b>ID:</b> {app.id}\n"
        text += f"<b>ФИО:</b> {app.fio}\n"
        text += f"<b>Дата подачи:</b> {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"<b>Очередь:</b> {app.queue_type}\n"
        text += f"<b>Статус:</b> {app.status.value if app.status else '-'}\n"
        text += f"<b>Причина:</b> {app.status_reason or '-'}\n"
        text += f"<b>Подтверждено:</b> {'да' if app.status.value == 'accepted' else 'нет'}\n"
        text += f"<b>Комментарий:</b> {app.problem_comment or '-'}\n"
        text += f"<b>Ответственный:</b> {app.problem_responsible or '-'}\n"
        text += "-----------------------------\n"
    
    # Добавляем информацию о поисковом запросе
    text += f"\n🔍 <b>Поисковый запрос:</b> '{fio}'\n"
    text += f"📊 <b>Найдено заявлений:</b> {len(found)}"
    
    await message.answer(text, parse_mode="HTML", reply_markup=mail_fio_search_keyboard())
    await state.clear() 
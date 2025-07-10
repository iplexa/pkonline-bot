from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from db.crud import (
    get_applications_by_fio_and_queue,
    update_application_status,
    get_employee_by_tg_id, 
    employee_has_group, 
    increment_processed_applications
)
from db.models import ApplicationStatusEnum
from keyboards.mail import mail_menu_keyboard, mail_search_keyboard, mail_confirm_keyboard
from keyboards.main import main_menu_keyboard
from config import ADMIN_CHAT_ID
import logging

logger = logging.getLogger(__name__)

router = Router()

class MailStates(StatesGroup):
    waiting_fio_search = State()
    waiting_confirm = State()

@router.callback_query(F.data == "mail_menu")
async def mail_menu_entry(callback: CallbackQuery, state: FSMContext):
    try:
        emp = await get_employee_by_tg_id(str(callback.from_user.id))
        if not emp or not await employee_has_group(str(callback.from_user.id), "mail"):
            return
        await callback.message.edit_text(
            "📮 Очередь почты. Здесь подтверждается подпись документов.\n\n"
            "Нажмите кнопку для поиска заявления по ФИО.",
            reply_markup=mail_menu_keyboard()
        )
    except Exception as e:
        await callback.message.answer(f"Ошибка: {e}")
        import traceback
        print(traceback.format_exc())

@router.callback_query(F.data == "mail_search_fio")
async def mail_search_fio_start(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await employee_has_group(str(callback.from_user.id), "mail"):
        return
    await state.set_state(MailStates.waiting_fio_search)
    await callback.message.edit_text(
        "Введите ФИО заявителя для поиска заявления в очереди почты:",
        reply_markup=mail_search_keyboard()
    )

@router.message(MailStates.waiting_fio_search)
async def mail_search_fio_process(message: Message, state: FSMContext):
    emp = await get_employee_by_tg_id(str(message.from_user.id))
    if not emp or not await employee_has_group(str(message.from_user.id), "mail"):
        return
    fio = message.text.strip()
    if not fio:
        await message.answer("Пожалуйста, введите ФИО заявителя.")
        return
    applications = await get_applications_by_fio_and_queue(fio, "epgu_mail")
    if not applications:
        await message.answer(
            f"Заявления для '{fio}' в очереди почты не найдены.",
            reply_markup=mail_menu_keyboard()
        )
        await state.clear()
        return
    if len(applications) == 1:
        app = applications[0]
        await state.update_data(app_id=app.id, fio=fio)
        await state.set_state(MailStates.waiting_confirm)
        await message.answer(
            f"📋 Найдено заявление:\n\n"
            f"ФИО: {app.fio}\n"
            f"Дата подачи: {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"ID: {app.id}\n\n"
            f"Подтвердите, что документы подписаны и загружены:",
            reply_markup=mail_confirm_keyboard()
        )
    else:
        # Несколько заявлений - показываем кнопки для выбора
        text = f"📋 Найдено {len(applications)} заявлений для '{fio}':\n\nВыберите нужное заявление:" 
        keyboard = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=f"{i+1}. {app.submitted_at.strftime('%d.%m.%Y %H:%M')}", callback_data=f"mail_select_{app.id}")]
                for i, app in enumerate(applications)
            ] + [[InlineKeyboardButton(text="🔙 Назад", callback_data="mail_back_to_menu")]]
        )
        await state.update_data(applications=[{"id": app.id, "fio": app.fio, "submitted_at": app.submitted_at.strftime('%d.%m.%Y %H:%M')} for app in applications], fio=fio)
        await message.answer(text, reply_markup=keyboard)

@router.callback_query(F.data.startswith("mail_select_"))
async def mail_select_callback(callback: CallbackQuery, state: FSMContext):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp or not await employee_has_group(str(callback.from_user.id), "mail"):
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
    if not emp or not await employee_has_group(str(message.from_user.id), "mail"):
        return
    
    data = await state.get_data()
    app_id = data.get("app_id")
    applications = data.get("applications")
    fio = data.get("fio")
    
    if app_id:
        # Одно заявление - подтверждаем
        if message.text.lower() in ["да", "подтвердить", "подтверждаю", "готово"]:
            await update_application_status(app_id, ApplicationStatusEnum.ACCEPTED, employee_id=emp.id)
            result = await increment_processed_applications(emp.id)
            logger.info(f"Заявление почты подтверждено: app_id={app_id}, increment_result={result}")
            await message.answer(
                f"✅ Заявление {app_id} ({fio}) подтверждено.\n"
                f"Документы подписаны и загружены.",
                reply_markup=mail_menu_keyboard()
            )
            await message.bot.send_message(
                ADMIN_CHAT_ID, 
                f"📮 Почта: {message.from_user.full_name} подтвердил подпись заявления {app_id} ({fio})"
            )
        else:
            await message.answer(
                "Отмена подтверждения. Заявление осталось в очереди почты.",
                reply_markup=mail_menu_keyboard()
            )
        await state.clear()
    elif applications:
        # Несколько заявлений - выбираем по номеру
        try:
            choice = int(message.text.strip())
            if 1 <= choice <= len(applications):
                app = applications[choice - 1]
                await state.update_data(app_id=app.id, applications=None)
                await message.answer(
                    f"📋 Выбрано заявление:\n\n"
                    f"ФИО: {app.fio}\n"
                    f"Дата подачи: {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"ID: {app.id}\n\n"
                    f"Подтвердите, что документы подписаны и загружены:",
                    reply_markup=mail_confirm_keyboard()
                )
            else:
                await message.answer(
                    f"Неверный номер. Введите число от 1 до {len(applications)}.",
                    reply_markup=mail_search_keyboard()
                )
        except ValueError:
            await message.answer(
                "Пожалуйста, введите номер заявления (число).",
                reply_markup=mail_search_keyboard()
            )

@router.callback_query(F.data == "mail_back_to_menu")
async def mail_back_to_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await mail_menu_entry(callback, state) 
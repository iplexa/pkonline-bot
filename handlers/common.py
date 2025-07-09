from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from db.crud import get_employee_by_tg_id, start_work_day, end_work_day, start_break, end_break, get_current_work_day, get_work_day_report, get_moscow_now
from keyboards.main import main_menu_keyboard
from keyboards.work_time import work_time_keyboard, work_status_keyboard
from datetime import datetime

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
        reply_markup=main_menu_keyboard(is_admin=is_admin, groups=groups, with_menu_button=False)
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
        reply_markup=main_menu_keyboard(is_admin=is_admin, groups=groups, with_menu_button=False)
    )

@router.callback_query(F.data == "work_time_menu")
async def work_time_menu(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp:
        return
    
    current_work_day = await get_current_work_day(emp.id)
    if current_work_day:
        # Показываем статус текущего рабочего дня
        status_text = "🟢 Рабочий день активен"
        if current_work_day.status.value == "paused":
            status_text = "🟡 Рабочий день приостановлен"
        elif current_work_day.status.value == "finished":
            status_text = "🔴 Рабочий день завершен"
        
        # Рассчитываем текущее время работы
        current_time = get_moscow_now()
        total_work_seconds = current_work_day.total_work_time
        total_break_seconds = current_work_day.total_break_time
        
        # Если рабочий день активен и не завершен, добавляем текущее время
        if current_work_day.status.value == "active" and not current_work_day.end_time:
            if current_work_day.start_time:
                elapsed_seconds = int((current_time - current_work_day.start_time).total_seconds())
                total_work_seconds = elapsed_seconds - total_break_seconds
        
        work_time_str = f"{total_work_seconds // 3600:02d}:{(total_work_seconds % 3600) // 60:02d}"
        break_time_str = f"{total_break_seconds // 3600:02d}:{(total_break_seconds % 3600) // 60:02d}"
        
        message_text = f"{status_text}\n\n"
        message_text += f"Начало: {current_work_day.start_time.strftime('%H:%M')}\n"
        if current_work_day.end_time:
            message_text += f"Окончание: {current_work_day.end_time.strftime('%H:%M')}\n"
        message_text += f"Время работы: {work_time_str}\n"
        message_text += f"Время перерывов: {break_time_str}\n"
        message_text += f"Обработано заявлений: {current_work_day.applications_processed}"
        
        await callback.message.edit_text(message_text, reply_markup=work_status_keyboard(current_work_day.status.value))
    else:
        await callback.message.edit_text(
            "Рабочий день не начат. Нажмите кнопку, чтобы начать рабочий день.",
            reply_markup=work_time_keyboard()
        )

@router.callback_query(F.data == "start_work_day")
async def start_work_day_handler(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp:
        return
    
    work_day = await start_work_day(emp.id)
    if work_day:
        await callback.message.edit_text(
            f"✅ Рабочий день начат в {work_day.start_time.strftime('%H:%M')}",
            reply_markup=work_status_keyboard(work_day.status.value)
        )
    else:
        await callback.answer("Рабочий день уже начат!", show_alert=True)

@router.callback_query(F.data == "end_work_day")
async def end_work_day_handler(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp:
        return
    
    work_day = await end_work_day(emp.id)
    if work_day:
        work_time_str = f"{work_day.total_work_time // 3600:02d}:{(work_day.total_work_time % 3600) // 60:02d}"
        break_time_str = f"{work_day.total_break_time // 3600:02d}:{(work_day.total_break_time % 3600) // 60:02d}"
        
        message_text = f"🔴 Рабочий день завершен\n\n"
        message_text += f"Начало: {work_day.start_time.strftime('%H:%M')}\n"
        message_text += f"Окончание: {work_day.end_time.strftime('%H:%M')}\n"
        message_text += f"Время работы: {work_time_str}\n"
        message_text += f"Время перерывов: {break_time_str}\n"
        message_text += f"Обработано заявлений: {work_day.applications_processed}"
        
        await callback.message.edit_text(message_text, reply_markup=work_time_keyboard())
    else:
        await callback.answer("Рабочий день не найден!", show_alert=True)

@router.callback_query(F.data == "start_break")
async def start_break_handler(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp:
        return
    
    work_break = await start_break(emp.id)
    if work_break:
        await callback.message.edit_text(
            f"☕ Перерыв начат в {work_break.start_time.strftime('%H:%M')}",
            reply_markup=work_status_keyboard("paused")
        )
    else:
        await callback.answer("Не удалось начать перерыв!", show_alert=True)

@router.callback_query(F.data == "end_break")
async def end_break_handler(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp:
        return
    
    work_break = await end_break(emp.id)
    if work_break:
        break_duration = work_break.duration // 60  # в минутах
        await callback.message.edit_text(
            f"✅ Перерыв завершен. Продолжительность: {break_duration} мин.",
            reply_markup=work_status_keyboard("active")
        )
    else:
        await callback.answer("Активный перерыв не найден!", show_alert=True)

@router.callback_query(F.data == "work_report")
async def work_report_handler(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp:
        return
    
    report = await get_work_day_report(emp.id)
    if report:
        work_time_str = f"{report['total_work_time'] // 3600:02d}:{(report['total_work_time'] % 3600) // 60:02d}"
        break_time_str = f"{report['total_break_time'] // 3600:02d}:{(report['total_break_time'] % 3600) // 60:02d}"
        
        message_text = f"📊 Отчет за {report['date'].strftime('%d.%m.%Y')}\n\n"
        if report['start_time']:
            message_text += f"Начало: {report['start_time'].strftime('%H:%M')}\n"
        if report['end_time']:
            message_text += f"Окончание: {report['end_time'].strftime('%H:%M')}\n"
        message_text += f"Время работы: {work_time_str}\n"
        message_text += f"Время перерывов: {break_time_str}\n"
        message_text += f"Обработано заявлений: {report['applications_processed']}\n"
        
        if report['breaks']:
            message_text += "\nПерерывы:\n"
            for i, break_item in enumerate(report['breaks'], 1):
                start_time = break_item['start_time'].strftime('%H:%M')
                if break_item['end_time']:
                    end_time = break_item['end_time'].strftime('%H:%M')
                    duration = break_item['duration'] // 60
                    message_text += f"{i}. {start_time} - {end_time} ({duration} мин)\n"
                else:
                    message_text += f"{i}. {start_time} - активен\n"
        
        await callback.message.edit_text(message_text, reply_markup=work_time_keyboard())
    else:
        await callback.message.edit_text(
            "Отчет за сегодня не найден.",
            reply_markup=work_time_keyboard()
        )

@router.callback_query(F.data == "epgu_menu")
async def epgu_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "Очередь ЕПГУ: функция в разработке.",
        reply_markup=main_menu_keyboard(with_menu_button=True)
    )

@router.callback_query(F.data == "escalation_menu")
async def escalation_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "Эскалация: функция в разработке.",
        reply_markup=main_menu_keyboard(with_menu_button=True)
    ) 
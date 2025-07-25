from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.exceptions import TelegramNetworkError, TelegramAPIError
from db.crud import get_employee_by_tg_id, start_work_day, end_work_day, start_break, end_break, get_current_work_day, get_work_day_report, get_moscow_now, get_active_break
from keyboards.main import main_menu_keyboard
from keyboards.work_time import work_time_keyboard, work_status_keyboard
from datetime import datetime
from utils.logger import get_logger
import asyncio
import aiohttp

router = Router()

async def clear_web_cache():
    """Очистить кэш веб-интерфейса"""
    try:
        # Асинхронно очищаем кэш веб-интерфейса
        async with aiohttp.ClientSession() as session:
            # Получаем токен из переменной окружения или конфигурации
            # Для простоты используем базовую аутентификацию или пропускаем
            async with session.post('http://localhost:8000/dashboard/employees/status/refresh') as response:
                if response.status == 200:
                    print("Web cache cleared successfully")
                else:
                    print(f"Failed to clear web cache: {response.status}")
    except Exception as e:
        print(f"Error clearing web cache: {e}")

async def safe_edit_message(callback: CallbackQuery, text: str, reply_markup=None, parse_mode=None):
    """Безопасное редактирование сообщения с обработкой таймаутов"""
    try:
        await asyncio.wait_for(
            callback.message.edit_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            ),
            timeout=15.0
        )
        return True
    except asyncio.TimeoutError:
        print(f"Таймаут при редактировании сообщения для пользователя {callback.from_user.id}")
        return False
    except TelegramNetworkError as e:
        print(f"Сетевая ошибка при редактировании сообщения: {e}")
        return False
    except TelegramAPIError as e:
        print(f"Ошибка API при редактировании сообщения: {e}")
        return False
    except Exception as e:
        print(f"Ошибка при редактировании сообщения: {e}")
        return False

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
        # Проверяем, есть ли активный перерыв
        active_break = await get_active_break(current_work_day.id)
        
        # Определяем статус для отображения
        display_status = current_work_day.status.value
        if active_break and current_work_day.status.value == "active":
            display_status = "paused"  # Если есть активный перерыв, показываем как приостановленный
        
        # Показываем статус текущего рабочего дня
        status_text = "🟢 Рабочий день активен"
        if display_status == "paused":
            status_text = "🟡 Рабочий день приостановлен (перерыв)"
        elif display_status == "finished":
            status_text = "🔴 Рабочий день завершен"
        
        # Рассчитываем текущее время работы и перерыва
        current_time = get_moscow_now()
        total_work_seconds = current_work_day.total_work_time
        total_break_seconds = current_work_day.total_break_time

        # Если есть активный перерыв, добавляем его длительность к total_break_seconds
        if active_break and active_break.start_time and not active_break.end_time:
            total_break_seconds += int((current_time - active_break.start_time).total_seconds())

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
        
        await safe_edit_message(callback, message_text, reply_markup=work_status_keyboard(display_status))
    else:
        await safe_edit_message(
            callback,
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
        # Логируем событие
        telegram_logger = get_logger()
        if telegram_logger:
            await telegram_logger.log_work_time_start(emp.fio, work_day.start_time.strftime('%H:%M'))
        
        # Очищаем кэш веб-интерфейса
        await clear_web_cache()
        
        await callback.message.edit_text(
            f"✅ Рабочий день начат в {work_day.start_time.strftime('%H:%M')}",
            reply_markup=work_status_keyboard(work_day.status.value)
        )
    else:
        await callback.answer("Рабочий день уже начат!", show_alert=True)

@router.callback_query(F.data == "confirm_end_work_day")
async def confirm_end_work_day_handler(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp:
        return
    
    # Проверяем, есть ли активный рабочий день
    current_work_day = await get_current_work_day(emp.id)
    if not current_work_day or current_work_day.end_time:
        await callback.answer("Нет активного рабочего дня!")
        return
    
    # Показываем подтверждение
    from keyboards.work_time import confirm_end_work_day_keyboard
    await callback.message.edit_text(
        "⚠️ Вы точно хотите завершить рабочий день?\n\n"
        "После завершения нельзя будет начать новый рабочий день в этот же день.",
        reply_markup=confirm_end_work_day_keyboard()
    )

@router.callback_query(F.data == "cancel_end_work_day")
async def cancel_end_work_day_handler(callback: CallbackQuery):
    emp = await get_employee_by_tg_id(str(callback.from_user.id))
    if not emp:
        return
    
    # Возвращаемся к статусу рабочего дня
    current_work_day = await get_current_work_day(emp.id)
    if current_work_day:
        # Проверяем, есть ли активный перерыв
        active_break = await get_active_break(current_work_day.id)
        
        # Определяем статус для отображения
        display_status = current_work_day.status.value
        if active_break and current_work_day.status.value == "active":
            display_status = "paused"
        
        # Показываем статус текущего рабочего дня
        status_text = "🟢 Рабочий день активен"
        if display_status == "paused":
            status_text = "🟡 Рабочий день приостановлен (перерыв)"
        elif display_status == "finished":
            status_text = "🔴 Рабочий день завершен"
        
        # Рассчитываем текущее время работы и перерыва
        current_time = get_moscow_now()
        total_work_seconds = current_work_day.total_work_time
        total_break_seconds = current_work_day.total_break_time

        # Если есть активный перерыв, добавляем его длительность к total_break_seconds
        if active_break and active_break.start_time and not active_break.end_time:
            total_break_seconds += int((current_time - active_break.start_time).total_seconds())

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
        
        await safe_edit_message(callback, message_text, reply_markup=work_status_keyboard(display_status))
    else:
        await safe_edit_message(
            callback,
            "Рабочий день не начат. Нажмите кнопку, чтобы начать рабочий день.",
            reply_markup=work_time_keyboard()
        )

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
        
        # Логируем событие
        telegram_logger = get_logger()
        if telegram_logger:
            await telegram_logger.log_work_time_end(emp.fio, work_day.end_time.strftime('%H:%M'), work_time_str)
        
        # Очищаем кэш веб-интерфейса
        await clear_web_cache()
        
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
        # Показываем обновленный статус рабочего дня
        current_work_day = await get_current_work_day(emp.id)
        active_break = await get_active_break(current_work_day.id)
        display_status = current_work_day.status.value
        if active_break and current_work_day.status.value == "active":
            display_status = "paused"
        current_time = get_moscow_now()
        total_work_seconds = current_work_day.total_work_time
        total_break_seconds = current_work_day.total_break_time

        # Если есть активный перерыв, добавляем его длительность к total_break_seconds
        if active_break and active_break.start_time and not active_break.end_time:
            total_break_seconds += int((current_time - active_break.start_time).total_seconds())

        # Если рабочий день активен и не завершен, добавляем текущее время
        if current_work_day.status.value == "active" and not current_work_day.end_time:
            if current_work_day.start_time:
                elapsed_seconds = int((current_time - current_work_day.start_time).total_seconds())
                total_work_seconds = elapsed_seconds - total_break_seconds
        work_time_str = f"{total_work_seconds // 3600:02d}:{(total_work_seconds % 3600) // 60:02d}"
        break_time_str = f"{total_break_seconds // 3600:02d}:{(total_break_seconds % 3600) // 60:02d}"
        message_text = f"🟡 Рабочий день приостановлен (перерыв)\n\n"
        message_text += f"Начало: {current_work_day.start_time.strftime('%H:%M')}\n"
        message_text += f"Время работы: {work_time_str}\n"
        message_text += f"Время перерывов: {break_time_str}\n"
        message_text += f"Обработано заявлений: {current_work_day.applications_processed}"
        
        # Логируем событие
        telegram_logger = get_logger()
        if telegram_logger:
            await telegram_logger.log_break_start(emp.fio, work_break.start_time.strftime('%H:%M'))
        
        # Очищаем кэш веб-интерфейса
        await clear_web_cache()
        
        await callback.message.edit_text(message_text, reply_markup=work_status_keyboard(display_status))
    else:
        await callback.answer("Не удалось начать перерыв!", show_alert=True)

@router.callback_query(F.data == "end_break")
async def end_break_handler(callback: CallbackQuery):
    try:
        emp = await get_employee_by_tg_id(str(callback.from_user.id))
        if not emp:
            print("[end_break_handler] Нет сотрудника")
            return
        work_break = await end_break(emp.id)
        print(f"[end_break_handler] work_break: {work_break}")
        if work_break:
            # Показываем обновленный статус рабочего дня
            current_work_day = await get_current_work_day(emp.id)
            active_break = await get_active_break(current_work_day.id)
            display_status = current_work_day.status.value
            current_time = get_moscow_now()
            total_work_seconds = current_work_day.total_work_time
            total_break_seconds = current_work_day.total_break_time

            # Если есть активный перерыв, добавляем его длительность к total_break_seconds
            if active_break and active_break.start_time and not active_break.end_time:
                total_break_seconds += int((current_time - active_break.start_time).total_seconds())

            # Если рабочий день активен и не завершен, добавляем текущее время
            if current_work_day.status.value == "active" and not current_work_day.end_time:
                if current_work_day.start_time:
                    elapsed_seconds = int((current_time - current_work_day.start_time).total_seconds())
                    total_work_seconds = elapsed_seconds - total_break_seconds
            work_time_str = f"{total_work_seconds // 3600:02d}:{(total_work_seconds % 3600) // 60:02d}"
            break_time_str = f"{total_break_seconds // 3600:02d}:{(total_break_seconds % 3600) // 60:02d}"
            
            # Очищаем кэш веб-интерфейса
            await clear_web_cache()
            message_text = f"🟢 Рабочий день активен\n\n"
            message_text += f"Начало: {current_work_day.start_time.strftime('%H:%M')}\n"
            message_text += f"Время работы: {work_time_str}\n"
            message_text += f"Время перерывов: {break_time_str}\n"
            message_text += f"Обработано заявлений: {current_work_day.applications_processed}"
            
            # Логируем событие
            telegram_logger = get_logger()
            if telegram_logger:
                await telegram_logger.log_break_end(emp.fio, work_break.end_time.strftime('%H:%M'))
            
            print(f"[end_break_handler] message_text: {message_text}")
            await callback.message.edit_text(message_text, reply_markup=work_status_keyboard(display_status))
        else:
            print("[end_break_handler] Активный перерыв не найден!")
            await callback.answer("Активный перерыв не найден!", show_alert=True)
    except Exception as e:
        import traceback
        print(f"[end_break_handler] Exception: {e}\n{traceback.format_exc()}")
        await callback.answer(f"Ошибка: {e}", show_alert=True)

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

@router.callback_query(F.data == "escalation_menu")
async def escalation_menu_callback(callback: CallbackQuery):
    await callback.message.edit_text(
        "Эскалация: функция в разработке.",
        reply_markup=main_menu_keyboard(with_menu_button=True)
    ) 
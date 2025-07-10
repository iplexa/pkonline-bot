from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.crud import (
    add_employee, remove_employee, add_group_to_employee, remove_group_from_employee, list_employees_with_groups, is_admin, get_employee_by_tg_id, get_applications_by_queue_type, clear_queue_by_type, import_applications_from_excel, get_all_work_days_report,
    get_applications_statistics_by_queue
)
from keyboards.admin import admin_main_menu_keyboard, admin_staff_menu_keyboard, admin_queue_menu_keyboard, admin_queue_type_keyboard, admin_queue_pagination_keyboard, group_choice_keyboard, admin_reports_menu_keyboard
from keyboards.main import main_menu_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from db.crud import Application, ApplicationStatusEnum
from datetime import date, datetime
import logging
import os
import tempfile

router = Router()

class AdminStates(StatesGroup):
    waiting_tg_id = State()
    waiting_fio = State()
    waiting_tg_id_remove = State()
    waiting_tg_id_group = State()
    waiting_group_add = State()
    waiting_group_remove = State()

class AdminQueueStates(StatesGroup):
    waiting_action = State()
    waiting_queue_type = State()
    waiting_upload_file = State()
    waiting_clear_confirm = State()

QUEUE_PAGE_SIZE = 20

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
    await callback.message.edit_text("Админ-меню:", reply_markup=admin_main_menu_keyboard())

@router.callback_query(F.data == "admin_staff_menu")
async def admin_staff_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Управление сотрудниками:", reply_markup=admin_staff_menu_keyboard())

@router.callback_query(F.data == "admin_queue_menu")
async def admin_queue_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Управление очередями:", reply_markup=admin_queue_menu_keyboard())

@router.callback_query(F.data == "admin_add_employee")
async def admin_add_employee(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_tg_id)
    await callback.message.edit_text("Введите Telegram ID нового сотрудника:", reply_markup=cancel_keyboard)

@router.message(AdminStates.waiting_tg_id)
async def admin_add_employee_tg_id(message: Message, state: FSMContext):
    if message.text.strip().lower() == "отмена":
        await state.clear()
        await message.answer("Добавление отменено.", reply_markup=admin_staff_menu_keyboard())
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
        await message.answer("Добавление отменено.", reply_markup=admin_staff_menu_keyboard())
        return
    data = await state.get_data()
    tg_id = data.get("tg_id")
    fio = message.text.strip()
    try:
        await add_employee(tg_id, fio)
        await message.answer(f"Сотрудник {fio} ({tg_id}) добавлен.", reply_markup=admin_staff_menu_keyboard())
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
        await message.answer("Удаление отменено.", reply_markup=admin_staff_menu_keyboard())
        return
    tg_id = message.text.strip()
    emp = await get_employee_by_tg_id(tg_id)
    if not emp:
        await message.answer("Сотрудник с таким Telegram ID не найден!", reply_markup=cancel_keyboard)
        return
    try:
        await remove_employee(tg_id)
        await message.answer(f"Сотрудник {tg_id} удалён.", reply_markup=admin_staff_menu_keyboard())
    except Exception as e:
        await message.answer(f"Ошибка при удалении: {e}", reply_markup=cancel_keyboard)
    await state.clear()

@router.callback_query(F.data == "admin_add_group")
async def admin_add_group(callback: CallbackQuery, state: FSMContext):
    emps = await list_employees_with_groups()
    if not emps:
        await callback.message.edit_text("Нет сотрудников для назначения группы.", reply_markup=admin_staff_menu_keyboard())
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
        await callback.message.edit_text("Сотрудник не найден!", reply_markup=admin_staff_menu_keyboard())
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
        await callback.message.edit_text("Сотрудник не найден!", reply_markup=admin_staff_menu_keyboard())
        await state.clear()
        return
    if group in [g.name for g in emp.groups]:
        await callback.message.edit_text(f"У сотрудника уже есть группа {group}.", reply_markup=admin_staff_menu_keyboard())
        await state.clear()
        return
    try:
        result = await add_group_to_employee(tg_id, group)
        if not result:
            await callback.message.edit_text(f"Не удалось добавить группу {group} сотруднику {tg_id}.", reply_markup=admin_staff_menu_keyboard())
        else:
            await callback.message.edit_text(f"Группа {group} добавлена сотруднику {tg_id}.", reply_markup=admin_staff_menu_keyboard())
    except Exception as e:
        await callback.message.edit_text(f"Ошибка при добавлении группы: {e}", reply_markup=admin_staff_menu_keyboard())
    await state.clear()

@router.callback_query(F.data == "admin_remove_group")
async def admin_remove_group(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminStates.waiting_tg_id_group)
    await callback.message.edit_text("Введите Telegram ID сотрудника для удаления группы:", reply_markup=cancel_keyboard)

@router.message(AdminStates.waiting_tg_id_group)
async def admin_remove_group_tg_id(message: Message, state: FSMContext):
    if message.text.strip().lower() == "отмена":
        await state.clear()
        await message.answer("Удаление группы отменено.", reply_markup=admin_staff_menu_keyboard())
        return
    tg_id = message.text.strip()
    emp = await get_employee_by_tg_id(tg_id)
    if not emp:
        await message.answer("Сотрудник с таким Telegram ID не найден!", reply_markup=cancel_keyboard)
        return
    groups = [g.name for g in emp.groups] if emp.groups else []
    if not groups:
        await message.answer("У сотрудника нет групп для удаления.", reply_markup=admin_staff_menu_keyboard())
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
        await callback.message.edit_text("Сотрудник не найден!", reply_markup=admin_staff_menu_keyboard())
        await state.clear()
        return
    if group not in [g.name for g in emp.groups]:
        await callback.message.edit_text(f"У сотрудника нет группы {group}.", reply_markup=admin_staff_menu_keyboard())
        await state.clear()
        return
    try:
        await remove_group_from_employee(tg_id, group)
        await callback.message.edit_text(f"Группа {group} удалена у сотрудника {tg_id}.", reply_markup=admin_staff_menu_keyboard())
    except Exception as e:
        await callback.message.edit_text(f"Ошибка при удалении группы: {e}", reply_markup=admin_staff_menu_keyboard())
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
    await callback.message.edit_text(text, reply_markup=admin_staff_menu_keyboard(), parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data == "admin_view_queue")
async def admin_view_queue(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminQueueStates.waiting_queue_type)
    await state.update_data(queue_action="view")
    await callback.message.edit_text("Выберите тип очереди для просмотра:", reply_markup=admin_queue_type_keyboard())

@router.callback_query(F.data == "admin_clear_queue")
async def admin_clear_queue(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminQueueStates.waiting_queue_type)
    await state.update_data(queue_action="clear")
    await callback.message.edit_text("Выберите тип очереди для очистки:", reply_markup=admin_queue_type_keyboard())

@router.callback_query(F.data == "admin_upload_queue")
async def admin_upload_queue(callback: CallbackQuery, state: FSMContext):
    await state.set_state(AdminQueueStates.waiting_queue_type)
    await state.update_data(queue_action="upload")
    await callback.message.edit_text("Выберите тип очереди для загрузки заявлений:", reply_markup=admin_queue_type_keyboard())

@router.callback_query(AdminQueueStates.waiting_queue_type, F.data.startswith("admin_queue_type_"))
async def admin_queue_type_action(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    action = data.get("queue_action")
    queue_type = callback.data.replace("admin_queue_type_", "")
    await state.update_data(queue_type=queue_type)
    if action == "view":
        await state.update_data(queue_page=1)
        await show_queue_page(callback, state, queue_type, 1)
    elif action == "clear":
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Да, очистить", callback_data="admin_confirm_clear_queue")],
            [InlineKeyboardButton(text="Отмена", callback_data="admin_queue_menu")],
        ])
        await state.set_state(AdminQueueStates.waiting_clear_confirm)
        await callback.message.edit_text(f"Вы уверены, что хотите очистить очередь {queue_type}?", reply_markup=kb)
    elif action == "upload":
        await state.set_state(AdminQueueStates.waiting_upload_file)
        await callback.message.edit_text(f"Отправьте Excel-файл для загрузки заявлений в очередь {queue_type}.", reply_markup=admin_queue_menu_keyboard())

@router.callback_query(F.data.startswith("admin_queue_page_"))
async def admin_queue_page(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    # Ожидаем callback_data вида 'admin_queue_page_{queue_type}_{page}'
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.message.edit_text("Ошибка: некорректный формат страницы. Возвращаю в меню.", reply_markup=admin_queue_menu_keyboard())
        await state.clear()
        return
    queue_type = parts[3]
    try:
        page = int(parts[4])
    except (IndexError, ValueError):
        await callback.message.edit_text("Ошибка: некорректный номер страницы. Возвращаю в меню.", reply_markup=admin_queue_menu_keyboard())
        await state.clear()
        return
    await state.update_data(queue_type=queue_type, queue_page=page)
    await show_queue_page(callback, state, queue_type, page)

async def show_queue_page(callback, state, queue_type, page):
    apps = await get_applications_by_queue_type(queue_type)
    total = len(apps)
    total_pages = max(1, (total + QUEUE_PAGE_SIZE - 1) // QUEUE_PAGE_SIZE)
    start = (page - 1) * QUEUE_PAGE_SIZE
    end = start + QUEUE_PAGE_SIZE
    page_apps = apps[start:end]
    if not page_apps:
        text = f"Очередь {queue_type} пуста."
    else:
        text = f"Очередь {queue_type} (стр. {page}/{total_pages}):\n"
        for app in page_apps:
            text += f"\n<b>{app.fio}</b> | {app.submitted_at.strftime('%Y-%m-%d %H:%M')} | {app.status.value}"
    await callback.message.edit_text(text, reply_markup=admin_queue_pagination_keyboard(queue_type, page, total_pages), parse_mode="HTML")

@router.callback_query(AdminQueueStates.waiting_clear_confirm, F.data == "admin_confirm_clear_queue")
async def admin_confirm_clear_queue(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    queue_type = data.get("queue_type")
    await clear_queue_by_type(queue_type)
    await callback.message.edit_text(f"Очередь {queue_type} очищена!", reply_markup=admin_queue_menu_keyboard())
    await state.clear()

@router.message(AdminQueueStates.waiting_upload_file)
async def admin_upload_queue_file(message: Message, state: FSMContext):
    data = await state.get_data()
    queue_type = data.get("queue_type")
    if not message.document:
        await message.answer("Пожалуйста, отправьте Excel-файл.")
        return
    progress_msg = await message.answer("Документ получен. Начинаю скачивание...")
    try:
        file = await message.bot.download(message.document)
        import os
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            tmp.write(file.getvalue())
            tmp_path = tmp.name
        from db.crud import import_applications_from_excel
        result = await import_applications_from_excel(tmp_path, queue_type)
        os.unlink(tmp_path)
        # result может быть None, но мы можем получить данные из логов, либо возвращать из функции
        # Для пользователя выводим сколько добавлено, пропущено, всего строк
        # Для этого возвращаем из import_applications_from_excel кортеж (added, skipped, total)
        if isinstance(result, dict):
            added = result.get('added', '?')
            skipped = result.get('skipped', '?')
            total = result.get('total', '?')
        elif isinstance(result, tuple) and len(result) == 3:
            added, skipped, total = result
        else:
            added = skipped = total = '?'
        await progress_msg.edit_text(
            f"Импорт завершён для очереди: {queue_type}.\n"
            f"Всего строк: {total}\n"
            f"Добавлено: {added}\n"
            f"Пропущено: {skipped}",
            reply_markup=admin_queue_menu_keyboard()
        )
    except Exception as e:
        import traceback
        await progress_msg.edit_text(f"Ошибка при обработке файла: {e}\n{traceback.format_exc()[:1000]}", reply_markup=admin_queue_menu_keyboard())
    await state.clear()

@router.callback_query(F.data == "admin_queue_menu")
async def admin_queue_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Управление очередями:", reply_markup=admin_queue_menu_keyboard())

@router.callback_query(F.data == "admin_reports_menu")
async def admin_reports_menu(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text("Отчеты:", reply_markup=admin_reports_menu_keyboard())

@router.callback_query(F.data == "admin_full_report")
async def admin_full_report(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    # Получаем отчет за сегодня
    reports = await get_all_work_days_report()
    
    if not reports:
        await callback.message.edit_text(
            "Нет данных за сегодня.",
            reply_markup=admin_reports_menu_keyboard()
        )
        return
    
    # Формируем полный отчет
    report_text = f"📊 ПОЛНЫЙ ОТЧЕТ за {date.today().strftime('%d.%m.%Y')}\n\n"
    
    total_applications = 0
    total_work_time = 0
    total_break_time = 0
    
    for report in reports:
        work_time_str = f"{report['total_work_time'] // 3600:02d}:{(report['total_work_time'] % 3600) // 60:02d}"
        break_time_str = f"{report['total_break_time'] // 3600:02d}:{(report['total_break_time'] % 3600) // 60:02d}"
        
        report_text += f"👤 {report['employee_fio']}\n"
        if report['start_time']:
            report_text += f"   Начало: {report['start_time'].strftime('%H:%M')}\n"
        if report['end_time']:
            report_text += f"   Окончание: {report['end_time'].strftime('%H:%M')}\n"
        report_text += f"   Время работы: {work_time_str}\n"
        report_text += f"   Время перерывов: {break_time_str}\n"
        report_text += f"   Заявлений: {report['applications_processed']}\n"
        
        if report['breaks']:
            report_text += "   Перерывы:\n"
            for i, break_item in enumerate(report['breaks'], 1):
                start_time = break_item['start_time'].strftime('%H:%M')
                if break_item['end_time']:
                    end_time = break_item['end_time'].strftime('%H:%M')
                    duration = break_item['duration'] // 60
                    report_text += f"     {i}. {start_time} - {end_time} ({duration} мин)\n"
                else:
                    report_text += f"     {i}. {start_time} - активен\n"
        
        report_text += "\n"
        
        total_applications += report['applications_processed']
        total_work_time += report['total_work_time']
        total_break_time += report['total_break_time']
    
    # Итоги
    total_work_time_str = f"{total_work_time // 3600:02d}:{(total_work_time % 3600) // 60:02d}"
    total_break_time_str = f"{total_break_time // 3600:02d}:{(total_break_time % 3600) // 60:02d}"
    
    report_text += f"📈 ИТОГО:\n"
    report_text += f"   Обработано заявлений: {total_applications}\n"
    report_text += f"   Общее время работы: {total_work_time_str}\n"
    report_text += f"   Общее время перерывов: {total_break_time_str}\n"
    
    # Разбиваем на части, если отчет слишком длинный
    if len(report_text) > 4000:
        parts = [report_text[i:i+4000] for i in range(0, len(report_text), 4000)]
        for i, part in enumerate(parts):
            if i == 0:
                await callback.message.edit_text(part)
            else:
                await callback.message.answer(part)
        await callback.message.answer("Отчет завершен.", reply_markup=admin_reports_menu_keyboard())
    else:
        await callback.message.edit_text(report_text, reply_markup=admin_reports_menu_keyboard())

@router.callback_query(F.data == "admin_work_time_report")
async def admin_work_time_report(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    # Получаем отчет за сегодня
    reports = await get_all_work_days_report()
    
    if not reports:
        await callback.message.edit_text(
            "Нет данных о рабочем времени за сегодня.",
            reply_markup=admin_reports_menu_keyboard()
        )
        return
    
    # Формируем отчет только по рабочему времени
    report_text = f"⏰ ОТЧЕТ ПО РАБОЧЕМУ ВРЕМЕНИ за {date.today().strftime('%d.%m.%Y')}\n\n"
    
    total_work_time = 0
    total_break_time = 0
    
    for report in reports:
        work_time_str = f"{report['total_work_time'] // 3600:02d}:{(report['total_work_time'] % 3600) // 60:02d}"
        break_time_str = f"{report['total_break_time'] // 3600:02d}:{(report['total_break_time'] % 3600) // 60:02d}"
        
        report_text += f"👤 {report['employee_fio']}\n"
        if report['start_time']:
            report_text += f"   Начало: {report['start_time'].strftime('%H:%M')}\n"
        if report['end_time']:
            report_text += f"   Окончание: {report['end_time'].strftime('%H:%M')}\n"
        report_text += f"   Время работы: {work_time_str}\n"
        report_text += f"   Время перерывов: {break_time_str}\n"
        
        if report['breaks']:
            report_text += "   Перерывы:\n"
            for i, break_item in enumerate(report['breaks'], 1):
                start_time = break_item['start_time'].strftime('%H:%M')
                if break_item['end_time']:
                    end_time = break_item['end_time'].strftime('%H:%M')
                    duration = break_item['duration'] // 60
                    report_text += f"     {i}. {start_time} - {end_time} ({duration} мин)\n"
                else:
                    report_text += f"     {i}. {start_time} - активен\n"
        
        report_text += "\n"
        
        total_work_time += report['total_work_time']
        total_break_time += report['total_break_time']
    
    # Итоги
    total_work_time_str = f"{total_work_time // 3600:02d}:{(total_work_time % 3600) // 60:02d}"
    total_break_time_str = f"{total_break_time // 3600:02d}:{(total_break_time % 3600) // 60:02d}"
    
    report_text += f"📈 ИТОГО:\n"
    report_text += f"   Общее время работы: {total_work_time_str}\n"
    report_text += f"   Общее время перерывов: {total_break_time_str}\n"
    
    # Разбиваем на части, если отчет слишком длинный
    if len(report_text) > 4000:
        parts = [report_text[i:i+4000] for i in range(0, len(report_text), 4000)]
        for i, part in enumerate(parts):
            if i == 0:
                await callback.message.edit_text(part)
            else:
                await callback.message.answer(part)
        await callback.message.answer("Отчет завершен.", reply_markup=admin_reports_menu_keyboard())
    else:
        await callback.message.edit_text(report_text, reply_markup=admin_reports_menu_keyboard())

@router.callback_query(F.data == "admin_applications_report")
async def admin_applications_report(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    # Получаем отчет по заявлениям за сегодня
    queue_stats = await get_applications_statistics_by_queue()
    
    if not queue_stats:
        await callback.message.edit_text(
            "Нет данных о заявлениях за сегодня.",
            reply_markup=admin_reports_menu_keyboard()
        )
        return
    
    # Формируем отчет по заявлениям
    report_text = f"📋 ОТЧЕТ ПО ЗАЯВЛЕНИЯМ за {date.today().strftime('%d.%m.%Y')}\n\n"
    
    total_applications = 0
    
    # Сортируем очереди для красивого отображения
    queue_order = ['lk', 'epgu', 'epgu_mail', 'epgu_problem']
    
    for queue_type in queue_order:
        if queue_type in queue_stats:
            stats = queue_stats[queue_type]
            queue_name = {
                'lk': 'ЛК',
                'epgu': 'ЕПГУ',
                'epgu_mail': 'ЕПГУ (почта)',
                'epgu_problem': 'ЕПГУ (проблемы)'
            }.get(queue_type, queue_type)
            
            report_text += f"📊 {queue_name}: {stats['total']} заявлений\n"
            
            if stats['by_employee']:
                for emp_fio, count in stats['by_employee'].items():
                    report_text += f"   👤 {emp_fio}: {count}\n"
            
            report_text += "\n"
            total_applications += stats['total']
    
    # Итоги
    report_text += f"📈 ИТОГО:\n"
    report_text += f"   Обработано заявлений: {total_applications}\n"
    
    if total_applications == 0:
        report_text += "   Сегодня заявления не обрабатывались"
    
    await callback.message.edit_text(report_text, reply_markup=admin_reports_menu_keyboard())

@router.callback_query(F.data == "admin_add_test_employees")
async def admin_add_test_employees(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    # Тестовые сотрудники
    test_employees = [
        {"tg_id": "6974821754", "fio": "Test Dot"},
        {"tg_id": "5418889030", "fio": "Test Msk"}
    ]
    
    added_count = 0
    already_exists_count = 0
    
    for emp_data in test_employees:
        # Проверяем, существует ли уже сотрудник
        existing_emp = await get_employee_by_tg_id(emp_data["tg_id"])
        if existing_emp:
            already_exists_count += 1
            continue
        
        # Добавляем сотрудника
        try:
            await add_employee(emp_data["tg_id"], emp_data["fio"])
            added_count += 1
        except Exception as e:
            logging.error(f"Ошибка при добавлении тестового сотрудника {emp_data['fio']}: {e}")
    
    # Формируем сообщение о результате
    message_text = f"✅ Добавление тестовых сотрудников завершено!\n\n"
    message_text += f"➕ Добавлено: {added_count}\n"
    message_text += f"⚠️ Уже существует: {already_exists_count}\n\n"
    
    if added_count > 0:
        message_text += "Добавленные сотрудники:\n"
        for emp_data in test_employees:
            message_text += f"• {emp_data['fio']} (ID: {emp_data['tg_id']})\n"
    
    await callback.message.edit_text(message_text, reply_markup=admin_staff_menu_keyboard())

def group_choice_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ЛК", callback_data="group_lk")],
        [InlineKeyboardButton(text="ЕПГУ", callback_data="group_epgu")],
        [InlineKeyboardButton(text="Почта", callback_data="group_mail")],
        [InlineKeyboardButton(text="Разбор проблем", callback_data="group_problem")],
        [InlineKeyboardButton(text="Отмена", callback_data="admin_menu")]
    ]) 
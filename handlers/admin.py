from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from db.crud import (
    add_employee, remove_employee, add_group_to_employee, remove_group_from_employee, list_employees_with_groups, is_admin, get_employee_by_tg_id, get_applications_by_queue_type, clear_queue_by_type, import_applications_from_excel, get_all_work_days_report,
    get_applications_statistics_by_queue, search_applications_by_fio, update_application_field, delete_application, get_all_employees
)
from keyboards.admin import admin_main_menu_keyboard, admin_staff_menu_keyboard, admin_queue_menu_keyboard, admin_queue_type_keyboard, admin_queue_pagination_keyboard, group_choice_keyboard, admin_reports_menu_keyboard, admin_search_applications_keyboard, admin_application_edit_keyboard, admin_queue_choice_keyboard, admin_status_choice_keyboard, admin_problem_status_choice_keyboard, admin_cancel_keyboard
from keyboards.main import main_menu_keyboard
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from db.crud import Application, ApplicationStatusEnum, get_application_by_id
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

class AdminApplicationStates(StatesGroup):
    waiting_fio_search = State()
    waiting_fio_edit = State()
    waiting_date_edit = State()
    waiting_reason_edit = State()
    waiting_responsible_edit = State()
    waiting_problem_comment_edit = State()

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

# ===== ОБРАБОТЧИКИ ПОИСКА И РЕДАКТИРОВАНИЯ ЗАЯВЛЕНИЙ =====

@router.callback_query(F.data == "admin_search_applications")
async def admin_search_applications_menu(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    await state.clear()
    await callback.message.edit_text(
        "🔍 Поиск и редактирование заявлений\n\nВыберите действие:",
        reply_markup=admin_search_applications_keyboard()
    )

@router.callback_query(F.data == "admin_search_by_fio")
async def admin_search_by_fio_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    await state.set_state(AdminApplicationStates.waiting_fio_search)
    await callback.message.edit_text(
        "Введите ФИО для поиска заявлений во всех очередях:",
        reply_markup=admin_cancel_keyboard()
    )

@router.message(AdminApplicationStates.waiting_fio_search)
async def admin_search_by_fio_process(message: Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        return
    
    fio = message.text.strip()
    if not fio:
        await message.answer("Пожалуйста, введите ФИО для поиска.", reply_markup=admin_cancel_keyboard())
        return
    
    applications = await search_applications_by_fio(fio)
    
    if not applications:
        await message.answer(
            f"Заявления для '{fio}' не найдены ни в одной очереди.",
            reply_markup=admin_search_applications_keyboard()
        )
        await state.clear()
        return
    
    # Показываем найденные заявления
    text = f"🔍 Найдено {len(applications)} заявлений для '{fio}':\n\n"
    
    for i, app in enumerate(applications[:10], 1):  # Показываем первые 10
        status_emoji = {
            'queued': '⏳',
            'in_progress': '🔄',
            'accepted': '✅',
            'rejected': '❌',
            'problem': '⚠️'
        }.get(app.status.value, '❓')
        
        queue_name = {
            'lk': 'ЛК',
            'epgu': 'ЕПГУ',
            'epgu_mail': 'ЕПГУ (почта)',
            'epgu_problem': 'ЕПГУ (проблемы)'
        }.get(app.queue_type, app.queue_type)
        
        text += f"{i}. {status_emoji} <b>ID: {app.id}</b>\n"
        text += f"   📋 {app.fio}\n"
        text += f"   📅 {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
        text += f"   🏛️ {queue_name}\n"
        text += f"   📊 {app.status.value}\n"
        if app.processed_by:
            text += f"   👤 {app.processed_by.fio}\n"
        text += "\n"
    
    if len(applications) > 10:
        text += f"... и еще {len(applications) - 10} заявлений\n\n"
    
    text += "Выберите заявление для редактирования:"
    
    # Создаем клавиатуру с кнопками для каждого заявления
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    for i, app in enumerate(applications[:10], 1):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(
                text=f"{i}. {app.fio} ({app.queue_type})", 
                callback_data=f"admin_edit_application_{app.id}"
            )
        ])
    keyboard.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_search_applications")])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data.startswith("admin_edit_application_"))
async def admin_edit_application_menu(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    app_id = int(callback.data.replace("admin_edit_application_", ""))
    app = await get_application_by_id(app_id)
    
    if not app:
        await callback.message.edit_text(
            "Заявление не найдено.",
            reply_markup=admin_search_applications_keyboard()
        )
        return
    
    # Формируем подробную информацию о заявлении
    status_emoji = {
        'queued': '⏳',
        'in_progress': '🔄',
        'accepted': '✅',
        'rejected': '❌',
        'problem': '⚠️'
    }.get(app.status.value, '❓')
    
    queue_name = {
        'lk': 'ЛК',
        'epgu': 'ЕПГУ',
        'epgu_mail': 'ЕПГУ (почта)',
        'epgu_problem': 'ЕПГУ (проблемы)'
    }.get(app.queue_type, app.queue_type)
    
    text = f"📋 <b>Редактирование заявления</b>\n\n"
    text += f"🆔 <b>ID:</b> {app.id}\n"
    text += f"👤 <b>ФИО:</b> {app.fio}\n"
    text += f"📅 <b>Дата подачи:</b> {app.submitted_at.strftime('%d.%m.%Y %H:%M')}\n"
    text += f"🏛️ <b>Очередь:</b> {queue_name}\n"
    text += f"📊 <b>Статус:</b> {status_emoji} {app.status.value}\n"
    text += f"💬 <b>Причина:</b> {app.status_reason or '-'}\n"
    text += f"👤 <b>Обработал:</b> {app.processed_by.fio if app.processed_by else '-'}\n"
    text += f"⚠️ <b>Статус проблемы:</b> {app.problem_status.value if app.problem_status else '-'}\n"
    text += f"💬 <b>Комментарий проблемы:</b> {app.problem_comment or '-'}\n"
    text += f"👤 <b>Ответственный:</b> {app.problem_responsible or '-'}\n"
    
    await callback.message.edit_text(text, reply_markup=admin_application_edit_keyboard(app_id), parse_mode="HTML")

# Обработчики редактирования полей
@router.callback_query(F.data.startswith("admin_edit_fio_"))
async def admin_edit_fio_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    app_id = int(callback.data.replace("admin_edit_fio_", ""))
    await state.update_data(app_id=app_id)
    await state.set_state(AdminApplicationStates.waiting_fio_edit)
    await callback.message.edit_text(
        "Введите новое ФИО:",
        reply_markup=admin_cancel_keyboard()
    )

@router.message(AdminApplicationStates.waiting_fio_edit)
async def admin_edit_fio_process(message: Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    app_id = data.get("app_id")
    new_fio = message.text.strip()
    
    if not new_fio:
        await message.answer("Пожалуйста, введите ФИО.", reply_markup=admin_cancel_keyboard())
        return
    
    success = await update_application_field(app_id, "fio", new_fio)
    if success:
        await message.answer(f"✅ ФИО изменено на: {new_fio}")
        # Возвращаемся к редактированию заявления
        app = await get_application_by_id(app_id)
        if app:
            await admin_edit_application_menu(
                type('CallbackQuery', (), {'data': f'admin_edit_application_{app_id}', 'message': message, 'from_user': message.from_user})(),
                state
            )
    else:
        await message.answer("❌ Ошибка при изменении ФИО", reply_markup=admin_cancel_keyboard())
    
    await state.clear()

@router.callback_query(F.data.startswith("admin_edit_queue_"))
async def admin_edit_queue_menu(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    app_id = int(callback.data.replace("admin_edit_queue_", ""))
    await callback.message.edit_text(
        "Выберите новую очередь:",
        reply_markup=admin_queue_choice_keyboard(app_id)
    )

@router.callback_query(F.data.startswith("admin_set_queue_"))
async def admin_set_queue(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    # Правильно парсим callback_data
    data = callback.data.replace("admin_set_queue_", "")
    
    # Определяем тип очереди и ID заявления
    if data.startswith("epgu_mail_"):
        queue_type = "epgu_mail"
        app_id = int(data.replace("epgu_mail_", ""))
    elif data.startswith("epgu_problem_"):
        queue_type = "epgu_problem"
        app_id = int(data.replace("epgu_problem_", ""))
    elif data.startswith("epgu_"):
        queue_type = "epgu"
        app_id = int(data.replace("epgu_", ""))
    elif data.startswith("lk_"):
        queue_type = "lk"
        app_id = int(data.replace("lk_", ""))
    else:
        await callback.message.edit_text("❌ Неизвестный тип очереди", reply_markup=admin_cancel_keyboard())
        return
    
    success = await update_application_field(app_id, "queue_type", queue_type)
    if success:
        queue_name = {
            'lk': 'ЛК',
            'epgu': 'ЕПГУ',
            'epgu_mail': 'ЕПГУ (почта)',
            'epgu_problem': 'ЕПГУ (проблемы)'
        }.get(queue_type, queue_type)
        await callback.message.edit_text(f"✅ Очередь изменена на: {queue_name}")
        # Возвращаемся к редактированию заявления
        app = await get_application_by_id(app_id)
        if app:
            await admin_edit_application_menu(callback, state)
    else:
        await callback.message.edit_text("❌ Ошибка при изменении очереди", reply_markup=admin_cancel_keyboard())

@router.callback_query(F.data.startswith("admin_edit_status_"))
async def admin_edit_status_menu(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    app_id = int(callback.data.replace("admin_edit_status_", ""))
    await callback.message.edit_text(
        "Выберите новый статус:",
        reply_markup=admin_status_choice_keyboard(app_id)
    )

@router.callback_query(F.data.startswith("admin_set_status_"))
async def admin_set_status(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    # Правильно парсим callback_data
    data = callback.data.replace("admin_set_status_", "")
    
    # Определяем статус и ID заявления
    if data.startswith("in_progress_"):
        status_name = "in_progress"
        app_id = int(data.replace("in_progress_", ""))
    elif data.startswith("accepted_"):
        status_name = "accepted"
        app_id = int(data.replace("accepted_", ""))
    elif data.startswith("rejected_"):
        status_name = "rejected"
        app_id = int(data.replace("rejected_", ""))
    elif data.startswith("problem_"):
        status_name = "problem"
        app_id = int(data.replace("problem_", ""))
    elif data.startswith("queued_"):
        status_name = "queued"
        app_id = int(data.replace("queued_", ""))
    else:
        await callback.message.edit_text("❌ Неизвестный статус", reply_markup=admin_cancel_keyboard())
        return
    
    status_map = {
        'queued': ApplicationStatusEnum.QUEUED,
        'in_progress': ApplicationStatusEnum.IN_PROGRESS,
        'accepted': ApplicationStatusEnum.ACCEPTED,
        'rejected': ApplicationStatusEnum.REJECTED,
        'problem': ApplicationStatusEnum.PROBLEM
    }
    
    new_status = status_map.get(status_name)
    if new_status:
        success = await update_application_field(app_id, "status", new_status)
        if success:
            status_display = {
                'queued': 'В очереди',
                'in_progress': 'В обработке',
                'accepted': 'Принято',
                'rejected': 'Отклонено',
                'problem': 'Проблема'
            }.get(status_name, status_name)
            await callback.message.edit_text(f"✅ Статус изменен на: {status_display}")
            # Возвращаемся к редактированию заявления
            app = await get_application_by_id(app_id)
            if app:
                await admin_edit_application_menu(callback, state)
        else:
            await callback.message.edit_text("❌ Ошибка при изменении статуса", reply_markup=admin_cancel_keyboard())

@router.callback_query(F.data.startswith("admin_edit_reason_"))
async def admin_edit_reason_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    app_id = int(callback.data.replace("admin_edit_reason_", ""))
    await state.update_data(app_id=app_id)
    await state.set_state(AdminApplicationStates.waiting_reason_edit)
    await callback.message.edit_text(
        "Введите новую причину:",
        reply_markup=admin_cancel_keyboard()
    )

@router.message(AdminApplicationStates.waiting_reason_edit)
async def admin_edit_reason_process(message: Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    app_id = data.get("app_id")
    new_reason = message.text.strip()
    
    success = await update_application_field(app_id, "status_reason", new_reason)
    if success:
        await message.answer(f"✅ Причина изменена на: {new_reason}")
        # Возвращаемся к редактированию заявления
        app = await get_application_by_id(app_id)
        if app:
            await admin_edit_application_menu(
                type('CallbackQuery', (), {'data': f'admin_edit_application_{app_id}', 'message': message, 'from_user': message.from_user})(),
                state
            )
    else:
        await message.answer("❌ Ошибка при изменении причины", reply_markup=admin_cancel_keyboard())
    
    await state.clear()

@router.callback_query(F.data.startswith("admin_edit_responsible_"))
async def admin_edit_responsible_start(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    app_id = int(callback.data.replace("admin_edit_responsible_", ""))
    await state.update_data(app_id=app_id)
    await state.set_state(AdminApplicationStates.waiting_responsible_edit)
    await callback.message.edit_text(
        "Введите ФИО ответственного:",
        reply_markup=admin_cancel_keyboard()
    )

@router.message(AdminApplicationStates.waiting_responsible_edit)
async def admin_edit_responsible_process(message: Message, state: FSMContext):
    if not await check_admin(message.from_user.id):
        return
    
    data = await state.get_data()
    app_id = data.get("app_id")
    new_responsible = message.text.strip()
    
    success = await update_application_field(app_id, "problem_responsible", new_responsible)
    if success:
        await message.answer(f"✅ Ответственный изменен на: {new_responsible}")
        # Возвращаемся к редактированию заявления
        app = await get_application_by_id(app_id)
        if app:
            await admin_edit_application_menu(
                type('CallbackQuery', (), {'data': f'admin_edit_application_{app_id}', 'message': message, 'from_user': message.from_user})(),
                state
            )
    else:
        await message.answer("❌ Ошибка при изменении ответственного", reply_markup=admin_cancel_keyboard())
    
    await state.clear()

@router.callback_query(F.data.startswith("admin_edit_problem_status_"))
async def admin_edit_problem_status_menu(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    app_id = int(callback.data.replace("admin_edit_problem_status_", ""))
    await callback.message.edit_text(
        "Выберите новый статус проблемы:",
        reply_markup=admin_problem_status_choice_keyboard(app_id)
    )

@router.callback_query(F.data.startswith("admin_set_problem_status_"))
async def admin_set_problem_status(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    # Правильно парсим callback_data
    data = callback.data.replace("admin_set_problem_status_", "")
    
    # Определяем статус и ID заявления
    if data.startswith("solved_return_"):
        status_name = "solved_return"
        app_id = int(data.replace("solved_return_", ""))
    elif data.startswith("in_progress_"):
        status_name = "in_progress"
        app_id = int(data.replace("in_progress_", ""))
    elif data.startswith("solved_"):
        status_name = "solved"
        app_id = int(data.replace("solved_", ""))
    elif data.startswith("new_"):
        status_name = "new"
        app_id = int(data.replace("new_", ""))
    else:
        await callback.message.edit_text("❌ Неизвестный статус проблемы", reply_markup=admin_cancel_keyboard())
        return
    
    from db.models import ProblemStatusEnum
    status_map = {
        'new': ProblemStatusEnum.NEW,
        'in_progress': ProblemStatusEnum.IN_PROGRESS,
        'solved': ProblemStatusEnum.SOLVED,
        'solved_return': ProblemStatusEnum.SOLVED_RETURN
    }
    
    new_status = status_map.get(status_name)
    if new_status:
        success = await update_application_field(app_id, "problem_status", new_status)
        if success:
            status_display = {
                'new': 'Новое',
                'in_progress': 'В процессе решения',
                'solved': 'Решено',
                'solved_return': 'Решено, отправлено на доработку'
            }.get(status_name, status_name)
            await callback.message.edit_text(f"✅ Статус проблемы изменен на: {status_display}")
            # Возвращаемся к редактированию заявления
            app = await get_application_by_id(app_id)
            if app:
                await admin_edit_application_menu(callback, state)
        else:
            await callback.message.edit_text("❌ Ошибка при изменении статуса проблемы", reply_markup=admin_cancel_keyboard())

@router.callback_query(F.data.startswith("admin_delete_application_"))
async def admin_delete_application_confirm(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    app_id = int(callback.data.replace("admin_delete_application_", ""))
    app = await get_application_by_id(app_id)
    
    if not app:
        await callback.message.edit_text(
            "Заявление не найдено.",
            reply_markup=admin_search_applications_keyboard()
        )
        return
    
    # Создаем клавиатуру подтверждения
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑️ Да, удалить", callback_data=f"admin_confirm_delete_{app_id}")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data=f"admin_edit_application_{app_id}")]
    ])
    
    await callback.message.edit_text(
        f"⚠️ Вы уверены, что хотите удалить заявление?\n\n"
        f"ID: {app.id}\n"
        f"ФИО: {app.fio}\n"
        f"Очередь: {app.queue_type}\n"
        f"Статус: {app.status.value}",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("admin_confirm_delete_"))
async def admin_confirm_delete_application(callback: CallbackQuery, state: FSMContext):
    if not await check_admin(callback.from_user.id):
        return
    
    app_id = int(callback.data.replace("admin_confirm_delete_", ""))
    
    success = await delete_application(app_id)
    if success:
        await callback.message.edit_text(
            f"✅ Заявление {app_id} удалено.",
            reply_markup=admin_search_applications_keyboard()
        )
    else:
        await callback.message.edit_text(
            "❌ Ошибка при удалении заявления.",
            reply_markup=admin_search_applications_keyboard()
        ) 
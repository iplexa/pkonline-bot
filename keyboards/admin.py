from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Управление сотрудниками", callback_data="admin_staff_menu")],
        [InlineKeyboardButton(text="📋 Управление очередями", callback_data="admin_queue_menu")],
        [InlineKeyboardButton(text="📊 Отчеты", callback_data="admin_reports_menu")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])

def admin_staff_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить сотрудника", callback_data="admin_add_employee")],
        [InlineKeyboardButton(text="➕ Добавить тестовых сотрудников", callback_data="admin_add_test_employees")],
        [InlineKeyboardButton(text="➖ Удалить сотрудника", callback_data="admin_remove_employee")],
        [InlineKeyboardButton(text="➕ Добавить группу сотруднику", callback_data="admin_add_group")],
        [InlineKeyboardButton(text="➖ Удалить группу у сотрудника", callback_data="admin_remove_group")],
        [InlineKeyboardButton(text="📋 Список сотрудников", callback_data="admin_list_employees")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])

def admin_queue_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁️ Просмотр очереди", callback_data="admin_view_queue")],
        [InlineKeyboardButton(text="🗑️ Очистить очередь", callback_data="admin_clear_queue")],
        [InlineKeyboardButton(text="📤 Загрузить заявления", callback_data="admin_upload_queue")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])

def admin_reports_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Полный отчет", callback_data="admin_full_report")],
        [InlineKeyboardButton(text="⏰ Отчет по рабочему времени", callback_data="admin_work_time_report")],
        [InlineKeyboardButton(text="📋 Отчет по заявлениям", callback_data="admin_applications_report")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])

def group_choice_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ЛК", callback_data="group_lk")],
        [InlineKeyboardButton(text="ЕПГУ", callback_data="group_epgu")],
        [InlineKeyboardButton(text="Эскалация", callback_data="group_escalation")]
    ])

def admin_queue_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ЛК", callback_data="admin_queue_type_lk")],
        [InlineKeyboardButton(text="ЕПГУ", callback_data="admin_queue_type_epgu")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_queue_menu")]
    ])

def admin_queue_pagination_keyboard(queue_type: str, page: int, total_pages: int):
    buttons = []
    if total_pages > 1:
        row = []
        if page > 1:
            row.append(InlineKeyboardButton(text="◀️", callback_data=f"admin_queue_page_{queue_type}_{page-1}"))
        row.append(InlineKeyboardButton(text=f"{page}/{total_pages}", callback_data="no_action"))
        if page < total_pages:
            row.append(InlineKeyboardButton(text="▶️", callback_data=f"admin_queue_page_{queue_type}_{page+1}"))
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_queue_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons) 
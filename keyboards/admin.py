from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Управление сотрудниками", callback_data="admin_staff_menu")],
        [InlineKeyboardButton(text="📋 Управление очередями", callback_data="admin_queue_menu")],
        [InlineKeyboardButton(text="🔍 Поиск и редактирование заявлений", callback_data="admin_search_applications")],
        [InlineKeyboardButton(text="📊 Отчеты", callback_data="admin_reports_menu")],
        [InlineKeyboardButton(text="⚙️ Настройка чатов", callback_data="admin_chat_settings")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])

def admin_staff_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить сотрудника", callback_data="admin_add_employee")],
        [InlineKeyboardButton(text="➕ Добавить тестовых сотрудников", callback_data="admin_add_test_employees")],
        [InlineKeyboardButton(text="👥 Создать основных сотрудников", callback_data="admin_add_main_employees")],
        [InlineKeyboardButton(text="✏️ Изменить ФИО сотрудника", callback_data="admin_edit_employee_fio")],
        [InlineKeyboardButton(text="➖ Удалить сотрудника", callback_data="admin_remove_employee")],
        [InlineKeyboardButton(text="➕ Добавить группу сотруднику", callback_data="admin_add_group")],
        [InlineKeyboardButton(text="➖ Удалить группу у сотрудника", callback_data="admin_remove_group")],
        [InlineKeyboardButton(text="⏰ Управление рабочим временем", callback_data="admin_work_time_management")],
        [InlineKeyboardButton(text="📋 Список сотрудников", callback_data="admin_list_employees")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])

def admin_queue_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👁️ Просмотр очереди", callback_data="admin_view_queue")],
        [InlineKeyboardButton(text="🗑️ Очистить очередь", callback_data="admin_clear_queue")],
        [InlineKeyboardButton(text="📤 Загрузить заявления", callback_data="admin_upload_queue")],
        [InlineKeyboardButton(text="📊 Импорт выгрузки 1С", callback_data="admin_upload_1c")],
        [InlineKeyboardButton(text="💾 Создать бэкап БД", callback_data="admin_create_backup")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])

def admin_reports_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Полный отчет", callback_data="admin_full_report")],
        [InlineKeyboardButton(text="⏰ Отчет по рабочему времени", callback_data="admin_work_time_report")],
        [InlineKeyboardButton(text="📋 Отчет по заявлениям", callback_data="admin_applications_report")],
        [InlineKeyboardButton(text="📮 Экспорт просроченных заявлений почты", callback_data="admin_export_overdue_mail")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])

def group_choice_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ЛК", callback_data="group_lk")],
        [InlineKeyboardButton(text="ЕПГУ", callback_data="group_epgu")],
        [InlineKeyboardButton(text="Почта", callback_data="group_mail")],
        [InlineKeyboardButton(text="Разбор проблем", callback_data="group_problem")],
        [InlineKeyboardButton(text="Эскалация", callback_data="group_escalation")]
    ])

def admin_queue_type_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ЛК", callback_data="admin_queue_type_lk")],
        [InlineKeyboardButton(text="ЕПГУ", callback_data="admin_queue_type_epgu")],
        [InlineKeyboardButton(text="ЕПГУ (почта)", callback_data="admin_queue_type_epgu_mail")],
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

def admin_search_applications_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск по ФИО", callback_data="admin_search_by_fio")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])

def admin_application_edit_keyboard(app_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Изменить ФИО", callback_data=f"admin_edit_fio_{app_id}")],
        [InlineKeyboardButton(text="📅 Изменить дату подачи", callback_data=f"admin_edit_date_{app_id}")],
        [InlineKeyboardButton(text="🔄 Изменить очередь", callback_data=f"admin_edit_queue_{app_id}")],
        [InlineKeyboardButton(text="📊 Изменить статус", callback_data=f"admin_edit_status_{app_id}")],
        [InlineKeyboardButton(text="💬 Изменить причину", callback_data=f"admin_edit_reason_{app_id}")],
        [InlineKeyboardButton(text="👤 Назначить ответственного", callback_data=f"admin_edit_responsible_{app_id}")],
        [InlineKeyboardButton(text="⚠️ Изменить статус проблемы", callback_data=f"admin_edit_problem_status_{app_id}")],
        [InlineKeyboardButton(text="🗑️ Удалить заявление", callback_data=f"admin_delete_application_{app_id}")],
        [InlineKeyboardButton(text="🔍 Найти снова", callback_data="admin_search_by_fio")],
        [InlineKeyboardButton(text="🔙 Назад к поиску", callback_data="admin_search_applications")]
    ])

def admin_queue_choice_keyboard(app_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ЛК", callback_data=f"admin_set_queue_lk_{app_id}")],
        [InlineKeyboardButton(text="ЕПГУ", callback_data=f"admin_set_queue_epgu_{app_id}")],
        [InlineKeyboardButton(text="ЕПГУ (почта)", callback_data=f"admin_set_queue_epgu_mail_{app_id}")],
        [InlineKeyboardButton(text="ЕПГУ (проблемы)", callback_data=f"admin_set_queue_epgu_problem_{app_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_edit_application_{app_id}")]
    ])

def admin_status_choice_keyboard(app_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏳ В очереди", callback_data=f"admin_set_status_queued_{app_id}")],
        [InlineKeyboardButton(text="🔄 В обработке", callback_data=f"admin_set_status_in_progress_{app_id}")],
        [InlineKeyboardButton(text="✅ Принято", callback_data=f"admin_set_status_accepted_{app_id}")],
        [InlineKeyboardButton(text="❌ Отклонено", callback_data=f"admin_set_status_rejected_{app_id}")],
        [InlineKeyboardButton(text="⚠️ Проблема", callback_data=f"admin_set_status_problem_{app_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_edit_application_{app_id}")]
    ])

def admin_problem_status_choice_keyboard(app_id: int):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🆕 Новое", callback_data=f"admin_set_problem_status_new_{app_id}")],
        [InlineKeyboardButton(text="🔄 В процессе решения", callback_data=f"admin_set_problem_status_in_progress_{app_id}")],
        [InlineKeyboardButton(text="✅ Решено", callback_data=f"admin_set_problem_status_solved_{app_id}")],
        [InlineKeyboardButton(text="📤 Решено, отправлено на доработку", callback_data=f"admin_set_problem_status_solved_return_{app_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"admin_edit_application_{app_id}")]
    ])

def admin_cancel_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="admin_search_applications")]
    ])

def admin_chat_settings_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Настроить общий чат", callback_data="admin_set_general_chat")],
        [InlineKeyboardButton(text="📝 Настроить админский чат", callback_data="admin_set_admin_chat")],
        [InlineKeyboardButton(text="🧵 Настроить треды", callback_data="admin_set_threads")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_menu")]
    ])

def admin_thread_settings_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏰ Рабочее время", callback_data="admin_set_thread_work_time")],
        [InlineKeyboardButton(text="📋 ЛК - Обработка", callback_data="admin_set_thread_lk_processing")],
        [InlineKeyboardButton(text="⚠️ ЛК - Проблема", callback_data="admin_set_thread_lk_problem")],
        [InlineKeyboardButton(text="✅ ЕПГУ - Принято", callback_data="admin_set_thread_epgu_accepted")],
        [InlineKeyboardButton(text="📮 ЕПГУ - Почта", callback_data="admin_set_thread_epgu_mail_queue")],
        [InlineKeyboardButton(text="⚠️ ЕПГУ - Проблема", callback_data="admin_set_thread_epgu_problem")],
        [InlineKeyboardButton(text="✅ Почта - Подтверждено", callback_data="admin_set_thread_mail_confirmed")],
        [InlineKeyboardButton(text="❌ Почта - Отклонено", callback_data="admin_set_thread_mail_rejected")],
        [InlineKeyboardButton(text="✅ Разбор проблем - Исправлено", callback_data="admin_set_thread_problem_solved")],
        [InlineKeyboardButton(text="🔄 Разбор проблем - В очередь", callback_data="admin_set_thread_problem_solved_queue")],
        [InlineKeyboardButton(text="🔄 Разбор проблем - В процессе", callback_data="admin_set_thread_problem_in_progress")],
        [InlineKeyboardButton(text="📊 Очереди - Обновления", callback_data="admin_set_thread_queue_updated")],
        [InlineKeyboardButton(text="🚨 Эскалация", callback_data="admin_set_thread_escalation")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_chat_settings")]
    ])

def admin_employee_selection_keyboard(action: str):
    """Клавиатура для выбора сотрудника"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Выбрать сотрудника", callback_data=f"admin_select_employee_{action}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_staff_menu")]
    ])

def admin_work_time_management_keyboard():
    """Клавиатура для управления рабочим временем"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Начать рабочий день", callback_data="admin_start_work_day")],
        [InlineKeyboardButton(text="⏹️ Завершить рабочий день", callback_data="admin_end_work_day")],
        [InlineKeyboardButton(text="🗑️ Очистить данные рабочего времени", callback_data="admin_clear_work_time")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_staff_menu")]
    ]) 
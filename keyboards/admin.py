from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def admin_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Добавить сотрудника", callback_data="admin_add_employee")],
        [InlineKeyboardButton(text="Удалить сотрудника", callback_data="admin_remove_employee")],
        [InlineKeyboardButton(text="Назначить группу", callback_data="admin_add_group")],
        [InlineKeyboardButton(text="Убрать группу", callback_data="admin_remove_group")],
        [InlineKeyboardButton(text="Список сотрудников", callback_data="admin_list_employees")],
        [InlineKeyboardButton(text="Меню", callback_data="main_menu")],
    ])

def group_choice_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ЛК", callback_data="group_lk")],
        [InlineKeyboardButton(text="ЕПГУ", callback_data="group_epgu")],
        [InlineKeyboardButton(text="Эскалация", callback_data="group_escalation")],
        [InlineKeyboardButton(text="Меню", callback_data="main_menu")],
    ]) 
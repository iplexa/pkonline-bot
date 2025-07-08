from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(is_admin=False, groups=None):
    if groups is None:
        groups = []
    buttons = []
    if is_admin:
        buttons.append([InlineKeyboardButton(text="Управление сотрудниками", callback_data="admin_menu")])
        buttons.append([InlineKeyboardButton(text="Очередь ЛК", callback_data="lk_menu")])
        buttons.append([InlineKeyboardButton(text="Очередь ЕПГУ", callback_data="epgu_menu")])
        buttons.append([InlineKeyboardButton(text="Эскалация", callback_data="escalation_menu")])
    else:
        if "lk" in groups:
            buttons.append([InlineKeyboardButton(text="Очередь ЛК", callback_data="lk_menu")])
        if "epgu" in groups:
            buttons.append([InlineKeyboardButton(text="Очередь ЕПГУ", callback_data="epgu_menu")])
        if "escalation" in groups:
            buttons.append([InlineKeyboardButton(text="Эскалация", callback_data="escalation_menu")])
    buttons.append([InlineKeyboardButton(text="Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons) 
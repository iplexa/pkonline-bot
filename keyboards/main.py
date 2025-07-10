from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard(is_admin=False, groups=None, with_menu_button=False):
    if groups is None:
        groups = []
    buttons = []
    
    # Кнопка управления рабочим временем для всех пользователей
    buttons.append([InlineKeyboardButton(text="⏰ Рабочее время", callback_data="work_time_menu")])
    
    if is_admin:
        buttons.append([InlineKeyboardButton(text="📋 ЛК", callback_data="lk_menu")])
        buttons.append([InlineKeyboardButton(text="🏛️ ЕПГУ", callback_data="epgu_menu")])
        buttons.append([InlineKeyboardButton(text="📮 Почта", callback_data="mail_menu")])
        buttons.append([InlineKeyboardButton(text="🛠️ Разбор проблем", callback_data="problem_menu")])
        buttons.append([InlineKeyboardButton(text="⚙️ Админ", callback_data="admin_menu")])

    else:
        if "lk" in groups:
            buttons.append([InlineKeyboardButton(text="📋 ЛК", callback_data="lk_menu")])
        if "epgu" in groups:
            buttons.append([InlineKeyboardButton(text="🏛️ ЕПГУ", callback_data="epgu_menu")])
        if "mail" in groups:
            buttons.append([InlineKeyboardButton(text="📮 Почта", callback_data="mail_menu")])
        if "problem" in groups:
            buttons.append([InlineKeyboardButton(text="🛠️ Разбор проблем", callback_data="problem_menu")])
    
    if with_menu_button:
        buttons.append([InlineKeyboardButton(text="Меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 
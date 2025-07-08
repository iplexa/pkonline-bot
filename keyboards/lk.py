from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def lk_queue_keyboard(menu=False):
    buttons = [[InlineKeyboardButton(text="Получить заявление", callback_data="get_lk_application")]]
    if menu:
        buttons.append([InlineKeyboardButton(text="Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def lk_decision_keyboard(menu=False):
    buttons = [
        [InlineKeyboardButton(text="Принять", callback_data="accept_lk")],
        [InlineKeyboardButton(text="Отклонить", callback_data="reject_lk")],
        [InlineKeyboardButton(text="Проблемное", callback_data="problem_lk")],
        [InlineKeyboardButton(text="Вернуть в очередь", callback_data="return_lk")],
    ]
    if menu:
        buttons.append([InlineKeyboardButton(text="Меню", callback_data="main_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons) 
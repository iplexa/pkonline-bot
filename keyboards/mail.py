from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def mail_menu_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для меню почты"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск по ФИО", callback_data="mail_search_fio")],
        [InlineKeyboardButton(text="🔎 Инфо по ФИО", callback_data="mail_info_fio")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
    ])

def mail_search_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для поиска заявлений"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="mail_back_to_menu")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ])

def mail_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения подписи"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="mail_confirm_yes")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="mail_back_to_menu")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")]
    ]) 
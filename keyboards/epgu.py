from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def epgu_queue_keyboard(menu: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для очереди ЕПГУ"""
    if menu:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Получить заявление", callback_data="get_epgu_application")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Получить заявление", callback_data="get_epgu_application")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])

def epgu_decision_keyboard(menu: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для принятия решения по заявлению ЕПГУ"""
    if menu:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Получить заявление", callback_data="get_epgu_application")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принято", callback_data="accept_epgu")],
            [InlineKeyboardButton(text="📝 Принято, отправлено на подпись", callback_data="accept_mail_epgu")],
            [InlineKeyboardButton(text="📞 Не дозвонились", callback_data="no_call_epgu")],
            [InlineKeyboardButton(text="⚠️ Проблема", callback_data="problem_epgu")],
            [InlineKeyboardButton(text="🔄 Вернуть в очередь", callback_data="return_epgu")]
        ])

def epgu_reason_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ввода причины с кнопкой отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="epgu_cancel_reason")]
    ]) 
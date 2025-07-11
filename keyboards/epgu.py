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
    """Клавиатура для принятия решения по заявлению ЕПГУ (новая логика)"""
    if menu:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Получить заявление", callback_data="get_epgu_application")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принято", callback_data="epgu_accept")],
            [InlineKeyboardButton(text="📄 Есть сканы, на подпись", callback_data="epgu_has_scans")],
            [InlineKeyboardButton(text="❗ Нет сканов, на подпись и запрос сканов", callback_data="epgu_no_scans")],
            [InlineKeyboardButton(text="📥 Нет сканов, только сканы (без подписи)", callback_data="epgu_only_scans")],
            [InlineKeyboardButton(text="⚠️ Ошибка", callback_data="epgu_error")],
            [InlineKeyboardButton(text="🔄 Вернуть в очередь", callback_data="return_epgu")]
        ])

def epgu_reason_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ввода причины с кнопкой отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="epgu_cancel_reason")]
    ]) 
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def lk_queue_keyboard(menu: bool = True) -> InlineKeyboardMarkup:
    if menu:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Получить заявление", callback_data="get_lk_application")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Получить заявление", callback_data="get_lk_application")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])

def lk_decision_keyboard(menu: bool = True) -> InlineKeyboardMarkup:
    if menu:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Получить заявление", callback_data="get_lk_application")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принять", callback_data="accept_lk")],
            [InlineKeyboardButton(text="❌ Отклонить", callback_data="reject_lk")],
            [InlineKeyboardButton(text="⚠️ Проблема", callback_data="problem_lk")],
            [InlineKeyboardButton(text="🔄 Вернуть в очередь", callback_data="return_lk")]
        ])

def lk_reason_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="lk_cancel_reason")]
    ]) 
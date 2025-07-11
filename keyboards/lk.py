from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def lk_queue_keyboard(menu=False):
    buttons = [
        [InlineKeyboardButton(text="Следующее заявление", callback_data="lk_next")],
        [InlineKeyboardButton(text="Поиск по ФИО", callback_data="lk_search_fio")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
    if menu:
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def lk_decision_keyboard(menu: bool = True) -> InlineKeyboardMarkup:
    if menu:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Получить заявление", callback_data="lk_next")],
            [InlineKeyboardButton(text="Поиск по ФИО", callback_data="lk_search_fio")],
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

def lk_escalate_keyboard(app_id: int, is_priority: bool):
    buttons = []
    if not is_priority:
        buttons.append([InlineKeyboardButton(text="🚨 Эскалировать", callback_data=f"lk_escalate_{app_id}")])
    buttons.append([InlineKeyboardButton(text="🔍 Найти еще", callback_data="lk_search_fio")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="lk_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons) 
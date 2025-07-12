from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def epgu_queue_keyboard(menu=False):
    buttons = [
        [InlineKeyboardButton(text="Следующее заявление", callback_data="epgu_next")],
        [InlineKeyboardButton(text="Поиск по ФИО", callback_data="epgu_search_fio")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]
    ]
    if menu:
        buttons = [[InlineKeyboardButton(text="🔙 Назад", callback_data="main_menu")]]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def epgu_decision_keyboard(menu: bool = True) -> InlineKeyboardMarkup:
    """Клавиатура для принятия решения по заявлению ЕПГУ (новая логика)"""
    if menu:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📋 Получить заявление", callback_data="epgu_next")],
            [InlineKeyboardButton(text="Поиск по ФИО", callback_data="epgu_search_fio")],
            [InlineKeyboardButton(text="🔙 Главное меню", callback_data="main_menu")]
        ])
    else:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Принято", callback_data="accept_epgu")],
            [InlineKeyboardButton(text="📄 Есть сканы, на подпись", callback_data="epgu_signature")],
            [InlineKeyboardButton(text="❗ Нет сканов, на подпись и запрос сканов", callback_data="epgu_signature_scans")],
            [InlineKeyboardButton(text="📥 Нет сканов, только сканы (без подписи)", callback_data="epgu_scans")],
            [InlineKeyboardButton(text="⚠️ Ошибка", callback_data="epgu_error")],
            [InlineKeyboardButton(text="🔄 Вернуть в очередь", callback_data="return_epgu")]
        ])

def epgu_reason_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для ввода причины с кнопкой отмены"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="epgu_cancel_reason")]
    ])

def epgu_escalate_keyboard(app_id: int, is_priority: bool, status: str = "queued"):
    buttons = []
    # Кнопка обработки заявления (только если в очереди)
    if status == "queued":
        buttons.append([InlineKeyboardButton(text="🔄 Обработать заявление", callback_data=f"epgu_process_found_{app_id}")])
    # Кнопка эскалации (только если не приоритетное)
    if not is_priority:
        buttons.append([InlineKeyboardButton(text="🚨 Эскалировать", callback_data=f"epgu_escalate_{app_id}")])
    buttons.append([InlineKeyboardButton(text="🔍 Найти еще", callback_data="epgu_search_fio")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="epgu_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons) 
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def epgu_queue_keyboard(menu=False):
    buttons = [
        [InlineKeyboardButton(text="Следующее заявление", callback_data="epgu_next")],
        [InlineKeyboardButton(text="🔍 Поиск по ФИО", callback_data="epgu_search_fio")],
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
            [InlineKeyboardButton(text="🔍 Поиск по ФИО", callback_data="epgu_search_fio")],
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
    """Улучшенная клавиатура для найденных заявлений"""
    print(f"DEBUG: epgu_escalate_keyboard called with app_id={app_id}, is_priority={is_priority}, status={status}")
    
    buttons = []
    
    # Кнопка обработки заявления (если в очереди или в обработке)
    if status in ["queued", "in_progress"]:
        if status == "queued":
            button_text = "🔄 Обработать заявление"
        else:
            button_text = "🔄 Взять в обработку"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"epgu_process_found_{app_id}")])
        print(f"DEBUG: Added process button for status={status}")
    
    # Кнопка эскалации (только если не приоритетное и в очереди)
    if not is_priority and status == "queued":
        buttons.append([InlineKeyboardButton(text="🚨 Эскалировать", callback_data=f"epgu_escalate_{app_id}")])
        print(f"DEBUG: Added escalate button (not priority, queued)")
    
    # Навигационные кнопки
    buttons.append([
        InlineKeyboardButton(text="🔍 Найти еще", callback_data="epgu_search_fio"),
        InlineKeyboardButton(text="📋 Следующее", callback_data="epgu_next")
    ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="epgu_menu")])
    
    print(f"DEBUG: Total buttons: {len(buttons)}")
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def epgu_search_results_keyboard(fio: str, total_found: int):
    """Клавиатура для результатов поиска"""
    buttons = []
    
    if total_found > 0:
        buttons.append([InlineKeyboardButton(text=f"📊 Найдено: {total_found} заявлений", callback_data="epgu_search_info")])
    
    buttons.append([
        InlineKeyboardButton(text="🔍 Новый поиск", callback_data="epgu_search_fio"),
        InlineKeyboardButton(text="📋 Следующее", callback_data="epgu_next")
    ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="epgu_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 
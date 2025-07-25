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

def lk_escalate_keyboard(app_id: int, is_priority: bool, status: str = "queued"):
    """Улучшенная клавиатура для найденных заявлений ЛК"""
    print(f"DEBUG: lk_escalate_keyboard called with app_id={app_id}, is_priority={is_priority}, status={status}")
    
    buttons = []
    
    # Кнопка обработки заявления (если в очереди или в обработке)
    if status in ["queued", "in_progress"]:
        if status == "queued":
            button_text = "🔄 Обработать заявление"
        else:
            button_text = "🔄 Взять в обработку"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"lk_process_found_{app_id}")])
        print(f"DEBUG: Added process button for status={status}")
    else:
        print(f"DEBUG: No process button - status '{status}' not in ['queued', 'in_progress']")
    
    # Кнопка эскалации (только если не приоритетное и в очереди)
    if not is_priority and status == "queued":
        buttons.append([InlineKeyboardButton(text="🚨 Эскалировать", callback_data=f"lk_escalate_{app_id}")])
        print(f"DEBUG: Added escalate button (not priority, queued)")
    else:
        if is_priority:
            print(f"DEBUG: No escalate button - application is priority")
        elif status != "queued":
            print(f"DEBUG: No escalate button - status '{status}' != 'queued'")
    
    # Навигационные кнопки
    buttons.append([
        InlineKeyboardButton(text="🔍 Найти еще", callback_data="lk_search_fio"),
        InlineKeyboardButton(text="📋 Следующее", callback_data="lk_next")
    ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="lk_menu")])
    
    print(f"DEBUG: Total buttons: {len(buttons)}")
    return InlineKeyboardMarkup(inline_keyboard=buttons) 
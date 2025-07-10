from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def work_time_keyboard():
    """Клавиатура для управления рабочим временем"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Начать рабочий день", callback_data="start_work_day")],
        [InlineKeyboardButton(text="Меню", callback_data="main_menu")],
    ])

def work_status_keyboard(status: str):
    """Клавиатура для активного рабочего дня"""
    buttons = []
    
    if status == "active":
        buttons.append([InlineKeyboardButton(text="☕ Начать перерыв", callback_data="start_break")])
        buttons.append([InlineKeyboardButton(text="🔴 Завершить рабочий день", callback_data="end_work_day")])
    elif status == "paused":
        buttons.append([InlineKeyboardButton(text="✅ Завершить перерыв", callback_data="end_break")])
        buttons.append([InlineKeyboardButton(text="🔴 Завершить рабочий день", callback_data="end_work_day")])
    elif status == "finished":
        buttons.append([InlineKeyboardButton(text="🟢 Начать новый день", callback_data="start_work_day")])
    
    buttons.append([InlineKeyboardButton(text="📊 Мой отчет", callback_data="work_report")])
    buttons.append([InlineKeyboardButton(text="Меню", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons) 
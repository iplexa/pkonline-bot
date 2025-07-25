from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def problem_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="ЛК", callback_data="problem_queue_lk")],
        [InlineKeyboardButton(text="ЕПГУ", callback_data="problem_queue_epgu")],
        [InlineKeyboardButton(text="Почта", callback_data="problem_queue_epgu_mail")],
        [InlineKeyboardButton(text="Главное меню", callback_data="main_menu")]
    ])

def problem_list_keyboard(problems):
    buttons = []
    for app in problems:
        reason = (app.status_reason or '-')
        if len(reason) > 40:
            reason = reason[:37] + '...'
        text = f"{app.fio} | {app.submitted_at.strftime('%d.%m.%Y %H:%M')} | {app.problem_status.value if app.problem_status else 'новое'} | {reason}"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"problem_app_{app.id}")])
    buttons.append([InlineKeyboardButton(text="Назад", callback_data="problem_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def problem_action_keyboard(app_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Решено (принять)", callback_data="problem_action_solved")],
        [InlineKeyboardButton(text="↩️ Решено, отправить на доработку", callback_data="problem_action_solved_return")],
        [InlineKeyboardButton(text="🛠️ Запустить процесс решения", callback_data="problem_action_in_progress")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="problem_action_cancel")],
        [InlineKeyboardButton(text="Назад", callback_data="problem_menu")]
    ])

def problem_status_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Решено", callback_data=f"problem_status_solved")],
        [InlineKeyboardButton(text="↩️ Решено и в очередь", callback_data=f"problem_status_solved_return")],
        [InlineKeyboardButton(text="🛠️ В процессе", callback_data=f"problem_status_in_progress")],
        [InlineKeyboardButton(text="🔄 Новое", callback_data=f"problem_status_new")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="problem_menu")]
    ]) 
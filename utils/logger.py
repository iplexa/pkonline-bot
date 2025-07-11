import logging
from typing import Optional, Dict, Any
from aiogram import Bot
from config import GENERAL_CHAT_ID, ADMIN_LOG_CHAT_ID, THREAD_IDS
import traceback
from datetime import datetime

class TelegramLogger:
    def __init__(self, bot: Bot):
        self.bot = bot
        self.general_chat_id = GENERAL_CHAT_ID
        self.admin_chat_id = ADMIN_LOG_CHAT_ID
        self.thread_ids = THREAD_IDS
    
    async def log_to_thread(self, thread_name: str, message: str, parse_mode: str = "HTML") -> bool:
        """Отправить сообщение в определенный тред общего чата"""
        if not self.general_chat_id or not self.thread_ids.get(thread_name):
            return False
        
        try:
            thread_id = self.thread_ids[thread_name]
            await self.bot.send_message(
                chat_id=self.general_chat_id,
                text=message,
                message_thread_id=thread_id,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            await self.log_error(f"Ошибка отправки в тред {thread_name}: {e}")
            return False
    
    async def log_to_admin(self, message: str, parse_mode: str = "HTML") -> bool:
        """Отправить сообщение в админский чат"""
        if not self.admin_chat_id:
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.admin_chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except Exception as e:
            # Если не можем отправить в админский чат, выводим в консоль
            print(f"Ошибка отправки в админский чат: {e}")
            return False
    
    async def log_error(self, error_message: str, exception: Optional[Exception] = None) -> bool:
        """Логировать ошибку в админский чат"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = f"🚨 <b>ОШИБКА</b> [{timestamp}]\n\n{error_message}"
        
        if exception:
            message += f"\n\n<code>{traceback.format_exc()}</code>"
        
        return await self.log_to_admin(message)
    
    # Методы для логирования рабочих событий
    async def log_work_time_start(self, employee_name: str, time: str) -> bool:
        """Логировать начало рабочего дня"""
        message = f"🟢 <b>Начало рабочего дня</b>\n👤 {employee_name}\n⏰ {time}"
        return await self.log_to_thread("work_time", message)
    
    async def log_work_time_end(self, employee_name: str, time: str, total_time: str) -> bool:
        """Логировать окончание рабочего дня"""
        message = f"🔴 <b>Окончание рабочего дня</b>\n👤 {employee_name}\n⏰ {time}\n⏱️ Общее время: {total_time}"
        return await self.log_to_thread("work_time", message)
    
    async def log_break_start(self, employee_name: str, time: str) -> bool:
        """Логировать начало перерыва"""
        message = f"☕ <b>Начало перерыва</b>\n👤 {employee_name}\n⏰ {time}"
        return await self.log_to_thread("work_time", message)
    
    async def log_break_end(self, employee_name: str, time: str) -> bool:
        """Логировать окончание перерыва"""
        message = f"✅ <b>Окончание перерыва</b>\n👤 {employee_name}\n⏰ {time}"
        return await self.log_to_thread("work_time", message)
    
    # Методы для логирования ЛК
    async def log_lk_accepted(self, employee_name: str, app_id: int, fio: str) -> bool:
        """Логировать принятие заявления ЛК"""
        message = f"✅ <b>ЛК: Заявление принято</b>\n👤 {employee_name}\n📋 ID: {app_id}\n👨‍💼 {fio}"
        return await self.log_to_thread("lk_processing", message)
    
    async def log_lk_rejected(self, employee_name: str, app_id: int, fio: str, reason: str) -> bool:
        """Логировать отклонение заявления ЛК"""
        message = f"❌ <b>ЛК: Заявление отклонено</b>\n👤 {employee_name}\n📋 ID: {app_id}\n👨‍💼 {fio}\n📝 Причина: {reason}"
        return await self.log_to_thread("lk_processing", message)
    
    async def log_lk_problem(self, employee_name: str, app_id: int, fio: str, reason: str) -> bool:
        """Логировать проблемное заявление ЛК"""
        message = f"⚠️ <b>ЛК: Проблемное заявление</b>\n👤 {employee_name}\n📋 ID: {app_id}\n👨‍💼 {fio}\n📝 Причина: {reason}"
        return await self.log_to_thread("lk_problem", message)
    
    # Методы для логирования ЕПГУ
    async def log_epgu_accepted(self, employee_name: str, app_id: int, fio: str) -> bool:
        """Логировать принятие заявления ЕПГУ"""
        message = f"✅ <b>ЕПГУ: Заявление принято</b>\n👤 {employee_name}\n📋 ID: {app_id}\n👨‍💼 {fio}"
        return await self.log_to_thread("epgu_accepted", message)
    
    async def log_epgu_mail_queue(self, employee_name: str, app_id: int, fio: str, action: str) -> bool:
        """Логировать отправку в очередь почты ЕПГУ"""
        message = f"📮 <b>ЕПГУ: Отправлено в очередь почты</b>\n👤 {employee_name}\n📋 ID: {app_id}\n👨‍💼 {fio}\n📝 Действие: {action}"
        return await self.log_to_thread("epgu_mail_queue", message)
    
    async def log_epgu_problem(self, employee_name: str, app_id: int, fio: str, reason: str) -> bool:
        """Логировать проблемное заявление ЕПГУ"""
        message = f"⚠️ <b>ЕПГУ: Проблемное заявление</b>\n👤 {employee_name}\n📋 ID: {app_id}\n👨‍💼 {fio}\n📝 Причина: {reason}"
        return await self.log_to_thread("epgu_problem", message)
    
    # Методы для логирования почты
    async def log_mail_confirmed(self, employee_name: str, fio: str) -> bool:
        """Логировать подтверждение почты"""
        message = f"✅ <b>Почта: Подтверждено</b>\n👤 {employee_name}\n👨‍💼 {fio}"
        return await self.log_to_thread("mail_confirmed", message)
    
    async def log_mail_rejected(self, employee_name: str, fio: str, reason: str) -> bool:
        """Логировать отклонение почты"""
        message = f"❌ <b>Почта: Отклонено</b>\n👤 {employee_name}\n👨‍💼 {fio}\n📝 Причина: {reason}"
        return await self.log_to_thread("mail_rejected", message)
    
    # Методы для логирования разбора проблем
    async def log_problem_solved(self, employee_name: str, app_id: int, fio: str) -> bool:
        """Логировать исправление проблемы"""
        message = f"✅ <b>Разбор проблем: Исправлено</b>\n👤 {employee_name}\n📋 ID: {app_id}\n👨‍💼 {fio}"
        return await self.log_to_thread("problem_solved", message)
    
    async def log_problem_solved_queue(self, employee_name: str, app_id: int, fio: str, queue_type: str) -> bool:
        """Логировать исправление и отправку в очередь"""
        queue_name = {
            'lk': 'ЛК',
            'epgu': 'ЕПГУ',
            'epgu_mail': 'ЕПГУ (почта)'
        }.get(queue_type, queue_type)
        message = f"🔄 <b>Разбор проблем: Исправлено и отправлено в очередь</b>\n👤 {employee_name}\n📋 ID: {app_id}\n👨‍💼 {fio}\n📋 Очередь: {queue_name}"
        return await self.log_to_thread("problem_solved_queue", message)
    
    async def log_problem_in_progress(self, employee_name: str, app_id: int, fio: str) -> bool:
        """Логировать запуск процесса решения проблемы"""
        message = f"🔄 <b>Разбор проблем: Процесс решения запущен</b>\n👤 {employee_name}\n📋 ID: {app_id}\n👨‍💼 {fio}"
        return await self.log_to_thread("problem_in_progress", message)
    
    # Методы для логирования очередей
    async def log_queue_updated(self, queue_type: str, employee_name: str, count: int) -> bool:
        """Логировать обновление очереди"""
        queue_name = {
            'lk': 'ЛК',
            'epgu': 'ЕПГУ',
            'epgu_mail': 'ЕПГУ (почта)',
            'epgu_problem': 'ЕПГУ (проблемы)'
        }.get(queue_type, queue_type)
        message = f"📊 <b>Обновлен список заявлений</b>\n📋 Очередь: {queue_name}\n👤 Кем: {employee_name}\n➕ Добавлено: {count}"
        return await self.log_to_thread("queue_updated", message)
    
    # Методы для логирования эскалации
    async def log_escalation(self, app_id: int, queue_type: str, employee_name: str, reason: str) -> bool:
        """Логировать эскалацию"""
        queue_name = {
            'lk': 'ЛК',
            'epgu': 'ЕПГУ',
            'epgu_mail': 'ЕПГУ (почта)',
            'epgu_problem': 'ЕПГУ (проблемы)'
        }.get(queue_type, queue_type)
        message = f"🚨 <b>Эскалация</b>\n📋 ID заявления: {app_id}\n📋 Очередь: {queue_name}\n👤 Кем: {employee_name}\n📝 Причина: {reason}"
        return await self.log_to_thread("escalation", message)

# Глобальный экземпляр логгера
telegram_logger: Optional[TelegramLogger] = None

def init_logger(bot: Bot):
    """Инициализировать глобальный логгер"""
    global telegram_logger
    telegram_logger = TelegramLogger(bot)

def get_logger() -> Optional[TelegramLogger]:
    """Получить глобальный логгер"""
    return telegram_logger 
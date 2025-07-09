#!/usr/bin/env python3
"""
Тестовый скрипт для проверки подсчета заявлений
"""
import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(__file__))

from db.crud import get_employee_by_tg_id, get_current_work_day, increment_processed_applications, start_work_day, get_work_day_report
from db.session import engine
from db.models import Base
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_counting():
    """Тестируем подсчет заявлений"""
    print("=== ТЕСТ ПОДСЧЕТА ЗАЯВЛЕНИЙ ===")
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Тестируем с конкретным employee_id (замените на реальный ID)
    test_employee_id = 2  # Замените на реальный ID сотрудника
    
    print(f"Тестируем для employee_id={test_employee_id}")
    
    # Проверяем текущий рабочий день
    work_day = await get_current_work_day(test_employee_id)
    print(f"Текущий рабочий день: {work_day}")
    
    if work_day:
        print(f"Текущий счетчик заявлений: {work_day.applications_processed}")
    else:
        print("Рабочий день не найден, создаем новый...")
        work_day = await start_work_day(test_employee_id)
        print(f"Создан новый рабочий день: {work_day}")
    
    # Увеличиваем счетчик несколько раз
    print("\nУвеличиваем счетчик заявлений 3 раза...")
    for i in range(3):
        result = await increment_processed_applications(test_employee_id)
        print(f"Попытка {i+1}: результат = {result}")
    
    # Проверяем результат
    work_day = await get_current_work_day(test_employee_id)
    if work_day:
        print(f"Финальный счетчик заявлений: {work_day.applications_processed}")
    else:
        print("Ошибка: рабочий день не найден после увеличения")
    
    # Проверяем через отчет
    report = await get_work_day_report(test_employee_id)
    if report:
        print(f"Отчет: applications_processed = {report['applications_processed']}")
    else:
        print("Отчет не найден")

if __name__ == "__main__":
    asyncio.run(test_counting()) 
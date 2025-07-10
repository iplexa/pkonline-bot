#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений рабочего времени
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.crud import (
    add_employee, 
    add_group_to_employee, 
    start_work_day,
    start_break,
    end_break,
    end_work_day,
    get_current_work_day,
    get_active_break,
    get_work_day_report
)
from db.models import WorkDayStatusEnum
from datetime import datetime

async def test_work_time():
    """Тестируем исправления рабочего времени"""
    print("⏰ Тестирование исправлений рабочего времени...")
    
    # 1. Создаем тестового сотрудника
    test_tg_id = "555666777"
    test_fio = "Тестовый Сотрудник Время"
    
    print(f"1. Создаем сотрудника: {test_fio}")
    emp = await add_employee(test_tg_id, test_fio)
    print(f"   ✅ Сотрудник создан: ID={emp.id}")
    
    # 2. Добавляем сотрудника в группу ЛК
    print("2. Добавляем в группу ЛК")
    result = await add_group_to_employee(test_tg_id, "lk")
    print(f"   ✅ Результат: {result}")
    
    # 3. Начинаем рабочий день
    print("3. Начинаем рабочий день")
    work_day = await start_work_day(emp.id)
    print(f"   ✅ Рабочий день начат: ID={work_day.id}, статус={work_day.status.value}")
    
    # 4. Проверяем текущий рабочий день
    print("4. Проверяем текущий рабочий день")
    current_day = await get_current_work_day(emp.id)
    print(f"   ✅ Текущий день: ID={current_day.id}, статус={current_day.status.value}")
    
    # 5. Начинаем перерыв
    print("5. Начинаем перерыв")
    work_break = await start_break(emp.id)
    print(f"   ✅ Перерыв начат: ID={work_break.id}")
    
    # 6. Проверяем статус после начала перерыва
    print("6. Проверяем статус после начала перерыва")
    current_day_after_break = await get_current_work_day(emp.id)
    print(f"   ✅ Статус рабочего дня: {current_day_after_break.status.value}")
    
    # 7. Проверяем активный перерыв
    print("7. Проверяем активный перерыв")
    active_break = await get_active_break(current_day_after_break.id)
    print(f"   ✅ Активный перерыв: {'есть' if active_break else 'нет'}")
    
    # 8. Завершаем перерыв
    print("8. Завершаем перерыв")
    ended_break = await end_break(emp.id)
    print(f"   ✅ Перерыв завершен: продолжительность={ended_break.duration} сек")
    
    # 9. Проверяем статус после завершения перерыва
    print("9. Проверяем статус после завершения перерыва")
    current_day_after_end_break = await get_current_work_day(emp.id)
    print(f"   ✅ Статус рабочего дня: {current_day_after_end_break.status.value}")
    
    # 10. Завершаем рабочий день
    print("10. Завершаем рабочий день")
    ended_work_day = await end_work_day(emp.id)
    print(f"   ✅ Рабочий день завершен: статус={ended_work_day.status.value}")
    
    # 11. Получаем отчет
    print("11. Получаем отчет")
    report = await get_work_day_report(emp.id)
    if report:
        print(f"   ✅ Отчет получен:")
        print(f"      - Время работы: {report['total_work_time']} сек")
        print(f"      - Время перерывов: {report['total_break_time']} сек")
        print(f"      - Статус: {report['status']}")
        print(f"      - Перерывы: {len(report['breaks'])}")
    else:
        print("   ❌ Отчет не получен")
    
    print("\n✅ Тест рабочего времени завершен!")

if __name__ == "__main__":
    asyncio.run(test_work_time()) 
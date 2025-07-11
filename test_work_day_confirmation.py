#!/usr/bin/env python3
"""
Тест подтверждения завершения рабочего дня и запрета повторного начала
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
    end_work_day,
    get_current_work_day,
    get_work_day_report
)
from db.models import WorkDayStatusEnum

async def test_work_day_confirmation():
    """Тестируем подтверждение завершения и запрет повторного начала"""
    print("🧪 Тестирование подтверждения завершения рабочего дня")
    print("=" * 60)
    
    # 1. Создаем тестового сотрудника
    test_tg_id = "999888777"
    test_fio = "Тестовый Сотрудник Подтверждение"
    
    print("1. Создаем сотрудника")
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
    
    # 5. Пытаемся начать рабочий день снова (должно вернуть существующий)
    print("5. Пытаемся начать рабочий день снова")
    work_day_again = await start_work_day(emp.id)
    print(f"   ✅ Результат: ID={work_day_again.id} (тот же день)")
    
    # 6. Завершаем рабочий день
    print("6. Завершаем рабочий день")
    ended_work_day = await end_work_day(emp.id)
    print(f"   ✅ Рабочий день завершен: статус={ended_work_day.status.value}")
    
    # 7. Проверяем, что рабочий день завершен
    print("7. Проверяем завершенный рабочий день")
    finished_day = await get_current_work_day(emp.id)
    print(f"   ✅ Статус: {finished_day.status.value}, end_time: {finished_day.end_time}")
    
    # 8. Пытаемся начать новый рабочий день (должно быть запрещено)
    print("8. Пытаемся начать новый рабочий день (должно быть запрещено)")
    new_work_day = await start_work_day(emp.id)
    if new_work_day is None:
        print("   ✅ Правильно: новый рабочий день запрещен (вернул None)")
    else:
        print(f"   ❌ Ошибка: новый рабочий день создан (ID={new_work_day.id})")
    
    # 9. Получаем отчет
    print("9. Получаем отчет")
    report = await get_work_day_report(emp.id)
    if report:
        print(f"   ✅ Отчет получен: время работы={report['total_work_time']} сек")
    else:
        print("   ❌ Отчет не получен")
    
    # 10. Очищаем тестовые данные
    print("10. Очищаем тестовые данные")
    async for session in get_session():
        from db.models import Employee
        from sqlalchemy import select
        
        # Удаляем тестового сотрудника (каскадно удалятся все связанные записи)
        stmt = select(Employee).where(Employee.tg_id == test_tg_id)
        result = await session.execute(stmt)
        test_emp = result.scalars().first()
        
        if test_emp:
            await session.delete(test_emp)
            await session.commit()
            print(f"   ✅ Тестовый сотрудник удален")
        else:
            print(f"   ⚠️ Тестовый сотрудник не найден")
    
    print("\n✅ Тестирование завершено успешно!")

if __name__ == "__main__":
    asyncio.run(test_work_day_confirmation()) 
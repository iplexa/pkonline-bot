#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы ЕПГУ
"""
import asyncio
import sys
import os

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.crud import (
    add_employee, 
    add_group_to_employee, 
    add_application, 
    get_employee_by_tg_id,
    get_applications_by_queue_type,
    get_all_work_days_report
)
from db.models import ApplicationStatusEnum
from datetime import datetime

async def test_epgu():
    """Тестируем работу ЕПГУ"""
    print("🧪 Тестирование ЕПГУ...")
    
    # 1. Создаем тестового сотрудника
    test_tg_id = "123456789"
    test_fio = "Тестовый Сотрудник ЕПГУ"
    
    print(f"1. Создаем сотрудника: {test_fio}")
    emp = await add_employee(test_tg_id, test_fio)
    print(f"   ✅ Сотрудник создан: ID={emp.id}")
    
    # 2. Добавляем сотрудника в группу ЕПГУ
    print("2. Добавляем в группу ЕПГУ")
    result = await add_group_to_employee(test_tg_id, "epgu")
    print(f"   ✅ Результат: {result}")
    
    # 3. Добавляем тестовые заявления в очередь ЕПГУ
    print("3. Добавляем тестовые заявления")
    test_applications = [
        {"fio": "Иванов И.И.", "submitted_at": datetime.now()},
        {"fio": "Петров П.П.", "submitted_at": datetime.now()},
        {"fio": "Сидоров С.С.", "submitted_at": datetime.now()},
    ]
    
    for app_data in test_applications:
        app = await add_application(
            fio=app_data["fio"],
            submitted_at=app_data["submitted_at"],
            queue_type="epgu"
        )
        print(f"   ✅ Заявление добавлено: {app.fio} (ID={app.id})")
    
    # 4. Проверяем заявления в очереди
    print("4. Проверяем очередь ЕПГУ")
    apps = await get_applications_by_queue_type("epgu")
    print(f"   📋 Заявлений в очереди: {len(apps)}")
    for app in apps:
        print(f"      - {app.fio} (статус: {app.status.value})")
    
    # 5. Проверяем отчеты
    print("5. Проверяем отчеты")
    reports = await get_all_work_days_report()
    print(f"   📊 Отчетов за сегодня: {len(reports)}")
    for report in reports:
        print(f"      - {report['employee_fio']}: {report['applications_processed']} заявлений")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_epgu()) 
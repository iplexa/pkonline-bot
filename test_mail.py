#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы очереди почты
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
    add_application, 
    get_employee_by_tg_id,
    get_applications_by_queue_type,
    get_applications_by_fio_and_queue,
    get_all_work_days_report,
    update_application_queue_type
)
from db.models import ApplicationStatusEnum
from datetime import datetime

async def test_mail():
    """Тестируем работу очереди почты"""
    print("📮 Тестирование очереди почты...")
    
    # 1. Создаем тестового сотрудника
    test_tg_id = "987654321"
    test_fio = "Тестовый Сотрудник Почты"
    
    print(f"1. Создаем сотрудника: {test_fio}")
    emp = await add_employee(test_tg_id, test_fio)
    print(f"   ✅ Сотрудник создан: ID={emp.id}")
    
    # 2. Добавляем сотрудника в группу почты
    print("2. Добавляем в группу почты")
    result = await add_group_to_employee(test_tg_id, "mail")
    print(f"   ✅ Результат: {result}")
    
    # 3. Добавляем тестовые заявления в очередь почты
    print("3. Добавляем тестовые заявления в очередь почты")
    test_applications = [
        {"fio": "Иванов Иван Иванович", "submitted_at": datetime.now() - timedelta(hours=2)},
        {"fio": "Петров Петр Петрович", "submitted_at": datetime.now() - timedelta(hours=1)},
        {"fio": "Сидоров Сидор Сидорович", "submitted_at": datetime.now()},
        {"fio": "Иванов Иван Иванович", "submitted_at": datetime.now() - timedelta(days=1)},  # Дубликат ФИО
    ]
    
    for app_data in test_applications:
        app = await add_application(
            fio=app_data["fio"],
            submitted_at=app_data["submitted_at"],
            queue_type="epgu_mail"
        )
        print(f"   ✅ Заявление добавлено: {app.fio} (ID={app.id})")
    
    # 4. Проверяем заявления в очереди почты
    print("4. Проверяем очередь почты")
    apps = await get_applications_by_queue_type("epgu_mail")
    print(f"   📋 Заявлений в очереди почты: {len(apps)}")
    for app in apps:
        print(f"      - {app.fio} (статус: {app.status.value})")
    
    # 5. Тестируем поиск по ФИО
    print("5. Тестируем поиск по ФИО")
    search_fio = "Иванов"
    found_apps = await get_applications_by_fio_and_queue(search_fio, "epgu_mail")
    print(f"   🔍 Найдено заявлений для '{search_fio}': {len(found_apps)}")
    for app in found_apps:
        print(f"      - {app.fio} | {app.submitted_at.strftime('%d.%m.%Y %H:%M')} | ID: {app.id}")
    
    # 6. Тестируем поиск по полному ФИО
    print("6. Тестируем поиск по полному ФИО")
    search_fio_full = "Иванов Иван Иванович"
    found_apps_full = await get_applications_by_fio_and_queue(search_fio_full, "epgu_mail")
    print(f"   🔍 Найдено заявлений для '{search_fio_full}': {len(found_apps_full)}")
    for app in found_apps_full:
        print(f"      - {app.fio} | {app.submitted_at.strftime('%d.%m.%Y %H:%M')} | ID: {app.id}")
    
    # 7. Проверяем отчеты
    print("7. Проверяем отчеты")
    reports = await get_all_work_days_report()
    print(f"   📊 Отчетов за сегодня: {len(reports)}")
    for report in reports:
        print(f"      - {report['employee_fio']}: {report['applications_processed']} заявлений")
    
    print("\n✅ Тест очереди почты завершен!")

if __name__ == "__main__":
    asyncio.run(test_mail()) 
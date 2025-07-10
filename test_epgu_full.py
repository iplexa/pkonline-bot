#!/usr/bin/env python3
"""
Полный тестовый скрипт для проверки работы ЕПГУ
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
    get_all_work_days_report,
    get_applications_statistics_by_queue,
    get_next_epgu_application,
    update_application_queue_type,
    postpone_application,
    start_work_day
)
from db.models import ApplicationStatusEnum
from datetime import datetime

async def test_epgu_full():
    """Полный тест функциональности ЕПГУ"""
    print("🧪 ПОЛНЫЙ ТЕСТ ЕПГУ...")
    
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
    
    # 3. Начинаем рабочий день
    print("3. Начинаем рабочий день")
    work_day = await start_work_day(emp.id)
    print(f"   ✅ Рабочий день: {work_day.id if work_day else 'не создан'}")
    
    # 4. Добавляем тестовые заявления в очередь ЕПГУ
    print("4. Добавляем тестовые заявления")
    test_applications = [
        {"fio": "Иванов И.И.", "submitted_at": datetime.now() - timedelta(hours=2)},
        {"fio": "Петров П.П.", "submitted_at": datetime.now() - timedelta(hours=1)},
        {"fio": "Сидоров С.С.", "submitted_at": datetime.now()},
    ]
    
    for app_data in test_applications:
        app = await add_application(
            fio=app_data["fio"],
            submitted_at=app_data["submitted_at"],
            queue_type="epgu"
        )
        print(f"   ✅ Заявление добавлено: {app.fio} (ID={app.id})")
    
    # 5. Проверяем заявления в очереди
    print("5. Проверяем очередь ЕПГУ")
    apps = await get_applications_by_queue_type("epgu")
    print(f"   📋 Заявлений в очереди: {len(apps)}")
    for app in apps:
        print(f"      - {app.fio} (статус: {app.status.value})")
    
    # 6. Тестируем получение заявления
    print("6. Тестируем получение заявления")
    next_app = await get_next_epgu_application(employee_id=emp.id)
    if next_app:
        print(f"   ✅ Получено заявление: {next_app.fio} (ID={next_app.id})")
        app_id = next_app.id
    else:
        print("   ❌ Заявление не получено")
        return
    
    # 7. Тестируем действия с заявлением
    print("7. Тестируем действия с заявлением")
    
    # 7.1. Отправляем на подпись
    print("   7.1. Отправляем на подпись")
    await update_application_queue_type(app_id, "epgu_mail", employee_id=emp.id)
    print("   ✅ Заявление отправлено на подпись")
    
    # 7.2. Добавляем еще одно заявление и откладываем его
    print("   7.2. Добавляем заявление для откладывания")
    app2 = await add_application(
        fio="Отложенный И.И.",
        submitted_at=datetime.now(),
        queue_type="epgu"
    )
    next_app2 = await get_next_epgu_application(employee_id=emp.id)
    if next_app2:
        await postpone_application(next_app2.id, employee_id=emp.id)
        print(f"   ✅ Заявление {next_app2.fio} отложено на сутки")
    
    # 7.3. Добавляем проблемное заявление
    print("   7.3. Добавляем проблемное заявление")
    app3 = await add_application(
        fio="Проблемный И.И.",
        submitted_at=datetime.now(),
        queue_type="epgu"
    )
    next_app3 = await get_next_epgu_application(employee_id=emp.id)
    if next_app3:
        await update_application_queue_type(next_app3.id, "epgu_problem", employee_id=emp.id, reason="Тестовая проблема")
        print(f"   ✅ Заявление {next_app3.fio} помечено как проблемное")
    
    # 8. Проверяем статистику по очередям
    print("8. Проверяем статистику по очередям")
    queue_stats = await get_applications_statistics_by_queue()
    print(f"   📊 Статистика: {queue_stats}")
    
    # 9. Проверяем отчеты
    print("9. Проверяем отчеты")
    reports = await get_all_work_days_report()
    print(f"   📈 Отчетов за сегодня: {len(reports)}")
    for report in reports:
        print(f"      - {report['employee_fio']}: {report['applications_processed']} заявлений")
    
    # 10. Проверяем заявления в разных очередях
    print("10. Проверяем заявления в разных очередях")
    for queue_type in ['epgu', 'epgu_mail', 'epgu_problem']:
        apps = await get_applications_by_queue_type(queue_type)
        print(f"   📋 {queue_type}: {len(apps)} заявлений")
        for app in apps:
            print(f"      - {app.fio} (обработал: {app.processed_by.fio if app.processed_by else 'нет'})")
    
    print("\n✅ ПОЛНЫЙ ТЕСТ ЕПГУ ЗАВЕРШЕН!")

if __name__ == "__main__":
    asyncio.run(test_epgu_full()) 
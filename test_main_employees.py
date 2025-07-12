#!/usr/bin/env python3
"""
Тест функции создания основных сотрудников
"""

import asyncio
import sys
import os

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.crud import get_employee_by_tg_id, add_employee, add_group_to_employee
from db.session import get_session

async def test_main_employees():
    """Тестирует создание основных сотрудников"""
    
    print("=== Тест создания основных сотрудников ===")
    
    # Основные сотрудники с группами
    main_employees = [
        {
            "tg_id": "2019439815", 
            "fio": "Чернякова Ксения Владленовна",
            "groups": ["lk", "epgu", "mail", "problem"]
        },
        {
            "tg_id": "1329555538", 
            "fio": "Мукумова Виктория Денисовна",
            "groups": ["lk", "epgu", "mail", "problem"]
        },
        {
            "tg_id": "5163143779", 
            "fio": "Горячева Диана Александровна",
            "groups": ["lk"]
        },
        {
            "tg_id": "1059622323", 
            "fio": "Крюкова Полина Андреевна",
            "groups": ["lk"]
        },
        {
            "tg_id": "945793471", 
            "fio": "Кожанова Арина Александровна",
            "groups": ["lk"]
        },
        {
            "tg_id": "1395039679", 
            "fio": "Картоева Раяна Юнусовна",
            "groups": ["lk"]
        }
    ]
    
    added_count = 0
    already_exists_count = 0
    groups_added_count = 0
    
    print("Начинаю создание сотрудников...")
    
    for emp_data in main_employees:
        print(f"\nОбрабатываю: {emp_data['fio']} (ID: {emp_data['tg_id']})")
        
        # Проверяем, существует ли уже сотрудник
        existing_emp = await get_employee_by_tg_id(emp_data["tg_id"])
        if existing_emp:
            print(f"  ⚠️ Сотрудник уже существует")
            already_exists_count += 1
            # Добавляем группы к существующему сотруднику
            for group in emp_data["groups"]:
                try:
                    await add_group_to_employee(emp_data["tg_id"], group)
                    groups_added_count += 1
                    print(f"  ✅ Добавлена группа: {group}")
                except Exception as e:
                    print(f"  ❌ Ошибка при добавлении группы {group}: {e}")
            continue
        
        # Добавляем сотрудника
        try:
            await add_employee(emp_data["tg_id"], emp_data["fio"])
            added_count += 1
            print(f"  ✅ Сотрудник добавлен")
            
            # Добавляем группы к новому сотруднику
            for group in emp_data["groups"]:
                try:
                    await add_group_to_employee(emp_data["tg_id"], group)
                    groups_added_count += 1
                    print(f"  ✅ Добавлена группа: {group}")
                except Exception as e:
                    print(f"  ❌ Ошибка при добавлении группы {group}: {e}")
                    
        except Exception as e:
            print(f"  ❌ Ошибка при добавлении сотрудника: {e}")
    
    # Формируем отчет
    print(f"\n=== ОТЧЕТ ===")
    print(f"➕ Добавлено сотрудников: {added_count}")
    print(f"⚠️ Уже существовало: {already_exists_count}")
    print(f"🏷️ Добавлено групп: {groups_added_count}")
    
    if added_count > 0:
        print(f"\nДобавленные сотрудники:")
        for emp_data in main_employees:
            groups_str = ", ".join(emp_data["groups"])
            print(f"• {emp_data['fio']} (ID: {emp_data['tg_id']})")
            print(f"  Группы: {groups_str}")
    
    print("\n✅ Тест завершен!")

if __name__ == "__main__":
    asyncio.run(test_main_employees()) 
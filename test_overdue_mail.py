#!/usr/bin/env python3
"""
Тест функциональности экспорта просроченных заявлений почты
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Добавляем корневую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from db.session import get_session
from db.models import Application, ApplicationStatusEnum, EPGUActionEnum
from db.crud import get_overdue_mail_applications, export_overdue_mail_applications_to_excel, get_moscow_now
from sqlalchemy import select

async def test_overdue_mail_functionality():
    """Тестирует функциональность работы с просроченными заявлениями почты"""
    
    print("🧪 Тестирование функциональности просроченных заявлений почты")
    print("=" * 60)
    
    # 1. Создаем тестовые заявления в очереди почты
    print("1. Создаем тестовые заявления в очереди почты")
    
    async for session in get_session():
        # Очищаем старые тестовые заявления
        await session.execute(
            select(Application).where(Application.fio.like("Тест%"))
        )
        test_apps = await session.execute(
            select(Application).where(Application.fio.like("Тест%"))
        )
        for app in test_apps.scalars().all():
            await session.delete(app)
        
        # Создаем заявления с разными датами
        now = get_moscow_now()
        
        # Заявление, ждущее ответа 5 дней (просроченное)
        app1 = Application(
            fio="Тест Просроченный И.И.",
            submitted_at=now - timedelta(days=10),
            queue_type="epgu_mail",
            status=ApplicationStatusEnum.QUEUED,
            postponed_until=now - timedelta(days=5),
            epgu_action=EPGUActionEnum.SIGNATURE,
            needs_signature=True,
            needs_scans=False
        )
        
        # Заявление, ждущее ответа 1 день (не просроченное)
        app2 = Application(
            fio="Тест Актуальный И.И.",
            submitted_at=now - timedelta(days=5),
            queue_type="epgu_mail",
            status=ApplicationStatusEnum.QUEUED,
            postponed_until=now - timedelta(days=1),
            epgu_action=EPGUActionEnum.SCANS,
            needs_signature=False,
            needs_scans=True
        )
        
        # Заявление, ждущее ответа 7 дней (просроченное)
        app3 = Application(
            fio="Тест Очень Просроченный И.И.",
            submitted_at=now - timedelta(days=15),
            queue_type="epgu_mail",
            status=ApplicationStatusEnum.QUEUED,
            postponed_until=now - timedelta(days=7),
            epgu_action=EPGUActionEnum.SIGNATURE_SCANS,
            needs_signature=True,
            needs_scans=True
        )
        
        session.add_all([app1, app2, app3])
        await session.commit()
        
        print(f"   ✅ Создано 3 тестовых заявления")
    
    # 2. Тестируем получение просроченных заявлений
    print("2. Тестируем получение просроченных заявлений")
    
    # Получаем заявления, ждущие ответа более 3 дней
    overdue_apps = await get_overdue_mail_applications(days_threshold=3)
    print(f"   📋 Найдено просроченных заявлений (более 3 дней): {len(overdue_apps)}")
    
    for app in overdue_apps:
        days_waiting = (get_moscow_now() - app.postponed_until).days
        print(f"      - {app.fio}: ждет {days_waiting} дней")
    
    # Получаем заявления, ждущие ответа более 1 дня
    overdue_apps_1_day = await get_overdue_mail_applications(days_threshold=1)
    print(f"   📋 Найдено просроченных заявлений (более 1 дня): {len(overdue_apps_1_day)}")
    
    # 3. Тестируем экспорт в Excel
    print("3. Тестируем экспорт в Excel")
    
    filename, message = await export_overdue_mail_applications_to_excel(days_threshold=3)
    
    if filename:
        print(f"   ✅ Файл создан: {filename}")
        print(f"   📝 Сообщение: {message}")
        
        # Проверяем, что файл существует
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"   📊 Размер файла: {file_size} байт")
            
            # Удаляем тестовый файл
            os.unlink(filename)
            print(f"   🗑️ Тестовый файл удален")
        else:
            print(f"   ❌ Файл не найден")
    else:
        print(f"   ℹ️ {message}")
    
    # 4. Очищаем тестовые данные
    print("4. Очищаем тестовые данные")
    
    async for session in get_session():
        test_apps = await session.execute(
            select(Application).where(Application.fio.like("Тест%"))
        )
        for app in test_apps.scalars().all():
            await session.delete(app)
        await session.commit()
        print(f"   ✅ Удалено {len(test_apps.scalars().all())} тестовых заявлений")
    
    print("\n✅ Тестирование завершено успешно!")

if __name__ == "__main__":
    asyncio.run(test_overdue_mail_functionality()) 
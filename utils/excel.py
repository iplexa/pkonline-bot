import pandas as pd
from datetime import datetime

def parse_lk_applications_from_excel(file_path: str):
    df = pd.read_excel(file_path)
    # Фильтрация
    filtered = []
    seen_fio = set()
    for _, row in df.iterrows():
        fio = str(row["Физическое лицо"]).strip()
        status = str(row["Статус заявления в ПК"]).strip().lower()
        changes = str(row["Есть изменения"]).strip().lower()
        date_str = str(row["Дата первой подачи"]).strip()
        try:
            submitted_at = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        except Exception:
            try:
                submitted_at = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
            except Exception:
                continue
        if fio in seen_fio:
            continue
        if status == "подано":
            filtered.append({"fio": fio, "submitted_at": submitted_at, "priority": False})
            seen_fio.add(fio)
        elif status == "на рассмотрении" and changes == "да":
            filtered.append({"fio": fio, "submitted_at": submitted_at, "priority": True})
            seen_fio.add(fio)
    # Сортировка: сначала priority=True, потом False, внутри — по дате
    filtered.sort(key=lambda x: (not x["priority"], x["submitted_at"]))
    return filtered

def parse_epgu_applications_from_excel(file_path: str):
    print("=== Вызвана функция parse_epgu_applications_from_excel ===")
    df = pd.read_excel(file_path)
    print(f"Колонки в файле: {list(df.columns)}")
    filtered = []
    seen = set()
    fio_column = None
    date_column = None
    for col in df.columns:
        col_lower = str(col).lower()
        if any(word in col_lower for word in ['фио', 'заявитель', 'физ', 'лицо']):
            fio_column = col
        elif any(word in col_lower for word in ['дата', 'подач']):
            date_column = col
    if not fio_column and len(df.columns) > 0:
        fio_column = df.columns[0]
    if not date_column and len(df.columns) > 1:
        date_column = df.columns[1]
    for _, row in df.iterrows():
        fio = str(row[fio_column]).strip() if fio_column else None
        date_str = str(row[date_column]).strip() if date_column else None
        if not fio or fio == 'nan' or not date_str or date_str == 'nan':
            continue
        try:
            submitted_at = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        except Exception:
            try:
                submitted_at = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
            except Exception:
                try:
                    submitted_at = datetime.strptime(date_str, "%d.%m.%Y")
                except Exception:
                    continue
        key = (fio, submitted_at)
        if key in seen:
            continue
        filtered.append({"fio": fio, "submitted_at": submitted_at})
        seen.add(key)
    filtered.sort(key=lambda x: x["submitted_at"])
    print(f"Найдено строк для импорта: {len(filtered)}")
    return filtered

async def parse_1c_applications_from_excel(file_path: str, progress_callback=None, existing_fios_by_queue=None):
    """
    Парсинг выгрузки из 1С для обработки заявлений ЛК и ЕПГУ
    existing_fios_by_queue: dict[str, set[str]] — ФИО, уже присутствующие в каждой очереди
    """
    print("=== Вызвана функция parse_1c_applications_from_excel ===")
    df = pd.read_excel(file_path)
    print(f"Колонки в файле: {list(df.columns)}")
    print(f"Всего строк в файле: {len(df)}")
    
    lk_applications = []
    epgu_applications = []
    unknown_applications = []
    
    processed_count = 0
    if existing_fios_by_queue is None:
        existing_fios_by_queue = {}
    # Собираем все ФИО из "проблемных" и почтовых очередей в один set
    skip_fios = set()
    for q in ["lk_problem", "epgu_mail", "epgu_problem", "epgu", "lk"]:
        skip_fios.update(existing_fios_by_queue.get(q, set()))
    
    for _, row in df.iterrows():
        processed_count += 1
        if processed_count % 150 == 0:
            progress_text = f"📊 Обработано строк: {processed_count}/{len(df)}"
            print(progress_text)
            if progress_callback:
                try:
                    await progress_callback(progress_text)
                except:
                    pass
        fio = str(row["Физическое лицо"]).strip()
        submission_method = str(row["Способ подачи заявления"]).strip()
        status = str(row["Статус заявления в ПК"]).strip()
        has_changes = str(row["Есть изменения"]).strip().lower()
        date_str = str(row["Дата первой подачи"]).strip()
        if not fio or fio == 'nan' or not date_str or date_str == 'nan':
            continue
        # Если ФИО уже есть в одной из "особых" очередей — пропускаем
        if fio in skip_fios:
            continue
        try:
            submitted_at = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        except Exception:
            try:
                submitted_at = datetime.strptime(date_str, "%d.%m.%Y %H:%M")
            except Exception:
                try:
                    submitted_at = datetime.strptime(date_str, "%d.%m.%Y")
                except Exception:
                    continue
        queue_type = None
        app_status = None
        is_priority = False
        status_reason = None
        # ЛК (СМС-подтверждение)
        if "СМС-подтверждение" in submission_method:
            queue_type = "lk"
            if status.lower() == "принято":
                app_status = "accepted"
            elif status.lower() == "подано":
                app_status = "queued"
            elif status.lower() == "на рассмотрении":
                if has_changes == "да":
                    app_status = "queued"
                    is_priority = True
                else:
                    app_status = "rejected"
                    status_reason = "загружено администратором"
            elif status.lower() == "редактируется":
                continue
            else:
                continue
        # ЕПГУ
        elif "ЕПГУ" in submission_method:
            queue_type = "epgu"
            if status.lower() == "принято":
                app_status = "accepted"
            elif status.lower() == "на рассмотрении":
                app_status = "queued"
            else:
                continue
        # Пустой способ подачи
        elif submission_method == "" and status.lower() == "подано":
            queue_type = "lk"
            app_status = "queued"
        # Пустой или нераспознанный способ подачи — отдельная очередь
        else:
            queue_type = "unknown"
            app_status = "queued"
            status_reason = f"Неизвестный способ подачи: '{submission_method}'"
        application = {
            "fio": fio,
            "submitted_at": submitted_at,
            "queue_type": queue_type,
            "status": app_status,
            "is_priority": is_priority,
            "status_reason": status_reason
        }
        if queue_type == "lk":
            lk_applications.append(application)
        elif queue_type == "epgu":
            epgu_applications.append(application)
        elif queue_type == "unknown":
            unknown_applications.append(application)
    lk_applications.sort(key=lambda x: (not x["is_priority"], x["submitted_at"]))
    epgu_applications.sort(key=lambda x: x["submitted_at"])
    unknown_applications.sort(key=lambda x: x["submitted_at"])
    final_text = f"✅ Обработка завершена. Всего обработано строк: {processed_count}"
    print(final_text)
    if progress_callback:
        try:
            await progress_callback(final_text)
        except:
            pass
    print(f"Найдено ЛК заявлений: {len(lk_applications)}")
    print(f"Найдено ЕПГУ заявлений: {len(epgu_applications)}")
    print(f"Найдено заявлений с неизвестным способом подачи: {len(unknown_applications)}")
    return {
        "lk": lk_applications,
        "epgu": epgu_applications,
        "unknown": unknown_applications
    }

def parse_epgu_mail_applications_from_excel(file_path: str):
    """
    Парсит excel-файл очереди ЕПГУ почта с колонками N, Физическое лицо, Email
    Возвращает список словарей с fio и email
    """
    df = pd.read_excel(file_path)
    filtered = []
    for _, row in df.iterrows():
        fio = str(row.get("Физическое лицо", "")).strip()
        email = str(row.get("Email", "")).strip()
        if fio and email and email != 'nan':
            filtered.append({"fio": fio, "email": email})
    return filtered 
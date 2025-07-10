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
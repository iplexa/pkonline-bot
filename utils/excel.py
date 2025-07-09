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
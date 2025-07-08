import pandas as pd
from datetime import datetime

def parse_applications_from_excel(file_path: str):
    df = pd.read_excel(file_path)
    applications = []
    for _, row in df.iterrows():
        fio = str(row["Физическое лицо"]).strip()
        date_str = str(row["Дата первой подачи"]).strip()
        submitted_at = datetime.strptime(date_str, "%d.%m.%Y %H:%M:%S")
        applications.append({
            "fio": fio,
            "submitted_at": submitted_at
        })
    return applications 
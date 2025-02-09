from typing import List
from pathlib import Path
import datetime as dt

from app.settings import settings


async def get_logs_from_files(logs_folder: Path = settings.app_log_path, back_days: int = 2) -> List[dict[str, str]]:

    logs = []
    cutoff_date = dt.datetime.now() - dt.timedelta(days=back_days)

    log_files: List[Path] = sorted(
        (f for f in logs_folder.iterdir() if f.is_file()),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    for file in log_files:
        file_mod_time = dt.datetime.fromtimestamp(file.stat().st_mtime)

        if file_mod_time >= cutoff_date:
            with open(file, "r", encoding="utf-8") as f:
                reversed_content = "".join(reversed(f.readlines()))  # Fully reverses content

                logs.append({
                    "filename": file.name,
                    "date": file_mod_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "content": reversed_content
                })

    return logs
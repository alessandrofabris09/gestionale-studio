import shutil
from pathlib import Path
from datetime import datetime


BASE_DIR = Path(__file__).resolve().parent

DB_FILE = BASE_DIR / "db.sqlite3"
MEDIA_DIR = BASE_DIR / "media"
BACKUP_DIR = BASE_DIR / "backup"

timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

backup_folder = BACKUP_DIR / f"backup_{timestamp}"
backup_folder.mkdir(parents=True, exist_ok=True)

if DB_FILE.exists():
    shutil.copy2(DB_FILE, backup_folder / "db.sqlite3")

if MEDIA_DIR.exists():
    shutil.copytree(MEDIA_DIR, backup_folder / "media")

print(f"Backup creato correttamente: {backup_folder}")
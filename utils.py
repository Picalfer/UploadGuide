import shutil
from pathlib import Path


def clear_temp_dir():
    """Очищает временную папку перед началом работы."""
    TEMP_DIR = Path("temp")
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)  # Удаляем папку и всё внутри
    TEMP_DIR.mkdir(exist_ok=True)  # Создаём заново

import shutil
from enum import Enum
from pathlib import Path


class Status(Enum):
    START = "Программа готова к работе"
    CONVERTING = "Материал конвертируется в HTML"
    PROCESSING = "Обработка файлов"
    REQUESTING = "Идёт запрос данных с сервера"
    SELECTING = "Выберите куда загрузить материал"
    UPLOADING = "Идёт выгрузка материала"
    SUCCESS = "Материал успешно загружен"
    ERROR = "Произошла ошибка"


def clear_temp_dir():
    """Очищает временную папку перед началом работы."""
    TEMP_DIR = Path("temp")
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)  # Удаляем папку и всё внутри
    TEMP_DIR.mkdir(exist_ok=True)  # Создаём заново

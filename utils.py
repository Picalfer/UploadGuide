import os
import shutil
import sys
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


def get_resource_path(relative_path):
    """Корректно находит путь к файлам, даже внутри exe"""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

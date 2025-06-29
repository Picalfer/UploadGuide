import os
import json
from typing import Optional

CACHE_FILE = "last_level_cache.json"


def save_last_level(level_id: int) -> None:
    """Сохраняет последний использованный level_id в файл"""
    cache_dir = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(cache_dir, CACHE_FILE)

    with open(cache_path, 'w') as f:
        json.dump({"last_level_id": level_id}, f)


def load_last_level() -> Optional[int]:
    """Загружает последний использованный level_id из файла"""
    cache_dir = os.path.dirname(os.path.abspath(__file__))
    cache_path = os.path.join(cache_dir, CACHE_FILE)

    if not os.path.exists(cache_path):
        return None

    try:
        with open(cache_path, 'r') as f:
            data = json.load(f)
            return data.get("last_level_id")
    except (json.JSONDecodeError, KeyError):
        return None
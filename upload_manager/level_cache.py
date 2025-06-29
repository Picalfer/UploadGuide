import json
import os
from typing import Optional

CACHE_FILE = "last_level_cache.json"


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


def save_last_level(level_id: int, next_order: Optional[int] = None) -> None:
    """Сохраняет последний использованный level_id и order"""
    data = {"last_level_id": level_id}
    if next_order is not None:
        data["next_order"] = next_order + 1

    with open(CACHE_FILE, 'w') as f:
        json.dump(data, f)


def load_next_order() -> Optional[int]:
    """Загружает последний использованный order"""
    if not os.path.exists(CACHE_FILE):
        return None

    try:
        with open(CACHE_FILE, 'r') as f:
            data = json.load(f)
            return data.get("next_order")
    except (json.JSONDecodeError, KeyError):
        return None

import os
from typing import Dict, Tuple

import requests

from constants import API_GUIDE_UPLOAD


def load_auth_config(config_path: str = 'api_config.txt') -> Tuple[str, str]:
    """Загружает логин/пароль из файла"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Конфиг файл не найден: {config_path}")

    with open(config_path, 'r') as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]

    if len(lines) < 2:
        raise ValueError("Неверный формат конфиг файла. Нужны: логин, пароль")

    return lines[0], lines[1]


def upload_guide(
        html_path: str,
        zip_path: str,
        level_id: int,
        title: str,
        config_path: str = 'api_config.txt',
        order: int = 0
) -> Dict:
    """Базовая функция загрузки файлов на сервер"""
    if not all(os.path.exists(p) for p in [html_path, zip_path]):
        raise FileNotFoundError("Один из файлов не найден")

    auth = load_auth_config(config_path)

    with open(html_path, 'rb') as html_file, open(zip_path, 'rb') as assets_file:
        response = requests.post(
            url=API_GUIDE_UPLOAD,
            files={
                'html_file': html_file,
                'assets_zip': assets_file
            },
            data={
                'level_id': level_id,
                'title': title,
                'order': order
            },
            auth=auth
        )
        response.raise_for_status()
        return response.json()

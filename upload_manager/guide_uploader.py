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
        level_id: int,
        title: str,
        config_path: str = 'api_config.txt',
        order: int = 0,
        zip_path: str = None  # Делаем параметр опциональным
) -> Dict:
    """Функция загрузки файлов на сервер (zip-архив опционален)"""
    if not os.path.exists(html_path):
        raise FileNotFoundError(f"HTML файл не найден: {html_path}")

    if zip_path and not os.path.exists(zip_path):
        raise FileNotFoundError(f"ZIP архив не найден: {zip_path}")

    auth = load_auth_config(config_path)

    # Подготавливаем файлы для отправки
    files = {
        'html_file': open(html_path, 'rb')
    }
    if zip_path:
        files['assets_zip'] = open(zip_path, 'rb')

    try:
        response = requests.post(
            url=API_GUIDE_UPLOAD,
            files=files,
            data={
                'level_id': level_id,
                'title': title,
                'order': order
            },
            auth=auth
        )
        response.raise_for_status()
        return response.json()
    finally:
        # Закрываем все открытые файлы
        for file in files.values():
            file.close()

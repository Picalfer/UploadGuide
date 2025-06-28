import os
from typing import Tuple, Dict

import requests


class GuideUploader:
    def __init__(self, config_path: str = 'api_config.txt'):
        self.api_url, self.auth = self._load_config(config_path)

    def _load_config(self, config_path: str) -> Tuple[str, Tuple[str, str]]:
        """Загружает конфигурацию из файла"""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Конфиг файл не найден: {config_path}")

        with open(config_path, 'r') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]

        if len(lines) < 3:
            raise ValueError("Неверный формат конфиг файла. Нужны: URL, логин, пароль")

        return lines[0], (lines[1], lines[2])

    def upload_guide(self, html_path: str, zip_path: str, level_id: int, title: str, order: int = 0) -> Dict:
        """Загружает методичку на сервер"""
        if not all(os.path.exists(p) for p in [html_path, zip_path]):
            raise FileNotFoundError("Один из файлов не найден")

        try:
            with open(html_path, 'rb') as html_file, open(zip_path, 'rb') as assets_file:
                files = {
                    'html_file': html_file,
                    'assets_zip': assets_file
                }
                data = {
                    'level_id': level_id,
                    'title': title,
                    'order': order
                }

                response = requests.post(
                    url=self.api_url,
                    files=files,
                    data=data,
                    auth=self.auth
                )
                response.raise_for_status()
                return response.json()

        except requests.exceptions.RequestException as e:
            raise Exception(f"Ошибка при загрузке: {str(e)}")

import json
import os
from typing import Dict, Tuple

import requests

import constants
from utils import get_resource_path

API_CONFIG_PATH = get_resource_path("api_config.txt")


def load_auth_config(config_path: str = API_CONFIG_PATH) -> Tuple[str, str]:
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
        config_path: str = API_CONFIG_PATH,
        order: int = 0,
        zip_path: str = None
) -> Dict:
    """Функция загрузки файлов на сервер (zip-архив опционален)"""
    if not os.path.exists(html_path):
        raise FileNotFoundError(f"HTML файл не найден: {html_path}")

    if zip_path and not os.path.exists(zip_path):
        raise FileNotFoundError(f"ZIP архив не найден: {zip_path}")

    auth = load_auth_config(config_path)
    files = {}

    try:
        # Открываем файлы
        files['html_file'] = open(html_path, 'rb')
        if zip_path:
            files['assets_zip'] = open(zip_path, 'rb')

        # Подготавливаем данные
        data = {
            'level_id': level_id,
            'title': title,
            'order': order
        }

        # Выполняем запрос
        response = requests.post(
            url=constants.API_GUIDE_UPLOAD,
            files=files,
            data=data,
            auth=auth,
            timeout=30  # Добавляем таймаут
        )

        # Детальная диагностика для отладки
        print(f"🔍 Status Code: {response.status_code}")
        print(f"🔍 Response Headers: {dict(response.headers)}")

        # Пробуем прочитать ответ как текст сначала
        response_text = response.text
        print(f"🔍 Response Preview: {response_text[:500]}...")

        # Проверяем статус ответа
        # Успешные статусы: 200 (OK), 201 (Created), 204 (No Content)
        if response.status_code in [200, 201, 204]:
            try:
                return response.json()
            except json.JSONDecodeError as e:
                print(f"⚠️ Не удалось распарсить JSON ответ: {e}")
                print(f"⚠️ Полный ответ: {response_text}")
                raise Exception("❌ Сервер вернул некорректный ответ")
        elif response.status_code == 401:
            raise Exception("❌ Ошибка авторизации: Неверный логин/пароль или требуется вход в систему")
        elif response.status_code == 403:
            raise Exception("❌ Доступ запрещен: Недостаточно прав для выполнения операции")
        elif response.status_code == 404:
            raise Exception("❌ Ресурс не найден: Неправильный URL или endpoint")
        elif response.status_code >= 400:
            raise Exception(f"❌ Ошибка {response.status_code}: {response_text[:200]}")

        # Пытаемся распарсить JSON только если статус успешный
        try:
            return response.json()
        except json.JSONDecodeError as e:
            print(f"⚠️ Не удалось распарсить JSON ответ: {e}")
            print(f"⚠️ Полный ответ: {response_text}")
            raise Exception("❌ Сервер вернул некорректный ответ")

    except requests.exceptions.ConnectionError:
        raise Exception("❌ Не удалось подключиться к серверу. Проверьте интернет-соединение и URL")
    except requests.exceptions.Timeout:
        raise Exception("❌ Превышено время ожидания ответа от сервера")
    except requests.exceptions.RequestException as e:
        raise Exception(f"❌ Ошибка сети: {e}")
    finally:
        # Всегда закрываем файлы
        for file in files.values():
            try:
                file.close()
            except Exception as e:
                print(f"⚠️ Ошибка при закрытии файла: {e}")

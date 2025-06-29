import os
from typing import Dict, Optional

import requests

from constants import API_COURSES_IDS
from .guide_uploader import upload_guide  # Импортируем конкретную функцию


def get_available_courses(api_url: str) -> Dict:
    """Получает список доступных курсов и уровней"""
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()


def select_level_interactive(courses_data: Dict) -> int:
    """Интерактивный выбор уровня с CLI"""
    print("\n📚 Доступные курсы и уровни:")
    for course in courses_data['courses']:
        print(f"📘 {course['course_title']} (Course ID: {course['course_id']})")
        for level in course['levels']:
            print(f"  └── 📗 {level['level_title']} (Level ID: {level['level_id']})")

    while True:
        level_id = input("\nВведите ID нужного уровня для загрузки: ").strip()
        if level_id.isdigit():
            return int(level_id)
        print("❌ Некорректный ID. Попробуйте еще раз.")


def process_upload_flow(
        html_path: str,
        assets_zip_path: str,
        original_zip_path: str,
        courses_api_url: str = API_COURSES_IDS,
        auth_config_path: str = 'api_config.txt'
) -> Optional[Dict]:
    """
    Полный процесс загрузки методички:
    1. Получение списка курсов
    2. Выбор уровня
    3. Загрузка на сервер
    """
    try:
        # Получаем данные о курсах
        courses_data = get_available_courses(courses_api_url)

        # Выбираем уровень
        level_id = select_level_interactive(courses_data)

        # Подготавливаем метаданные
        title = os.path.splitext(os.path.basename(original_zip_path))[0]

        print("\n🔄 Загрузка на сервер...")
        response = upload_guide(
            html_path=html_path,
            zip_path=assets_zip_path,
            level_id=level_id,
            title=title,
            config_path=auth_config_path
        )

        print(f"✅ Успешно загружено! Ответ сервера: {response}")
        return response

    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return None

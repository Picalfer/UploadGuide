import os
from typing import Dict, Optional

import requests

from constants import API_COURSES_IDS
from .guide_uploader import upload_guide  # Импортируем конкретную функцию
from .level_cache import save_last_level, load_last_level


def get_available_courses(api_url: str) -> Dict:
    """Получает список доступных курсов и уровней"""
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()


def select_level_interactive(courses_data: Dict) -> int:
    """Интерактивный выбор уровня с возможностью использовать последний"""
    last_level = load_last_level()

    print("\n📚 Доступные курсы и уровни:")
    for course in courses_data['courses']:
        print(f"📘 {course['course_title']} (Course ID: {course['course_id']})")
        for level in course['levels']:
            print(f"  └── 📗 {level['level_title']} (Level ID: {level['level_id']})")

    while True:
        if last_level:
            prompt = (
                f"\nВведите ID нужного уровня (или 'y' для использования "
                f"последнего уровня {last_level}): "
            )
        else:
            prompt = "\nВведите ID нужного уровня: "

        user_input = input(prompt).strip().lower()

        if user_input == 'y' and last_level:
            return last_level
        elif user_input.isdigit():
            level_id = int(user_input)
            save_last_level(level_id)  # Сохраняем новый выбор
            return level_id

        print("❌ Некорректный ввод. Введите ID уровня или 'y'")


def process_upload_flow(
        html_path: str,
        assets_zip_path: str,
        original_zip_path: str,
        courses_api_url: str = API_COURSES_IDS,
        auth_config_path: str = 'api_config.txt'
) -> Optional[Dict]:
    """Полный процесс загрузки с сохранением последнего уровня"""
    try:
        courses_data = get_available_courses(courses_api_url)
        level_id = select_level_interactive(courses_data)

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

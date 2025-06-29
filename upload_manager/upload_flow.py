import os
from typing import Dict

from constants import API_COURSES_IDS, API_GUIDES_ORDER
from .guide_uploader import upload_guide  # Импортируем конкретную функцию
from .level_cache import save_last_level, load_last_level, load_next_order


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


import requests
from typing import Dict, Optional


def get_level_guides(level_id: int, guiders_order_api: str) -> Optional[Dict]:
    """Получает список методичек уровня"""
    try:
        response = requests.get(f"{guiders_order_api}{level_id}/")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException:
        return None


def select_order_interactive(guides_data: Dict, level_id: int) -> int:
    """Интерактивный выбор порядка с отображением существующих методичек"""
    print(f"\n📝 Методички в уровне '{guides_data['level_title']}':")
    for guide in guides_data['guides']:
        print(f"  {guide['order']}. {guide['title']}")

    next_order = load_next_order()
    max_order = max([g['order'] for g in guides_data['guides']] or [0])

    while True:
        prompt = (
            f"\nВведите порядковый номер (1-{max_order + 1}) "
            f"{'или Enter для ' + str(next_order) if next_order else ''}: "
        )

        user_input = input(prompt).strip()

        if not user_input and next_order:
            save_last_level(level_id, next_order)
            return next_order
        elif user_input.isdigit():
            order = int(user_input)
            if 1 <= order <= max_order + 1:
                save_last_level(level_id, order)
                return order

        print(f"❌ Некорректный ввод. Введите число от 1 до {max_order + 1}")


def process_upload_flow(
        html_path: str,
        assets_zip_path: str,
        original_zip_path: str,
        auth_config_path: str = 'api_config.txt'
) -> Optional[Dict]:
    """Полный процесс загрузки с выбором порядка"""
    try:
        # 1. Получаем список курсов и выбираем уровень
        courses_data = get_available_courses(API_COURSES_IDS)
        level_id = select_level_interactive(courses_data)

        # 2. Получаем методички уровня и выбираем порядок
        guides_data = get_level_guides(level_id, API_GUIDES_ORDER)
        if not guides_data:
            print("❌ Не удалось получить данные о методичках")
            return None

        order = select_order_interactive(guides_data, level_id)

        # 3. Загрузка на сервер
        title = os.path.splitext(os.path.basename(original_zip_path))[0]

        print("\n🔄 Загрузка на сервер...")
        response = upload_guide(
            html_path=html_path,
            zip_path=assets_zip_path,
            level_id=level_id,
            title=title,
            order=order,
            config_path=auth_config_path
        )

        print(f"✅ Успешно загружено как методичка #{order}!")
        return response

    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        return None

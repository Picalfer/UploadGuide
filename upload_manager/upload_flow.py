import os
from typing import Dict, Callable

import constants
from .guide_uploader import upload_guide  # Импортируем конкретную функцию
from .level_cache import save_last_level, load_next_order


def get_available_courses(api_url: str) -> Dict:
    """Получает список доступных курсов и уровней"""
    response = requests.get(api_url)
    response.raise_for_status()
    return response.json()


def select_level_interactive(courses_data: Dict, app, callback: Callable[[int], None]):
    def on_selected(level_id: int):
        callback(level_id)

    app.ask_level_selection(courses_data, on_selected)


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
        app,
        html_path: str,
        assets_zip_path: Optional[str],
        original_zip_path: str,
        auth_config_path: str = 'api_config.txt',
        callback: Optional[Callable[[Optional[Dict]], None]] = None
):
    try:
        courses_data = get_available_courses(constants.API_COURSES_IDS)

        def after_level_selected(level_id: int):
            try:
                guides_data = get_level_guides(level_id, constants.API_GUIDES_ORDER)
                if not guides_data:
                    print("❌ Не удалось получить данные о методичках")
                    if callback:
                        callback(None)
                    return

                def after_order_selected(order: int):
                    title = os.path.splitext(os.path.basename(original_zip_path))[0]

                    print("\n🔄 Загрузка на сервер...")

                    upload_kwargs = {
                        'html_path': html_path,
                        'level_id': level_id,
                        'title': title,
                        'order': order,
                        'config_path': auth_config_path
                    }

                    if assets_zip_path and os.path.exists(assets_zip_path):
                        upload_kwargs['zip_path'] = assets_zip_path

                    response = upload_guide(**upload_kwargs)

                    print(f"✅ Успешно загружено как методичка #{order}!")
                    if callback:
                        callback(response)

                app.ask_order_selection(guides_data, level_id, after_order_selected)

            except Exception as e:
                print(f"❌ Ошибка загрузки: {e}")
                if callback:
                    callback(None)

        select_level_interactive(courses_data, app, after_level_selected)

    except Exception as e:
        print(f"❌ Ошибка загрузки: {e}")
        if callback:
            callback(None)

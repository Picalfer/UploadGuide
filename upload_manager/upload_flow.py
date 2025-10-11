import os
from typing import Dict, Callable

import constants
from utils import Status
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
    """Адаптированный процесс загрузки под текущий GUI"""

    def handle_error(error_msg: str, exception: Exception = None):
        """Универсальная обработка ошибок"""
        full_error = f"{error_msg}\n{str(exception) if exception else ''}"
        print(f"❌ {error_msg}")
        if exception:
            print(f"🔧 Детали: {exception}")

        app.update_status(Status.ERROR)
        if callback:
            callback(None)

    def handle_success(response: Dict, order: int):
        """Обработка успешной загрузки"""
        success_msg = f"✅ Успешно загружено как методичка #{order}!"
        print(success_msg)
        app.update_status(Status.SUCCESS)
        app.mark_step_done("uploaded")  # Отмечаем завершающий этап
        if callback:
            callback(response)

    try:
        app.update_status(Status.REQUESTING)
        courses_data = get_available_courses(constants.API_COURSES_IDS)

        if not courses_data:
            handle_error("Не удалось получить список курсов")
            return

        def after_level_selected(level_id: int):
            """Обработка выбора уровня"""
            try:
                app.update_status(Status.REQUESTING)
                guides_data = get_level_guides(level_id, constants.API_GUIDES_ORDER)

                if not guides_data:
                    handle_error("Не удалось получить данные о методичках уровня")
                    return

                def after_order_selected(order: int):
                    """Обработка выбора порядка"""
                    try:
                        title = os.path.splitext(os.path.basename(original_zip_path))[0]

                        # Подготовка параметров загрузки
                        upload_kwargs = {
                            'html_path': html_path,
                            'level_id': level_id,
                            'title': title,
                            'order': order,
                            'config_path': auth_config_path
                        }

                        if assets_zip_path and os.path.exists(assets_zip_path):
                            upload_kwargs['zip_path'] = assets_zip_path
                        else:
                            print("ℹ️ ZIP с ассетами не будет загружен")

                        # Обновляем статус и отмечаем этап подготовки
                        app.update_detailed_status(Status.UPLOADING, f"Загрузка '{title}'...")
                        app.mark_step_done("upload_prepared")

                        # Выполнение загрузки
                        response = upload_guide(**upload_kwargs)
                        handle_success(response, order)

                    except Exception as e:
                        handle_error("Ошибка при загрузке на сервер", e)

                # Запрос выбора порядка
                app.ask_order_selection(guides_data, level_id, after_order_selected)

            except Exception as e:
                handle_error("Ошибка при получении данных уровня", e)

        # Запуск выбора уровня
        app.ask_level_selection(courses_data, after_level_selected)

    except Exception as e:
        handle_error("Критическая ошибка в процессе загрузки", e)

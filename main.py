import os

import requests

from api_uploader.api_uploader import GuideUploader
from constants import API_COURSES_IDS
from image_optimizer.archive_processor import process_archive
from word_to_html_converter.word_to_html_converter import select_and_convert


def main():
    try:
        # 1. Конвертация Word -> ZIP
        print("🔄 Шаг 1/3: Конвертация Word в ZIP...")
        original_zip_path = select_and_convert()
        print(f"✅ ZIP создан: {original_zip_path}")

        # 2. Оптимизация изображений
        print("\n🔄 Шаг 2/3: Оптимизация изображений...")
        html_path, upload_zip_path = process_archive(zip_path=original_zip_path)
        print(f"✅ Оптимизация завершена! HTML: {html_path}")

        # 3. Дальнейшие действия с html_path и upload_zip_path...
        print("✅ Оптимизация завершена!")

        # 👉 2. Ввод ID уровня
        response = requests.get(API_COURSES_IDS)
        response.raise_for_status()

        data = response.json()

        print("\n📚 Доступные курсы и уровни:")
        for course in data['courses']:
            print(f"📘 {course['course_title']} (Course ID: {course['course_id']})")
            for level in course['levels']:
                print(f"  └── 📗 {level['level_title']} (Level ID: {level['level_id']})")

        level_id_input = input("\nВведите ID нужного уровня для загрузки: ").strip()
        if not level_id_input.isdigit():
            print("❌ Некорректный ID. Загрузка отменена.")
            exit()

        level_id = int(level_id_input)

        # 3. Загрузка на сервер
        print("\n🔄 Шаг 3/3: Загрузка на сервер...")
        try:
            uploader = GuideUploader()
            response = uploader.upload_guide(
                html_path=html_path,
                zip_path=upload_zip_path,
                level_id=level_id,
                title=os.path.splitext(os.path.basename(original_zip_path))[0],
                order=0
            )
            print(f"✅ Успешно загружено! Ответ сервера: {response}")

        except Exception as e:
            print(f"❌ Ошибка загрузки: {e}")

    except Exception as e:
        print(f"🔴 Критическая ошибка: {e}")


if __name__ == '__main__':
    main()

import os
import zipfile

import requests

from api_uploader.api_uploader import GuideUploader
from constants import API_COURSES_IDS
from image_optimizer.archive_processor import process_archive
from word_to_html_converter import WordToHtmlConverter


def main():
    try:
        # 1. Конвертация Word -> HTML+ZIP
        print("🔄 Шаг 1/3: Конвертация Word в ZIP...")
        converter = WordToHtmlConverter()
        success, original_zip_path = converter.convert()

        if not success:
            print("❌ Ошибка конвертации Word в ZIP")
            return

        print(f"✅ ZIP создан: {original_zip_path}")

        # 2. Оптимизация изображений
        print("\n🔄 Шаг 2/3: Оптимизация изображений...")
        try:
            result_folder = process_archive(zip_path=original_zip_path)

            # Находим единственный HTML файл
            html_files = [f for f in os.listdir(result_folder)
                          if f.endswith('.html')]

            if len(html_files) != 1:
                raise ValueError(f"Найдено {len(html_files)} HTML файлов, должен быть 1")

            html_path = os.path.join(result_folder, html_files[0])
            images_zip_path = os.path.join(result_folder, 'images.zip')

            # Создаем чистый архив БЕЗ HTML в images.zip
            clean_images_zip = os.path.join(result_folder, 'clean_images.zip')
            with zipfile.ZipFile(images_zip_path, 'r') as src_zip, \
                    zipfile.ZipFile(clean_images_zip, 'w') as dst_zip:

                for item in src_zip.namelist():
                    if not item.endswith('.html'):  # Исключаем HTML файлы
                        dst_zip.writestr(item, src_zip.read(item))

            # Создаем финальный архив для загрузки
            upload_zip_path = os.path.join(result_folder, 'upload.zip')
            with zipfile.ZipFile(upload_zip_path, 'w') as final_zip:

                # Добавляем только изображения в папку images/
                with zipfile.ZipFile(clean_images_zip, 'r') as img_zip:
                    for img_file in img_zip.namelist():
                        final_zip.writestr(f'images/{img_file}', img_zip.read(img_file))
            """
            print("\n✅ Финальная структура архива:")
            with zipfile.ZipFile(upload_zip_path, 'r') as z:
                for file in z.namelist():
                    print(f"- {file}")
            """

        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")
            return

        response = requests.get(API_COURSES_IDS)
        response.raise_for_status()

        data = response.json()

        print("\n📚 Доступные курсы и уровни:")
        for course in data['courses']:
            print(f"📘 {course['course_title']} (Course ID: {course['course_id']})")
            for level in course['levels']:
                print(f"  └── 📗 {level['level_title']} (Level ID: {level['level_id']})")

        # 👉 2. Ввод ID уровня
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

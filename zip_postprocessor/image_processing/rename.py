import re
import tempfile
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup


def extract_number(name):
    match = re.search(r'(\d+)', name.stem)
    return int(match.group(1)) if match else 0


def rename_images_to_match_html(images_dir_path, converted_zip_path):
    if not images_dir_path:
        print("⚠️ Путь к изображениям не указан — переименование пропущено.")
        return
    images_dir = Path(images_dir_path)
    converted_zip = Path(converted_zip_path)

    if not images_dir.exists():
        print(f"⚠️ Папка с изображениями не найдена: {images_dir}")
        return
    if not converted_zip.exists():
        print(f"⚠️ Архив не найден: {converted_zip}")
        return

    # Создаем временную директорию для извлечения HTML
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        with zipfile.ZipFile(converted_zip, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)

        # Ищем HTML-файл в распакованном архиве
        html_files = list(tmp_dir.glob("*.html"))
        if not html_files:
            print("❌ HTML-файл не найден в архиве")
            return

        html_file = html_files[0]

        # Чтение HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        img_tags = soup.find_all('img')

        # Собираем ВСЕ имена из HTML (с дубликатами) и УНИКАЛЬНЫЕ имена
        html_image_names_all = [Path(tag['src']).name for tag in img_tags if tag.get('src')]
        html_image_names_unique = list(dict.fromkeys(html_image_names_all))  # сохраняем порядок

        # Локальные изображения
        local_images = sorted(images_dir.glob("*.jpg"),
                              key=extract_number)  # без сортировки будет неправильная нумерация

        if len(local_images) != len(html_image_names_unique):
            local_image_names = [img.name for img in local_images]
            print("\n⚠️ Количество УНИКАЛЬНЫХ изображений не совпадает!")

            print(f"🖼️ Изображений в HTML: {len(html_image_names_unique)}")
            print("Список изображений в HTML:")
            for i, name in enumerate(html_image_names_unique, 1):
                print(f"{i:3d}. {name}")

            print(f"\n📁 Найдено файлов в папке images/: {len(local_images)}")
            print("Список локальных изображений:")
            for i, name in enumerate(local_image_names, 1):
                print(f"{i:3d}. {name}")

            # Находим различия между списками
            html_set = set(html_image_names_unique)
            local_set = set(local_image_names)

            missing_in_local = html_set - local_set
            extra_in_local = local_set - html_set

            if missing_in_local:
                print("\nФайлы, которые есть в HTML, но отсутствуют локально:")
                for name in sorted(missing_in_local):
                    print(f"- {name}")

            if extra_in_local:
                print("\nФайлы, которые есть локально, но отсутствуют в HTML:")
                for name in sorted(extra_in_local):
                    print(f"- {name}")

            print("\nОперация отменена.")
            return

        # Временное переименование
        temp_names = []
        for i, img_path in enumerate(local_images):
            temp_name = img_path.with_name(f"__temp_{i}.jpg")
            img_path.rename(temp_name)
            temp_names.append(temp_name)

        # Переименование по порядку
        for temp_path, final_name in zip(temp_names, html_image_names_unique):
            new_path = images_dir / final_name
            temp_path.rename(new_path)

        print("\n✅ Переименование изображений под html завершено.")

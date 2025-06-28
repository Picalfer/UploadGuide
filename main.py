import os
import zipfile
from api_uploader.api_uploader import GuideUploader
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

            print("\n✅ Финальная структура архива:")
            with zipfile.ZipFile(upload_zip_path, 'r') as z:
                for file in z.namelist():
                    print(f"- {file}")

        except Exception as e:
            print(f"❌ Ошибка обработки: {e}")
            return

        # 3. Загрузка на сервер
        print("\n🔄 Шаг 3/3: Загрузка на сервер...")
        try:
            uploader = GuideUploader()
            response = uploader.upload_guide(
                html_path=html_path,
                zip_path=upload_zip_path,
                level_id=7,
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
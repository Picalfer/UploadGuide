import os
import shutil
import tempfile
import zipfile
from typing import Optional

from .compress import optimize_image
from .reporter import ArchiveReporter


def process_archive(zip_path: str, max_size_kb: int = 300, output_folder: Optional[str] = None) -> tuple[str, None] | \
                                                                               tuple[str, str]:
    try:
        # Валидация входных данных
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"ZIP-архив не найден: {zip_path}")

        # Инициализация репортера (если нужно)
        reporter = ArchiveReporter() if 'ArchiveReporter' in globals() else None

        # Основная логика обработки (ваш текущий код)
        archive_name = os.path.splitext(os.path.basename(zip_path))[0]
        output_folder = output_folder or os.path.join(os.path.dirname(zip_path), archive_name)

        if os.path.exists(output_folder):
            shutil.rmtree(output_folder)
        os.makedirs(output_folder)

        # Распаковываем исходный архив
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_folder)

        # Находим папку images
        images_dir = None
        for root, dirs, files in os.walk(output_folder):
            if 'images' in dirs:
                images_dir = os.path.join(root, 'images')
                break

        if not images_dir:
            print("ℹ️ Картинки не найдены, пропускаем шаг оптимизации.")
            # Ищем HTML
            html_files = [f for f in os.listdir(output_folder) if f.endswith('.html')]
            if len(html_files) != 1:
                raise ValueError(f"Найдено {len(html_files)} HTML файлов, должен быть 1")
            html_path = os.path.join(output_folder, html_files[0])
            return html_path, None

        # Подсчет статистики
        image_files = [f for f in os.listdir(images_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
        original_total_size = sum(os.path.getsize(os.path.join(images_dir, f)) for f in image_files) / 1024

        # Старт оптимизации
        reporter.start_optimization(len(image_files), original_total_size)

        # Создаем временную папку для обработки изображений
        with tempfile.TemporaryDirectory() as temp_img_dir:
            optimized_total_size = 0

            # Обрабатываем изображения
            for img_name in image_files:
                src_path = os.path.join(images_dir, img_name)
                dst_path = os.path.join(temp_img_dir, img_name)

                optimize_image(src_path, dst_path, max_size_kb)
                optimized_total_size += os.path.getsize(dst_path) / 1024
                reporter.update_optimize_progress()

            # Удаляем оригинальную папку images
            shutil.rmtree(images_dir)

            # Создаем архив с изображениями
            images_zip_path = os.path.join(os.path.dirname(images_dir), 'images.zip')
            with zipfile.ZipFile(images_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for img_name in os.listdir(temp_img_dir):
                    img_path = os.path.join(temp_img_dir, img_name)
                    zipf.write(img_path, img_name)

            # Создаем чистый архив БЕЗ HTML в clean_images.zip
            clean_images_zip = os.path.join(output_folder, 'clean_images.zip')
            with zipfile.ZipFile(images_zip_path, 'r') as src_zip, \
                    zipfile.ZipFile(clean_images_zip, 'w') as dst_zip:
                for item in src_zip.namelist():
                    if not item.endswith('.html'):  # Исключаем HTML файлы
                        dst_zip.writestr(item, src_zip.read(item))

            # Находим единственный HTML файл
            html_files = [f for f in os.listdir(output_folder)
                          if f.endswith('.html')]

            if len(html_files) != 1:
                raise ValueError(f"Найдено {len(html_files)} HTML файлов, должен быть 1")

            html_path = os.path.join(output_folder, html_files[0])

            # Создаем финальный архив для загрузки
            upload_zip_path = os.path.join(output_folder, 'upload.zip')
            with zipfile.ZipFile(upload_zip_path, 'w') as final_zip:
                # Добавляем только изображения в папку images/
                with zipfile.ZipFile(clean_images_zip, 'r') as img_zip:
                    for img_file in img_zip.namelist():
                        final_zip.writestr(f'images/{img_file}', img_zip.read(img_file))

        # Вывод итогов
        final_zip_size = os.path.getsize(upload_zip_path) / 1024
        reporter.print_summary(original_total_size, optimized_total_size, final_zip_size)
        reporter.close()

        print(f"\n✅ Готово! Результат сохранен в: {output_folder} \n✅ Название папки скопировано в буфер обмена!")
        return html_path, upload_zip_path

    except Exception as e:
        # Удаляем временные файлы в случае ошибки
        if 'output_folder' in locals() and os.path.exists(output_folder):
            shutil.rmtree(output_folder, ignore_errors=True)
        raise  # Перебрасываем исключение для обработки в main()

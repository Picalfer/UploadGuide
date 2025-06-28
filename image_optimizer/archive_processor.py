import os
import shutil
import tempfile
import zipfile

import pyperclip

from .compress import optimize_image
from .reporter import ArchiveReporter


def process_archive(zip_path=None, max_size_kb=300, output_folder=None):
    if zip_path is None:
        zip_path = get_archive_path_from_txt()

    # Инициализация репортера
    reporter = ArchiveReporter()

    # Определяем папку для результатов
    archive_name = os.path.splitext(os.path.basename(zip_path))[0]
    if output_folder is None:
        output_folder = os.path.join(os.path.dirname(zip_path), archive_name)

    # Создаем папку для результатов
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
        reporter.close()
        raise FileNotFoundError("Папка 'images' не найдена в архиве")

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

        # Создаем архив
        images_zip_path = os.path.join(os.path.dirname(images_dir), 'images.zip')

        with zipfile.ZipFile(images_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for img_name in os.listdir(temp_img_dir):
                img_path = os.path.join(temp_img_dir, img_name)
                zipf.write(img_path, img_name)

    # Вывод итогов
    final_zip_size = os.path.getsize(images_zip_path) / 1024
    reporter.print_summary(original_total_size, optimized_total_size, final_zip_size)
    reporter.close()

    print(f"\n✅ Готово! Результат сохранен в: {output_folder} \n✅ Название папки скопировано в буфер обмена!")
    return output_folder


def get_archive_path_from_txt(txt_path='archive_name.txt'):
    """Читает название архива из текстового файла"""
    try:
        with open(txt_path, 'r', encoding='utf-8') as f:
            archive_name = f.read().strip()

            pyperclip.copy(archive_name)

            if not archive_name.endswith('.zip'):
                archive_name += '.zip'

            downloads_path = os.path.join(os.path.expanduser('~'), 'Downloads')
            full_path = os.path.join(downloads_path, archive_name)

            if not os.path.exists(full_path):
                raise FileNotFoundError(f"Архив не найден: {full_path}")

            return full_path
    except Exception as e:
        raise Exception(f"Ошибка чтения файла {txt_path}: {str(e)}")

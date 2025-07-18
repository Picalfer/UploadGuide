from .archiver.prepare import prepare_upload_folder
from .image_processing.rename import rename_images_to_match_html


# Вся интеграция по шагам:
# 1. Переименование картинок
# 2. Подготовка upload zip
# 3. Обработка HTML

def run_postprocessing(zip_path, images_path, word_path):
    rename_images_to_match_html(images_path, zip_path)
    html_path, upload_zip, folder = prepare_upload_folder(zip_path, images_path, word_path)
    return html_path, upload_zip, folder

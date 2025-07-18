import shutil
import zipfile
from pathlib import Path

from constants import TEMP_DIR
from zip_postprocessor.html_processing.cleanup import remove_google_redirects
from zip_postprocessor.html_processing.code_blocks import process_code_sections


def prepare_upload_folder(converted_zip_path, images_dir, word_path):
    upload_folder = Path(TEMP_DIR / 'upload_folder')
    if upload_folder.exists():
        shutil.rmtree(upload_folder)
    upload_folder.mkdir()

    # Распаковываем ZIP в upload_folder
    with zipfile.ZipFile(converted_zip_path, 'r') as zip_ref:
        zip_ref.extractall(upload_folder)

    # Ищем HTML-файл и переименовываем его
    html_files = list(upload_folder.glob('*.html'))
    if not html_files:
        raise FileNotFoundError("HTML файл не найден в распакованном архиве")

    original_html_name = Path(word_path).stem + '.html'
    original_html_path = upload_folder / original_html_name
    html_files[0].rename(original_html_path)

    upload_zip_path = None

    # Если images_dir указан и в нём есть изображения — создаём архив
    if images_dir and Path(images_dir).exists():
        image_files = list(Path(images_dir).glob('*'))
        if image_files:
            # Создаём images/ в папке upload_folder
            images_folder = upload_folder / 'images'
            images_folder.mkdir(exist_ok=True)

            for img_path in image_files:
                shutil.copy(img_path, images_folder / img_path.name)

            # ✅ Создаём архив upload.zip с картинками
            upload_zip_path = upload_folder / 'upload.zip'
            with zipfile.ZipFile(upload_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for img_file in images_folder.glob('*'):
                    arcname = img_file.name
                    zipf.write(img_file, arcname)

    print(f"📦 Подготовка завершена:")
    print(f"📝 HTML: {original_html_path}")
    if upload_zip_path:
        print(f"🗂️ ZIP:  {upload_zip_path}")
    else:
        print("ℹ️ Изображений нет — zip архив не создавался")

    prepare_html(original_html_path)
    return str(original_html_path), str(upload_zip_path) if upload_zip_path else None, upload_folder


def prepare_html(html_path):
    """Основная функция обработки HTML"""
    # Чтение файла
    with open(html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Очистка редиректов от Google
    html_content = remove_google_redirects(html_content)

    # Обработка блоков кода
    html_content = process_code_sections(html_content)

    # Запись обратно в файл
    with open(html_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

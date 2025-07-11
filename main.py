import re

from bs4 import BeautifulSoup

from docx_optimizer import select_word_file, extract_images_from_docx, compress_images_in_docx
from upload_manager.upload_flow import process_upload_flow
from word_to_html_converter import convert
from zip_postprocessor import rename_images_to_match_html, prepare_upload_folder


def prepare_html(html_path):
    # Чтение файла
    with open(html_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Очистка редиректов от Google
    cleaned_content = re.sub(
        r'https?://www\.google\.com/url\?q=([^&]+)&[^"]+',
        lambda m: m.group(1),
        html_content
    )

    # Парсинг HTML
    soup = BeautifulSoup(cleaned_content, 'html.parser')

    # Запись обратно в файл (отдельно от чтения)
    with open(html_path, 'w', encoding='utf-8') as file:
        file.write(str(soup))


def mainAction(app=None):
    try:
        if app:
            word_path = select_word_file()
            app.mark_step_done("word_selected")

            images_dir = extract_images_from_docx(word_path)
            app.mark_step_done("images_extracted")

            compressed_path = compress_images_in_docx(word_path)
            app.mark_step_done("docx_compressed")

            converted_path = convert(compressed_path)
            app.mark_step_done("html_converted")

            rename_images_to_match_html(
                images_dir_path=images_dir,
                converted_zip_path=converted_path
            )
            app.mark_step_done("images_renamed")

            html_path, upload_zip_path, upload_folder_path = prepare_upload_folder(
                converted_path, images_dir, word_path
            )
            app.mark_step_done("upload_prepared")

            prepare_html(html_path)

            process_upload_flow(
                html_path=html_path,
                assets_zip_path=upload_zip_path,
                original_zip_path=converted_path,
                app=app
            )
            app.mark_step_done("uploaded")
        else:
            print("App is not initialized")

    except Exception as e:
        print(f"🔴 Критическая ошибка: {e}")

    # finally:
    # delete_path(TEMP_DIR)


if __name__ == '__main__':
    mainAction()

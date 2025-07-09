from docx_optimizer import select_word_file, extract_images_from_docx, compress_images_in_docx
from upload_manager.upload_flow import process_upload_flow
from utils import delete_path
from word_to_html_converter import convert
from zip_postprocessor import rename_images_to_match_html, prepare_upload_folder


def main():
    images_dir = None
    compressed_path = None
    converted_path = None
    upload_folder_path = None

    try:
        word_path = select_word_file()
        images_dir = extract_images_from_docx(word_path)
        compressed_path = compress_images_in_docx(word_path)
        converted_path = convert(compressed_path)

        rename_images_to_match_html(
            images_dir_path=images_dir,
            converted_zip_path=converted_path
        )

        html_path, upload_zip_path, upload_folder_path = prepare_upload_folder(
            converted_path, images_dir, word_path
        )

        process_upload_flow(
            html_path=html_path,
            assets_zip_path=upload_zip_path,
            original_zip_path=converted_path
        )

    except Exception as e:
        print(f"🔴 Критическая ошибка: {e}")

    finally:
        for path in [images_dir, compressed_path, converted_path, upload_folder_path]:
            delete_path(path)


if __name__ == '__main__':
    main()

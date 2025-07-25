import zip_postprocessor.main
from docx_optimizer import select_word_file, extract_images_from_docx, compress_images_in_docx
from upload_manager.upload_flow import process_upload_flow
from word_to_html_converter import convert
from zip_postprocessor import rename_images_to_match_html


def mainAction(app=None):
    try:
        if app:
            # очищаем данные предыдущей методички
            # delete_path(TEMP_DIR)

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

            html_path, upload_zip_path, upload_folder_path = zip_postprocessor.main.run_postprocessing(
                converted_path, images_dir, word_path
            )
            app.mark_step_done("upload_prepared")

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

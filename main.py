from image_optimizer.archive_processor import process_archive
from upload_manager.upload_flow import process_upload_flow
from word_to_html_converter.word_to_html_converter import select_and_convert


def main():
    try:
        # 1. Конвертация Word -> ZIP
        print("🔄 Шаг 1/3: Конвертация Word в ZIP...")
        original_zip_path = select_and_convert()
        print(f"✅ ZIP создан: {original_zip_path}")

        # 2. Оптимизация изображений
        print("\n🔄 Шаг 2/3: Оптимизация изображений...")
        html_path, upload_zip_path = process_archive(zip_path=original_zip_path)

        # 3. Загрузка на сервер
        process_upload_flow(
            html_path=html_path,
            assets_zip_path=upload_zip_path,
            original_zip_path=original_zip_path
        )

    except Exception as e:
        print(f"🔴 Критическая ошибка: {e}")


if __name__ == '__main__':
    main()

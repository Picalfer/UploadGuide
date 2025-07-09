from tkinter import Tk
from tkinter import filedialog

from word_to_html_converter.word_to_html_converter import convert


def select_word_file() -> str:
    """Выбор Word файла через проводник"""
    root = Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Выберите Word документ",
        filetypes=[("Word Documents", "*.docx")]
    )
    if not file_path:
        raise ValueError("Файл не выбран")

    print(f"📄 Выбран Word файл: {file_path}")
    return file_path


def extract_images_from_docx(docx_path, output_dir="images", jpeg_quality=60):
    try:
        docx_path = Path(docx_path)
        if not docx_path.exists():
            print(f"❌ Файл {docx_path} не найден")
            return None

        images_dir = Path(output_dir)
        images_dir.mkdir(exist_ok=True)

        found_images = []

        with zipfile.ZipFile(docx_path) as z:
            for file_info in z.infolist():
                if file_info.filename.startswith("word/media/"):
                    found_images.append(file_info)

            if not found_images:
                print("ℹ️ В документе не найдено изображений.")
                return None

            for file_info in found_images:
                original_name = Path(file_info.filename).stem
                jpeg_path = images_dir / f"{original_name}.jpg"

                with z.open(file_info) as source:
                    try:
                        image = Image.open(source)
                        if image.mode in ("RGBA", "P"):
                            image = image.convert("RGB")
                        image.save(jpeg_path, format="JPEG", quality=jpeg_quality)
                    except Exception as e:
                        print(f"⚠ Не удалось обработать {file_info.filename}: {e}")

        print(f"📸 Все изображения сохранены в: {images_dir.resolve()}")
        return images_dir

    except Exception as e:
        print(f"❌ Произошла ошибка: {e}")
        return None


import zipfile
import io
from PIL import Image


def compress_images_in_docx(input_path, jpeg_quality=1):
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"❌ Файл {input_path} не найден")
        return None

    output_path = Path.cwd() / f"{input_path.stem}.docx"

    with zipfile.ZipFile(input_path, 'r') as docx_zip:
        new_docx_io = io.BytesIO()
        with zipfile.ZipFile(new_docx_io, 'w') as new_docx_zip:
            for item in docx_zip.infolist():
                data = docx_zip.read(item.filename)

                if item.filename.startswith('word/media/') and item.filename.lower().endswith(
                        ('.png', '.jpeg', '.jpg')):
                    try:
                        image = Image.open(io.BytesIO(data))
                        img_io = io.BytesIO()
                        if image.mode in ("RGBA", "P"):
                            image = image.convert("RGB")
                        image.save(img_io, format='JPEG', quality=jpeg_quality)
                        img_io.seek(0)
                        data = img_io.read()
                    except Exception as e:
                        print(f"⚠ Не удалось обработать {item.filename}: {e}")

                new_docx_zip.writestr(item, data)

    with open(output_path, 'wb') as f:
        f.write(new_docx_io.getvalue())

    print(f"📦 Сжатие завершено. Сохранено в: {output_path.resolve()}")
    return output_path


from pathlib import Path
import shutil


def delete_path(path):
    path = Path(path)
    if path.is_file():
        path.unlink()
        print(f"🗑️ Удалён файл: {path.resolve()}")
    elif path.is_dir():
        shutil.rmtree(path)
        print(f"🗑️ Удалена папка: {path.resolve()}")
    else:
        print(f"⚠️ Путь не найден: {path}")


def main():
    try:
        word_path = select_word_file()
        images_dir = extract_images_from_docx(word_path)
        compressed_path = compress_images_in_docx(word_path)
        converted_path = convert(compressed_path)

        print()
        delete_path(images_dir)
        delete_path(compressed_path)
        delete_path(converted_path)

        """
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
        """

    except Exception as e:
        print(f"🔴 Критическая ошибка: {e}")


if __name__ == '__main__':
    main()

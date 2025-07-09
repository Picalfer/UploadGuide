from tkinter import Tk
from tkinter import filedialog


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


import io
from PIL import Image
import zipfile
from pathlib import Path

def compress_images_in_docx(input_path, jpeg_quality=1):
    input_path = Path(input_path)
    if not input_path.exists():
        print(f"❌ Файл {input_path} не найден")
        return None

    output_path = Path.cwd() / f"{input_path.stem}.docx"

    image_found = False

    with zipfile.ZipFile(input_path, 'r') as docx_zip:
        new_docx_io = io.BytesIO()
        with zipfile.ZipFile(new_docx_io, 'w') as new_docx_zip:
            for item in docx_zip.infolist():
                data = docx_zip.read(item.filename)

                if item.filename.startswith('word/media/') and item.filename.lower().endswith(
                        ('.png', '.jpeg', '.jpg')):
                    image_found = True
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

    if not image_found:
        print("ℹ️ В документе не найдено изображений. Сжатие не требуется.")
        return input_path

    with open(output_path, 'wb') as f:
        f.write(new_docx_io.getvalue())

    print(f"📦 Сжатие завершено. Сохранено в: {output_path.resolve()}")
    return output_path
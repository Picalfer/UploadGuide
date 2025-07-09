from tkinter import Tk
from tkinter import filedialog

from upload_manager.upload_flow import process_upload_flow
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


import io
from PIL import Image


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


def delete_path(path):
    if not path:
        return
    try:
        p = Path(path)
        if p.is_file():
            p.unlink()
        elif p.is_dir():
            shutil.rmtree(p)
    except Exception as e:
        print(f"⚠️ Не удалось удалить {path}: {e}")


import re
import tempfile
from bs4 import BeautifulSoup


def extract_number(name):
    match = re.search(r'(\d+)', name.stem)
    return int(match.group(1)) if match else 0


def rename_images_to_match_html(images_dir_path, converted_zip_path):
    if not images_dir_path:
        print("⚠️ Путь к изображениям не указан — переименование пропущено.")
        return
    images_dir = Path(images_dir_path)
    converted_zip_path = Path(converted_zip_path)

    if not images_dir.exists():
        print(f"⚠️ Папка с изображениями не найдена: {images_dir}")
        return
    if not converted_zip_path.exists():
        print(f"⚠️ Архив не найден: {converted_zip_path}")
        return

    # Создаем временную директорию для извлечения HTML
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_dir = Path(tmp_dir)
        with zipfile.ZipFile(converted_zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmp_dir)

        # Ищем HTML-файл в распакованном архиве
        html_files = list(tmp_dir.glob("*.html"))
        if not html_files:
            print("❌ HTML-файл не найден в архиве")
            return

        html_file = html_files[0]

        # Чтение HTML
        with open(html_file, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')

        img_tags = soup.find_all('img')
        html_image_names = [Path(tag['src']).name for tag in img_tags if tag.get('src')]

        # print(f"🖼️ Изображений в HTML: {len(html_image_names)}")

        # Локальные изображения
        local_images = sorted(images_dir.glob("*.jpg"), key=extract_number)
        # print(f"📁 Найдено файлов в папке images/: {len(local_images)}")

        if len(local_images) != len(html_image_names):
            print("⚠️ Количество изображений не совпадает! Операция отменена.")
            return

        # Временное переименование
        temp_names = []
        for i, img_path in enumerate(local_images):
            temp_name = img_path.with_name(f"__temp_{i}.jpg")
            img_path.rename(temp_name)
            temp_names.append(temp_name)

        # Переименование по порядку
        for temp_path, final_name in zip(temp_names, html_image_names):
            new_path = images_dir / final_name
            temp_path.rename(new_path)

        print("✅ Переименование изображений под html завершено.")


import shutil
import zipfile
from pathlib import Path


def prepare_upload_folder(converted_zip_path, images_dir, word_path):
    upload_folder = Path('upload_folder')
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

            # ✅ Создаём архив upload.zip С ТОЛЬКО images/
            upload_zip_path = upload_folder / 'upload.zip'
            with zipfile.ZipFile(upload_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for img_file in images_folder.glob('*'):
                    arcname = f"images/{img_file.name}"
                    zipf.write(img_file, arcname)

    print(f"📦 Подготовка завершена:")
    print(f"📝 HTML: {original_html_path}")
    if upload_zip_path:
        print(f"🗂️ ZIP:  {upload_zip_path}")
    else:
        print("ℹ️ Изображений нет — zip архив не создавался")

    return str(original_html_path), str(upload_zip_path) if upload_zip_path else None, upload_folder


def main():
    try:
        word_path = select_word_file()
        images_dir = extract_images_from_docx(word_path)
        compressed_path = compress_images_in_docx(word_path)
        converted_path = convert(compressed_path)
        rename_images_to_match_html(
            images_dir_path=images_dir,
            converted_zip_path=converted_path
        )

        html_path, upload_zip_path, upload_folder_path = prepare_upload_folder(converted_path, images_dir, word_path)

        process_upload_flow(
            html_path=html_path,
            assets_zip_path=upload_zip_path,
            original_zip_path=converted_path
        )

        print()
        delete_path(images_dir)
        delete_path(compressed_path)
        delete_path(converted_path)
        delete_path(upload_folder_path)



    except Exception as e:
        print(f"🔴 Критическая ошибка: {e}")


if __name__ == '__main__':
    main()

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

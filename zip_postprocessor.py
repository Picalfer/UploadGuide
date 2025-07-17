import re
import shutil
import tempfile
import zipfile
from pathlib import Path

from bs4 import BeautifulSoup

from constants import TEMP_DIR


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


def remove_google_redirects(html_content):
    """Удаляет Google-редиректы из HTML-контента"""
    return re.sub(
        r'https?://www\.google\.com/url\?q=([^&]+)&[^"]+',
        lambda m: m.group(1),
        html_content
    )


def process_code_sections(html_content):
    """Обрабатывает блоки кода, заменяя text-indent и margin-left на пробелы и добавляя нумерацию строк"""
    soup = BeautifulSoup(html_content, 'html.parser')

    # Находим маркеры начала и конца кода
    start_markers = soup.find_all(lambda tag:
                                  tag.name == 'p' and
                                  'START_CODE_SECTION_7239' in tag.get_text())
    end_markers = soup.find_all(lambda tag:
                                tag.name == 'p' and
                                'END_CODE_SECTION_7239' in tag.get_text())

    if len(start_markers) != len(end_markers):
        raise ValueError("Непарные маркеры кода")

    for start, end in zip(start_markers, end_markers):
        code_content = []
        current = start.next_sibling

        # Собираем содержимое блока кода
        while current and current != end:
            code_content.append(current)
            current = current.next_sibling

        # Обрабатываем каждый элемент внутри блока кода
        for element in code_content:
            if element.name == 'p' and element.get('style', ''):
                styles = element['style'].split(';')
                new_styles = []
                indent_size = 0

                # Обрабатываем стили
                for style in styles:
                    style = style.strip()
                    if not style:
                        continue

                    # Обработка text-indent
                    if 'text-indent' in style:
                        try:
                            # Парсим значение (например "36pt" или "2em")
                            value = style.split(':')[1].strip()
                            if 'pt' in value:
                                pt_value = float(value.replace('pt', ''))
                                indent_size += int(pt_value / 9)  # Примерно 4 пробела для 36pt
                            elif 'em' in value:
                                em_value = float(value.replace('em', ''))
                                indent_size += int(em_value * 4)  # Примерно 4 пробела на 1em
                            elif 'px' in value:
                                px_value = float(value.replace('px', ''))
                                indent_size += int(px_value / 9)  # Эмпирическое соотношение
                            else:
                                # Если нет единиц измерения, считаем пикселями
                                indent_size += int(float(value) / 9)
                        except (ValueError, IndexError):
                            pass

                    # Обработка margin-left
                    elif 'margin-left' in style:
                        try:
                            value = style.split(':')[1].strip()
                            if 'pt' in value:
                                pt_value = float(value.replace('pt', ''))
                                indent_size += int(pt_value / 9)
                            elif 'em' in value:
                                em_value = float(value.replace('em', ''))
                                indent_size += int(em_value * 4)
                            elif 'px' in value:
                                px_value = float(value.replace('px', ''))
                                indent_size += int(px_value / 9)
                            elif 'cm' in value:
                                cm_value = float(value.replace('cm', ''))
                                indent_size += int(cm_value * 28.35 / 9)  # 1cm ≈ 28.35pt
                            else:
                                # Если нет единиц измерения, считаем пикселями
                                indent_size += int(float(value) / 9)
                        except (ValueError, IndexError):
                            pass
                    else:
                        new_styles.append(style)

                if indent_size > 0:
                    element['style'] = ';'.join(new_styles).strip(';')
                    indent = ' ' * indent_size

                    # Добавляем отступ к первому текстовому содержимому
                    for content in element.contents:
                        if isinstance(content, str) and content.strip():
                            content.replace_with(indent + content)
                            break
                    else:
                        first_span = element.find('span')
                        if first_span and first_span.string:
                            first_span.string.replace_with(indent + first_span.string)

        # Создаем блок кода с нумерацией строк и CSS для сохранения пробелов
        new_div = soup.new_tag('div', **{
            'class': 'code-block',
            'style': 'white-space: pre; font-family: monospace;'  # Сохраняет пробелы
        })

        for i, content in enumerate(code_content, 1):
            line_div = soup.new_tag('div', **{'class': 'line'})
            line_div.append(content)
            new_div.append(line_div)

        start.insert_before(new_div)

        # Удаляем старые элементы
        current = start
        while current and current != end:
            next_node = current.next_sibling
            current.decompose()
            current = next_node

        if end:
            end.decompose()

    return str(soup)


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

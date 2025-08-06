from bs4 import BeautifulSoup

from zip_postprocessor.utils.style_parser import _process_styles


def process_code_sections(html_content):
    """Обрабатывает блоки кода, сохраняя все строки и отступы"""
    soup = BeautifulSoup(html_content, 'html.parser')
    start_markers, end_markers = _find_code_markers(soup)
    _validate_markers(start_markers, end_markers)

    for start, end in zip(start_markers, end_markers):
        code_content = _collect_code_content(start, end)
        processed_lines = _process_code_content_with_indents(code_content)
        code_block = _create_preserved_code_block(soup, processed_lines)
        _replace_with_code_block(start, end, code_block)

    return str(soup)


def _process_code_content_with_indents(code_content):
    """Обрабатывает содержимое кода, сохраняя ВСЕ строки, включая пустые"""
    lines = []
    for element in code_content:
        # Получаем текст элемента как есть, с сохранением всех переносов
        text = str(element) if element.name else str(element)

        # Разбиваем на строки с сохранением пустых
        element_lines = text.split('\n') if '\n' in text else [text]

        # Для каждого элемента вычисляем отступ
        indent_size = 0
        if element.name == 'p' and element.get('style', ''):
            styles = element['style'].split(';')
            _, indent_size = _process_styles(styles)

        for line in element_lines:
            # Очищаем строку от HTML-тегов (если были)
            clean_line = BeautifulSoup(line, 'html.parser').get_text()

            lines.append({
                'text': clean_line,
                'indent': indent_size,
                'is_empty': not clean_line.strip()
            })

    return lines


def _create_preserved_code_block(soup, processed_lines):
    """Создает полную структуру блока кода с оберткой и сохранением всех строк"""
    # Создаем внешний контейнер
    code_container = soup.new_tag('div', **{'class': 'code-container'})

    # Создаем внутренний блок кода
    code_block = soup.new_tag('div', **{'class': 'code-block'})
    code_container.append(code_block)

    # Добавляем строки кода
    for i, line_data in enumerate(processed_lines):
        # Пропускаем дублирующиеся пустые строки
        if i > 0 and line_data['is_empty'] and processed_lines[i - 1]['is_empty']:
            continue

        line_div = soup.new_tag('div', **{'class': 'line'})
        code_tag = soup.new_tag('code')

        indent = ' ' * line_data['indent']
        text = line_data['text']

        if line_data['is_empty']:
            code_tag.string = indent + '\u200b'  # неразрывный пробел для пустых строк
        else:
            code_tag.string = indent + text

        line_div.append(code_tag)
        code_block.append(line_div)

    return code_container  # Возвращаем уже готовый контейнер с оберткой


def _find_code_markers(soup):
    """Находит маркеры начала и конца кода в HTML"""
    start_markers = soup.find_all(lambda tag:
                                  tag.name == 'p' and
                                  'START_CODE_SECTION' in tag.get_text())
    end_markers = soup.find_all(lambda tag:
                                tag.name == 'p' and
                                'END_CODE_SECTION' in tag.get_text())
    return start_markers, end_markers


def _validate_markers(start_markers, end_markers):
    """Проверяет, что маркеры кода парные"""
    if len(start_markers) != len(end_markers):
        raise ValueError("Непарные маркеры кода")


def _collect_code_content(start_marker, end_marker):
    """Собирает содержимое между маркерами, сохраняя пустые строки"""
    code_content = []
    current = start_marker.next_sibling

    while current and current != end_marker:
        # Сохраняем все элементы, включая текстовые узлы (которые могут быть пустыми строками)
        if isinstance(current, str) and current.strip() == '':
            # Создаем искусственный элемент для пустой строки
            empty_p = BeautifulSoup('<p></p>', 'html.parser').p
            empty_p.string = current
            code_content.append(empty_p)
        else:
            code_content.append(current)
        current = current.next_sibling

    return code_content


def _process_code_elements(code_content):
    """Обрабатывает элементы кода, заменяя отступы на пробелы"""
    for element in code_content:
        if element.name == 'p' and element.get('style', ''):
            styles = element['style'].split(';')
            new_styles, indent_size = _process_styles(styles)

            if indent_size > 0:
                element['style'] = ';'.join(new_styles).strip(';')
                _apply_indent_to_element(element, indent_size)


def _apply_indent_to_element(element, indent_size):
    """Добавляет пробелы в начало элемента, сохраняя пустые строки"""
    indent = ' ' * indent_size
    for content in element.contents:
        if isinstance(content, str):
            # Применяем отступ ко всем строкам, включая пустые
            content.replace_with(indent + content)
            return
    # Обработка вложенных элементов (например, span)
    first_span = element.find('span')
    if first_span and (first_span.string or first_span.string == ''):
        first_span.string.replace_with(indent + first_span.string)


def _create_code_block(soup, code_content):
    """Создает кастомный блок кода с построчной оберткой для стилизации и подсветки"""

    # Внешний контейнер
    code_block = soup.new_tag('div', **{'class': 'code-block'})

    # Получаем весь текст кода, сохраняя пустые строки
    raw_lines = []
    for element in code_content:
        text = element.get_text()
        # Разбиваем текст на строки, сохраняя пустые строки
        lines = text.split('\n') if '\n' in text else [text]
        raw_lines.extend(lines)

    # Каждую строку оборачиваем в div.line с вложенным <code>
    for i, line in enumerate(raw_lines):
        line_div = soup.new_tag('div', **{'class': 'line'})

        code_tag = soup.new_tag('code')
        # Сохраняем пустые строки как есть (содержащие только whitespace)
        code_tag.string = line if line.strip() != '' or not line else '\u200b'  # невидимый символ для полностью пустых строк

        line_div.append(code_tag)
        code_block.append(line_div)

    return code_block


def _replace_with_code_block(start_marker, end_marker, code_container):
    """Заменяет оригинальное содержимое готовым блоком кода с оберткой"""
    # Вставляем контейнер перед начальным маркером
    start_marker.insert_before(code_container)

    current = start_marker
    while current and current != end_marker:
        next_node = current.next_sibling
        current.decompose()
        current = next_node

    if end_marker:
        end_marker.decompose()

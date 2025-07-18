from bs4 import BeautifulSoup

from zip_postprocessor.utils.style_parser import _process_styles


def process_code_sections(html_content):
    """Обрабатывает блоки кода, заменяя text-indent и margin-left на пробелы и добавляя нумерацию строк"""
    soup = BeautifulSoup(html_content, 'html.parser')
    start_markers, end_markers = _find_code_markers(soup)

    _validate_markers(start_markers, end_markers)

    for start, end in zip(start_markers, end_markers):
        code_content = _collect_code_content(start, end)
        _process_code_elements(code_content)
        code_block = _create_code_block(soup, code_content)

        _replace_with_code_block(start, end, code_block)

    return str(soup)


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
    """Собирает содержимое между маркерами начала и конца кода"""
    code_content = []
    current = start_marker.next_sibling

    while current and current != end_marker:
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
    """Добавляет пробелы в начало элемента в соответствии с вычисленным отступом"""
    indent = ' ' * indent_size

    for content in element.contents:
        if isinstance(content, str) and content.strip():
            content.replace_with(indent + content)
            return

    first_span = element.find('span')
    if first_span and first_span.string:
        first_span.string.replace_with(indent + first_span.string)


def _create_code_block(soup, code_content):
    """Создает блок кода с нумерацией строк"""
    new_div = soup.new_tag('div', **{
        'class': 'code-block',
        'style': 'white-space: pre; font-family: monospace;'
    })

    for i, content in enumerate(code_content, 1):
        line_div = soup.new_tag('div', **{'class': 'line'})
        line_div.append(content)
        new_div.append(line_div)

    return new_div


def _replace_with_code_block(start_marker, end_marker, code_block):
    """Заменяет оригинальное содержимое новым блоком кода"""
    start_marker.insert_before(code_block)

    current = start_marker
    while current and current != end_marker:
        next_node = current.next_sibling
        current.decompose()
        current = next_node

    if end_marker:
        end_marker.decompose()

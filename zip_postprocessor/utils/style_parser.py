def _process_styles(styles):
    """Обрабатывает стили элемента, вычисляя общий отступ"""
    new_styles = []
    indent_size = 0

    for style in styles:
        style = style.strip()
        if not style:
            continue

        if 'text-indent' in style:
            indent_size += _parse_style_value(style)
        elif 'margin-left' in style:
            indent_size += _parse_style_value(style)
        else:
            new_styles.append(style)

    return new_styles, indent_size


def _parse_style_value(style):
    """Парсит значение стиля и преобразует его в количество пробелов"""
    try:
        value = style.split(':')[1].strip()
        if 'pt' in value:
            pt_value = float(value.replace('pt', ''))
            return int(pt_value / 9)
        elif 'em' in value:
            em_value = float(value.replace('em', ''))
            return int(em_value * 4)
        elif 'px' in value:
            px_value = float(value.replace('px', ''))
            return int(px_value / 9)
        elif 'cm' in value:
            cm_value = float(value.replace('cm', ''))
            return int(cm_value * 28.35 / 9)
        else:
            return int(float(value) / 9)
    except (ValueError, IndexError):
        return 0

import os

from PIL import Image


def optimize_image(input_path, output_path, max_size_kb=300):
    """
    Сжимает изображение без изменения формата:
    - PNG остаются PNG (с прозрачностью или без)
    - JPG остаются JPG
    - Всегда сохраняет оригинальное расширение файла
    """
    original_size = os.path.getsize(input_path) / 1024
    optimized = False
    original_ext = os.path.splitext(input_path)[1].lower()

    with Image.open(input_path) as img:
        # Определяем тип изображения
        if img.mode in ('RGBA', 'LA'):
            # PNG с прозрачностью
            img = img.convert('RGBA')
            file_type = 'PNG'
            quality = None
        elif original_ext == '.png':
            # PNG без прозрачности
            img = img.convert('RGB')
            file_type = 'PNG'
            quality = 85
        else:
            # JPG/JPEG
            file_type = 'JPEG'
            quality = 85

        # Сохраняем с итеративным сжатием
        while True:
            save_args = {'optimize': True}
            if quality:
                save_args['quality'] = quality

            if file_type == 'PNG' and img.mode != 'RGBA':
                # Для PNG без прозрачности уменьшаем палитру
                img = img.convert('P', palette=Image.ADAPTIVE, colors=256)

            img.save(output_path, **save_args)
            current_size = os.path.getsize(output_path) / 1024

            if current_size <= max_size_kb:
                optimized = True
                break

            if quality and quality > 30:
                quality -= 5
            else:
                # Если сжатие не помогает - уменьшаем размер
                width, height = img.size
                new_width = int(width * 0.9)
                new_height = int(height * 0.9)
                img = img.resize((new_width, new_height), Image.LANCZOS)

                if width == new_width:  # Защита от бесконечного цикла
                    break

    if optimized:
        pass
    else:
        print(f"Не удалось оптимизировать: {os.path.basename(input_path)}")

    return optimized

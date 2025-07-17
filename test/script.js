document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.code-block').forEach(block => {
        const btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.title = 'Копировать код';
        btn.textContent = 'Копировать';

        block.appendChild(btn);

        btn.addEventListener('click', function (e) {
            e.stopPropagation();

            // Собираем текст с учетом всех отступов
            const lines = Array.from(block.querySelectorAll('.line')).map(line => {
                // Получаем вычисленные стили элемента
                const style = window.getComputedStyle(line);

                // Парсим text-indent и margin-left
                const textIndent = parseIndent(style.textIndent);
                const marginLeft = parseIndent(style.marginLeft);

                // Суммируем отступы (в пунктах)
                const totalIndent = textIndent + marginLeft;

                // Конвертируем пункты в табы (1 таб ≈ 36pt)
                const tabCount = Math.round(totalIndent / 36);
                const indent = '\t'.repeat(tabCount > 0 ? tabCount : 0);

                // Удаляем номер строки если есть и добавляем вычисленный отступ
                return indent + line.textContent.replace(/^\d+\s/gm, '').trimEnd();
            });

            // Объединяем строки, убирая полностью пустые
            const code = lines.filter(line => line.trim() !== '').join('\n');

            navigator.clipboard.writeText(code)
                .then(() => {
                    btn.classList.add('copied');
                    btn.textContent = 'Скопировано!';
                    setTimeout(() => {
                        btn.classList.remove('copied');
                        btn.textContent = 'Копировать';
                    }, 2000);
                })
                .catch(err => {
                    console.error('Ошибка:', err);
                    btn.textContent = 'Ошибка';
                    btn.style.backgroundColor = '#dc3545';
                    setTimeout(() => {
                        btn.textContent = 'Копировать';
                        btn.style.backgroundColor = '';
                    }, 2000);
                });
        });

    });

    // Функция для конвертации значений в пункты
    function parseIndent(value) {
        if (value.endsWith('pt')) {
            return parseFloat(value);
        } else if (value.endsWith('px')) {
            return parseFloat(value) * 0.75; // 1px ≈ 0.75pt
        }
        return 0;
    }
});

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll(".code-block").forEach(block => {
        // 1. Собираем строки кода
        const lines = Array.from(block.querySelectorAll("code")).map(c => c.textContent);
        const fullText = lines.join("\n");

        // 2. Подсвечиваем весь код одной строкой
        const result = hljs.highlightAuto(fullText);
        const highlightedLines = result.value.split('\n');

        // 3. Очищаем и пересобираем блок с подсветкой
        block.innerHTML = "";
        highlightedLines.forEach(lineHtml => {
            const lineDiv = document.createElement("div");
            lineDiv.classList.add("line");

            const codeTag = document.createElement("code");
            codeTag.className = "hljs";
            codeTag.innerHTML = lineHtml || "\u200b"; // пустая строка

            lineDiv.appendChild(codeTag);
            block.appendChild(lineDiv);
        });

        // 4. Добавляем кнопку копирования
        const btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.title = 'Копировать код';
        btn.textContent = 'Копировать';
        block.appendChild(btn);

        // 5. Обработчик копирования
        btn.addEventListener('click', function (e) {
            e.stopPropagation();

            const lines = Array.from(block.querySelectorAll('.line')).map(line => {
                const style = window.getComputedStyle(line);
                const textIndent = parseIndent(style.textIndent);
                const marginLeft = parseIndent(style.marginLeft);
                const totalIndent = textIndent + marginLeft;
                const tabCount = Math.round(totalIndent / 36);
                const indent = '\t'.repeat(tabCount > 0 ? tabCount : 0);

                return indent + line.textContent.replace(/^\d+\s/gm, '').trimEnd();
            });

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

    // 💡 Вспомогательная функция
    function parseIndent(value) {
        return parseFloat(value) || 0;
    }
});
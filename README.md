pip install -r requirements.txt


source venv/bin/activate

python src/main.py      

git checkout -b feature/fix-1
git add .
git commit -m "Fix proportion"

 git push origin feature/fix-1

Смотри проведи ревизию всего кода, все мы лишние структуры может нагенерили и не используем, где можно упростить и тд глобально





 1. Общий стайл-гайд приложения Interview Assistant
Цветовая палитра
Основной фон: #f5f5f5 (очень светлый серый)
Основной акцент (кнопки, иконки): #2196F3 (ярко-синий)
Акцент для записи: #E53935 (ярко-красный)
Текст: #222 (основной), #fff (на цветных кнопках)
Второстепенный фон/блоки: #ffffff (чисто белый)
Блоки кода: #e6ecf1 (очень светлый синий/серый), текст кода #23241f
Шрифты
Основной: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif
Код: 'JetBrains Mono', 'Fira Mono', 'Consolas', 'Menlo', monospace
Кнопки
Форма: Круглая или с сильным скруглением (border-radius: 24px или 50%)
Размер: 48x48px для главных действий (например, запись)
Иконки: SVG, минималистичные, в стиле Material Design
Цвет: Красная кнопка для записи, с белой иконкой микрофона или точки
Иконки
Стиль: Flat, минимализм, без теней, без градиентов, только заливка
Размер: 32x32px или 24x24px внутри кнопки
Цвет: Белый на цветной кнопке, цветной на белом фоне
Панели и блоки
Скругление: 6px
Тень: Лёгкая, только для всплывающих подсказок
Отступы: 10-16px между элементами
Списки и markdown: Одинаковый стиль для текста и подсказок, поддержка кода
Визуализация волн
Фон: #fafafa
График: Акцентный синий
Прочее
UX: Все интерактивные элементы с hover-эффектом (изменение цвета, лёгкая тень)
Копирование кода: При клике на блок кода — копировать в буфер, показывать “Скопировано!”
2. Промпт для генерации иконки записи
Промпт для GPT/DALL-E/Stable Diffusion:
> "Create a flat, minimalistic, round record button icon for a modern desktop application. The button should be a solid, vibrant red (#E53935) circle with a simple white microphone or white dot in the center. No gradients, no shadows, no background, no border. The style should match Material Design guidelines. SVG format, 32x32 pixels."
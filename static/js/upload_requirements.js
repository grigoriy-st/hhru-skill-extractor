document.addEventListener('DOMContentLoaded', function() {
    let categoryCounter = 0;
    const container = document.getElementById('categories-container');

    // Добавление новой категории
    document.getElementById('add-category').addEventListener('click', function() {
        addCategoryBlock();
    });

    // Загрузка JSON-файла
    document.getElementById('upload-btn').addEventListener('click', function() {
        document.getElementById('template-upload').click();
    });

    document.getElementById('template-upload').addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const template = JSON.parse(e.target.result);
                loadTemplate(template);
                document.getElementById('file-name').textContent = file.name;
            } catch (error) {
                alert('Ошибка: файл должен быть в формате JSON');
            }
        };
        reader.readAsText(file);
    });

    // Функция загрузки шаблона
    function loadTemplate(template) {
        // Очистка предыдущих категорий
        container.innerHTML = '';
        
        // Установка названия шаблона
        if (template.template_name) {
            document.getElementById('template_name').value = template.template_name;
        }

        // Добавление категорий из JSON
        for (const [categoryName, skills] of Object.entries(template)) {
            if (categoryName === 'template_name') continue;
            addCategoryBlock(categoryName, skills);
        }
    }

    // Создание блока категории
    function addCategoryBlock(name = '', skills = []) {
        const categoryId = `category_${categoryCounter++}`;
        const block = document.createElement('div');
        block.className = 'category-block';
        block.innerHTML = `
            <div class="form-group">
                <label>Название категории:</label>
                <input type="text" name="categories[${categoryId}][name]" value="${escapeHtml(name)}" required>
            </div>
            <div class="form-group">
                <label>Навыки (каждый с новой строки):</label>
                <textarea name="categories[${categoryId}][skills]" rows="5" required>${skills.join('\n')}</textarea>
            </div>
            <button type="button" class="btn remove-btn">Удалить</button>
        `;
        
        // Обработчик удаления
        block.querySelector('.remove-btn').addEventListener('click', function() {
            block.remove();
        });
        
        container.appendChild(block);
    }

    // Экранирование HTML (защита от XSS)
    function escapeHtml(text) {
        return text.toString()
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
});
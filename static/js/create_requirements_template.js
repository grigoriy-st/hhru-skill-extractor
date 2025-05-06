let categoryCounter = 0;
    
document.getElementById('add-category').addEventListener('click', function() {
    const container = document.getElementById('categories-container');
    const categoryId = `category_${categoryCounter++}`;
    
    const categoryBlock = document.createElement('div');
    categoryBlock.className = 'category-block';
    categoryBlock.dataset.categoryId = categoryId;
    categoryBlock.innerHTML = `
        <div class="form-group">
            <label>Название категории:</label>
            <input type="text" name="name_${categoryId}" required>
        </div>
        <div class="form-group">
            <label>Навыки (каждый с новой строки):</label>
            <textarea name="skills_${categoryId}" rows="5" required></textarea>
        </div>
        <button type="button" class="remove-btn" onclick="this.parentNode.remove()">Удалить категорию</button>
    `;
    
    container.appendChild(categoryBlock);
});

// Обработчик для кнопки загрузки файла
document.getElementById('upload-btn').addEventListener('click', function() {
    document.getElementById('template-upload').click();
});

// Отображение имени файла
document.getElementById('template-upload').addEventListener('change', function(e) {
    const fileName = e.target.files[0]?.name || "Файл не выбран";
    document.getElementById('file-name').textContent = fileName;
    
    // Автоматическая загрузка при выборе файла
    if (e.target.files[0]) {
        uploadTemplate(e.target.files[0]);
    }
});

// Функция для обработки загрузки
async function uploadTemplate(file) {
    try {
        const content = await readFileAsJson(file);
        populateFormFromTemplate(content);
    } catch (error) {
        alert(`Ошибка: ${error.message}`);
    }
}

// Чтение файла как JSON
function readFileAsJson(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = event => {
            try {
                resolve(JSON.parse(event.target.result));
            } catch (e) {
                reject(new Error("Неверный JSON-формат"));
            }
        };
        reader.onerror = () => reject(new Error("Ошибка чтения файла"));
        reader.readAsText(file);
    });
}

// Заполнение формы из шаблона
function populateFormFromTemplate(template) {
    // Очищаем существующие категории
    document.getElementById('categories-container').innerHTML = '';
    
    // Устанавливаем имя шаблона
    document.getElementById('template_name').value = template.template_name || '';
    
    // Добавляем категории
    for (const [categoryName, skills] of Object.entries(template)) {
        if (categoryName === 'template_name') continue;
        
        // Добавляем новую категорию
        document.getElementById('add-category').click();
        
        // Получаем последнюю добавленную категорию
        const blocks = document.querySelectorAll('.category-block');
        const lastBlock = blocks[blocks.length - 1];
        
        // Заполняем данные
        lastBlock.querySelector('[name$="_name"]').value = categoryName;
        lastBlock.querySelector('[name$="_skills"]').value = skills.join('\n');
    }
}
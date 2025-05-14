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
}document.querySelector('.vacancy-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Показываем progress bar
    document.getElementById('progress-container').style.display = 'block';
    document.getElementById('progress-status').textContent = 'Анализ начат...';
    
    // Собираем данные формы
    const formData = new FormData(this);
    
    // Отправляем запрос на сервер
    fetch("{{ url_for('work_with_analyzer.get_analyzer_page') }}", {
        method: 'POST',
        body: formData,
        // Добавляем redirect: 'manual' для ручной обработки редиректа
        redirect: 'manual'
    })
    .then(response => {
        // Если сервер вернул редирект (код 302)
        if (response.status === 302) {
            // Получаем URL редиректа из заголовка 'Location'
            const redirectUrl = response.headers.get('Location');
            // Перенаправляем вручную
            window.location.href = redirectUrl;
        } else {
            // Если это не редирект, обрабатываем как JSON
            return response.json();
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('progress-status').textContent = 'Ошибка: ' + error.message;
    });
});     // Если ответ не JSON, пробуем прочитать как текст
        return response.text().then(text => {
            throw new Error(`Ожидался JSON, но получен: ${text.slice(0, 100)}...`);
        });
    })
    .then(data => {
        if (data) {
            // Обработка данных, если они есть
            console.log("Данные с сервера:", data);
            if (data.redirect) {
                window.location.href = data.redirect;
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        progressStatus.textContent = 'Ошибка: ' + error.message;
    });
});
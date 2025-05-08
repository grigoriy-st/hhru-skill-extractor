document.querySelector('.vacancy-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // Показываем progress bar
    document.getElementById('progress-container').style.display = 'block';
    
    // Собираем данные формы
    const formData = new FormData(this);
    
    // Отправляем запрос на сервер
    fetch("{{ url_for('work_with_analyzer.get_analyzer_page') }}", {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        // Обновляем progress bar
        updateProgress(data.processed, data.total);
        
        // Когда обработка завершена
        if (data.completed) {
            console.log("Task is complete!")
            document.getElementById('progress-status').textContent = 'Анализ завершен!';
            // Показываем результаты
            displayResults(data.results);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('progress-status').textContent = 'Ошибка: ' + error.message;
    });
});

function updateProgress(processed, total) {
    const percent = Math.round((processed / total) * 100);
    document.getElementById('progress').style.width = percent + '%';
    // document.getElementById('progress-count').textContent = `${processed}/${total}`;
    document.getElementById('progress-status').textContent = `Анализируется... (${percent}%)`;
}

function displayResults(results) {
    const resultsContainer = document.getElementById('results');
    resultsContainer.style.display = 'block';
    
    // Форматируем результаты для отображения
    let html = '<h3>Результаты анализа:</h3><ul>';
    for (const [skill, count] of Object.entries(results)) {
        html += `<li>${skill}: ${count}</li>`;
    }
    html += '</ul>';
    
    resultsContainer.innerHTML = html;
}

const eventSource = new EventSource('/progress');

eventSource.onmessage = function(e) {
    const progress = parseInt(e.data);
    updateProgress(progress, 100);
    
    if (progress === 100) {
        eventSource.close();
        document.getElementById('progress-status').textContent = 'Анализ завершен!';
    }
};
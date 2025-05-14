document.querySelector('.vacancy-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const form = e.target;
    
    // Получаем URL из data-атрибута
    const actionUrl = form.action;
    const resultsUrl = form.dataset.resultsUrl || '/results'; // fallback
    
    // Показываем прогресс
    const progressContainer = document.getElementById('progress-container');
    const progressStatus = document.getElementById('progress-status');
    progressContainer.style.display = 'block';
    progressStatus.textContent = 'Анализ начат...';
    
    // Отправка формы
    fetch(actionUrl, {
        method: 'POST',
        body: new FormData(form),
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (response.redirected) {
            window.location.href = response.url;
        } else if (response.ok) {
            window.location.href = resultsUrl;
        } else {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        progressStatus.textContent = 'Ошибка: ' + error.message;
    });
});
document.querySelector('.vacancy-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const form = e.target;

    document.getElementById('progress-container').style.display = 'block';
    updateProgress(0, 'Подготовка к анализу...');

    fetch('/analyzer', {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: new FormData(form)
    })
    .then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        let buffer = '';

        function read() {
            reader.read().then(({ done, value }) => {
                if (done) return;

                buffer += decoder.decode(value, { stream: true });

                let lines = buffer.split('\n');
                buffer = lines.pop(); // Оставим последнюю строку

                for (let line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const data = JSON.parse(line);
                        if (data.redirect) {
                            window.location.href = data.redirect;
                        } else if (data.error) {
                            updateProgress(0, data.message || data.error);
                            console.error('Ошибка:', data.message || data.error);
                        } else {
                            updateProgress(data.progress, data.message);
                        }
                    } catch (err) {
                        console.error('Ошибка парсинга JSON:', err, line);
                    }
                }

                read();
            });
        }

        read();
    })
    .catch(err => {
        updateProgress(0, 'Ошибка соединения.');
        console.error(err);
    });
});

function updateProgress(percent, message) {
    document.getElementById('progress').style.width = percent + '%';
    document.getElementById('progress-status').textContent = message;
    document.getElementById('progress-percent').textContent = percent + '%';
}

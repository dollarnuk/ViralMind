document.getElementById('generateBtn').addEventListener('click', async () => {
    const urlInput = document.getElementById('videoUrl');
    const url = urlInput.value.trim();
    const status = document.getElementById('status');
    const loader = document.getElementById('loader');
    const btn = document.getElementById('generateBtn');
    const resultsDiv = document.getElementById('results');

    if (!url) {
        alert('Будь ласка, введіть посилання');
        return;
    }

    // Reset UI
    resultsDiv.innerHTML = '';
    btn.disabled = true;
    loader.style.display = 'block';
    status.innerText = 'Ініціалізація...';

    try {
        const response = await fetch('/api/v1/process-video', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ video_url: url })
        });

        if (!response.ok) throw new Error('Помилка сервера');

        const data = await response.json();
        pollStatus(data.task_id);

    } catch (err) {
        status.innerText = 'Сталася помилка. Спробуйте ще раз.';
        btn.disabled = false;
        loader.style.display = 'none';
        console.error(err);
    }
});

async function pollStatus(taskId) {
    const status = document.getElementById('status');
    const loader = document.getElementById('loader');
    const btn = document.getElementById('generateBtn');
    const resultsDiv = document.getElementById('results');

    const interval = setInterval(async () => {
        try {
            const res = await fetch(`/api/v1/task-status/${taskId}`);
            const data = await res.json();

            if (data.status === 'SUCCESS' || data.status === 'completed' || data.result?.status === 'completed') {
                clearInterval(interval);
                status.innerText = 'Готово!';
                loader.style.display = 'none';
                btn.disabled = false;

                // Display results
                const shorts = data.result?.shorts || [];
                if (shorts.length > 0) {
                    shorts.forEach(short => {
                        const item = document.createElement('div');
                        item.className = 'short-item';
                        item.innerHTML = `
                            <video src="/static/output/${short.file_path.split(/[\\/]/).pop()}" muted loop onmouseover="this.play()" onmouseout="this.pause()"></video>
                            <a href="/static/output/${short.file_path.split(/[\\/]/).pop()}" target="_blank" class="short-link">Завантажити</a>
                        `;
                        resultsDiv.appendChild(item);
                    });
                }
            } else if (data.status === 'FAILURE') {
                clearInterval(interval);
                status.innerText = 'Помилка обробки: ' + (data.result?.error || 'невідома помилка');
                loader.style.display = 'none';
                btn.disabled = false;
            } else {
                // Update specific state
                const state = data.status;
                const progress = data.result?.progress || 0;
                status.innerText = `${state}... ${progress}%`;
            }

        } catch (err) {
            console.error('Polling error:', err);
        }
    }, 2000);
}

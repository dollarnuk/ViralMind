document.addEventListener('DOMContentLoaded', () => {
    const videoUrl = document.getElementById('videoUrl');
    const generateBtn = document.getElementById('generateBtn');
    const dropZone = document.getElementById('dropZone');
    const videoFile = document.getElementById('videoFile');
    const processingSection = document.getElementById('processingSection');
    const statusText = document.getElementById('status');
    const progressFill = document.getElementById('progressFill');
    const resultsGrid = document.getElementById('results');

    // --- Drag & Drop Initialization ---
    dropZone.addEventListener('click', () => videoFile.click());

    videoFile.addEventListener('change', () => {
        if (videoFile.files.length) {
            uploadFile(videoFile.files[0]);
        }
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drop-zone--over');
    });

    ['dragleave', 'dragend'].forEach(type => {
        dropZone.addEventListener(type, () => {
            dropZone.classList.remove('drop-zone--over');
        });
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length) {
            videoFile.files = e.dataTransfer.files;
            uploadFile(e.dataTransfer.files[0]);
        }
        dropZone.classList.remove('drop-zone--over');
    });

    // --- URL Generation ---
    generateBtn.addEventListener('click', async () => {
        const url = videoUrl.value.trim();
        if (!url) return alert('Будь ласка, введіть посилання');

        startUI();
        try {
            const response = await fetch('/api/v1/process-video', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ video_url: url })
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Помилка сервера');
            pollStatus(data.task_id);
        } catch (err) {
            handleError(err.message);
        }
    });

    // --- Core Functions ---
    function startUI() {
        resultsGrid.innerHTML = '';
        processingSection.style.display = 'block';
        generateBtn.disabled = true;
        statusText.innerText = 'Ініціалізація...';
        progressFill.style.width = '0%';
    }

    function handleError(msg) {
        statusText.innerText = 'Помилка: ' + msg;
        generateBtn.disabled = false;
        progressFill.style.backgroundColor = '#ff453a';
    }

    async function uploadFile(file) {
        startUI();
        statusText.innerText = 'Завантаження відео на сервер...';

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/v1/upload-video', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            if (!response.ok) throw new Error(data.detail || 'Помилка завантаження');
            pollStatus(data.task_id);
        } catch (err) {
            handleError(err.message);
        }
    }

    function pollStatus(taskId) {
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`/api/v1/task-status/${taskId}`);
                const data = await res.json();

                if (data.status === 'SUCCESS' || data.status === 'completed' || data.result?.status === 'completed') {
                    clearInterval(interval);
                    statusText.innerText = 'Готово! Ваші Shorts створені.';
                    progressFill.style.width = '100%';
                    generateBtn.disabled = false;
                    displayResults(data.result?.shorts || []);
                } else if (data.status === 'FAILURE') {
                    clearInterval(interval);
                    handleError(data.result?.error || 'Невідома помилка обробки');
                } else {
                    const progress = data.result?.progress || 0;
                    statusText.innerText = `${data.status}... ${progress}%`;
                    progressFill.style.width = `${progress}%`;
                }
            } catch (err) {
                console.error('Polling error:', err);
            }
        }, 2000);
    }

    function displayResults(shorts) {
        resultsGrid.innerHTML = '';
        if (!shorts.length) {
            statusText.innerText = 'Обробка завершена, але цікавих моментів не знайдено.';
            return;
        }

        shorts.forEach((short, i) => {
            const filename = short.file_path.split(/[\\/]/).pop();
            const card = document.createElement('div');
            card.className = 'short-card';
            card.innerHTML = `
                <video src="/static/output/${filename}" muted loop playsinline></video>
                <div class="card-footer">
                    <span style="font-size: 13px; color: #86868b">Short #${i + 1}</span>
                    <a href="/static/output/${filename}" target="_blank" class="download-link" download>Завантажити</a>
                </div>
            `;

            // Auto play on hover
            card.addEventListener('mouseenter', () => card.querySelector('video').play());
            card.addEventListener('mouseleave', () => card.querySelector('video').pause());

            resultsGrid.appendChild(card);
        });
    }
});

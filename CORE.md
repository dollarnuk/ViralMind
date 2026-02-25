# CORE.md - ViralMind Project Documentation

## Інформація про проєкт

**Назва**: ViralMind
**Короткий опис**: Автоматизований сервіс для створення вірусних Shorts з довгих відео за посиланням.
**Основна мова інтерфейсу**: Українська (планується) / Англійська (API)

**Технологічний стек**:
- Backend: Python 3.10, FastAPI, Celery
- База даних: Redis (для черг та тимчасових даних)
- Frontend: Vanilla JS + CSS (Apple-like design) - *у розробці*
- AI/ML: PySceneDetect, MediaPipe, Librosa
- Деплой: Docker, EasyPanel
- Інше: FFmpeg, yt-dlp

**Структура файлів проєкту**:
```text
ViralMind/
├── app/
│   ├── api/          # Ендпоінти FastAPI (v1)
│   ├── core/         # Конфігурація (Pydantic Settings)
│   ├── services/     # Логіка (Downloader, Analyzer, Generator)
│   ├── schemas/      # Pydantic моделі (запити/відповіді)
│   ├── tasks/        # Фонові завдання (Celery)
│   └── main.py       # Точка входу в додаток
├── downloads/        # Тимчасове сховище для завантажених відео
├── output/           # Директорія для згенерованих Shorts
├── static/           # Статичні файли фронтенду
├── docker/           # Конфігурації Docker
├── Dockerfile        # Образ додатка
├── docker-compose.yml # Оркестрація (App + Redis)
└── requirements.txt  # Залежності Python
```

**Головні можливості**:
- Автоматичне завантаження відео за URL (YouTube та інші).
- Визначення "вірусних" моментів за зміною сцен та рівнем звуку.
- Розумне кадрування (9:16) з фокусом на обличчях (MediaPipe).
- Автоматична генерація Shorts за допомогою FFmpeg.
- Інтеграція з n8n через API.

**API ендпоінти**:
```text
- POST /api/v1/process-video - Запустити обробку відео
- GET /api/v1/task-status/{task_id} - Перевірити статус завдання
```

**Змінні оточення (.env)**:
```text
- REDIS_URL=redis://localhost:6379/0 (URL для підключення до Redis)
- DOWNLOAD_DIR=downloads (Папка для завантажень)
- OUTPUT_DIR=output (Папка для результатів)
```

**Авторизація**: Немає (MVP)
**Монетизація**: Немає (MVP)

**Як запустити локально**:
```bash
# Клонувати репозиторій
# Встановити залежності
pip install -r requirements.txt

# Запустити Redis (якщо локально)
# Запустити додаток
python -m app.main
```

**Як задеплоїти**:
```bash
# Використовуючи Docker Compose
docker-compose up -d --build
```

**Відомі баги**: Немає (початкова стадія)

**Важливі архітектурні рішення / нюанси**:
- Використання **MediaPipe** для Face Tracking на CPU (мінімізація витрат).
- Асинхронна обробка через **Celery** для уникнення блокувань API.
- Пріоритет на **Open Source** інструменти (FFmpeg, yt-dlp).

**Що заплановано / в розробці**:
- [ ] Реалізація аналізу вірусності (Scene Change + Audio).
- [ ] Розумне кадрування 9:16.
- [ ] Apple-like Web UI.
- [ ] Повна інтеграція з n8n (webhooks).

---

## GEMINI FLASH — СИСТЕМНІ ІНСТРУКЦІЇ ТА РЕКОМЕНДАЦІЇ

### 1. Визначення ролі

Ти — Senior Python/FastAPI розробник та AI/ML спеціаліст, який працює над проєктом **ViralMind**. Твоє основне завдання — допомагати розвивати цей проєкт від MVP до повноцінного продукту.

**Твої компетенції в контексті цього проєкту:**
- Глибоке знання Python 3.10, FastAPI, Celery, Redis
- Досвід роботи з FFmpeg (subprocess, фільтри, кодеки)
- Практичний досвід із PySceneDetect, MediaPipe (Face Detection/Mesh), Librosa
- Розуміння Docker та docker-compose для оркестрації сервісів
- Знання шаблонів проєктування для асинхронних пайплайнів обробки медіа

**Принципи поведінки:**
- Завжди враховуй поточний стан проєкту: що вже реалізовано, а що ні (див. структуру вище)
- Не пропонуй переписувати те, що вже працює, без вагомої причини
- Пріоритезуй простоту та читабельність коду над зайвою абстракцією
- Кожна відповідь повинна містити конкретний код, а не лише теоретичні поради
- Якщо пропонуєш зміни — завжди вказуй точний шлях до файлу та повний код модуля
- Коментарі в коді — англійською, документація та спілкування — українською

---

### 2. Правила стилю коду

#### 2.1 Загальні правила
- **PEP 8** — суворе дотримання (рядок до 99 символів, 4 пробіли для відступів)
- **Type hints** — обов'язкові для всіх функцій, методів та змінних класів
- **Docstrings** — у форматі Google Style для всіх публічних функцій та класів
- **Іменування**: `snake_case` для функцій/змінних, `PascalCase` для класів, `UPPER_SNAKE_CASE` для констант

#### 2.2 Async-патерни
- Всі ендпоінти FastAPI — `async def`
- Блокуючі операції (FFmpeg, yt-dlp, MediaPipe) виконувати ТІЛЬКИ через Celery worker, НЕ в event loop FastAPI
- Якщо потрібно запустити синхронну функцію з async-контексту — використовувати `asyncio.to_thread()` або `run_in_executor()`
- Ніколи не використовувати `time.sleep()` в async-коді — тільки `await asyncio.sleep()`

```python
# ПРАВИЛЬНО — ендпоінт делегує роботу Celery
@router.post("/process-video", response_model=VideoResponse)
async def process_video(request: VideoRequest) -> VideoResponse:
    task = process_video_task.delay(str(request.video_url), request.num_shorts)
    return VideoResponse(task_id=task.id, status="queued")

# НЕПРАВИЛЬНО — блокуюча операція в async ендпоінті
@router.post("/process-video")
async def process_video(request: VideoRequest):
    result = downloader.download(str(request.video_url))  # БЛОКУЄ event loop!
    return {"file": result}
```

#### 2.3 Обробка помилок
- Кожен сервіс повинен мати власні кастомні виключення в `app/core/exceptions.py`
- Ендпоінти обгортати через `try/except` з чіткими HTTP-кодами
- Celery таски повинні логувати помилки через `logging` та зберігати статус `FAILURE` з повідомленням

```python
# app/core/exceptions.py
class ShortsGenieError(Exception):
    """Базова помилка проєкту."""

class DownloadError(ShortsGenieError):
    """Помилка завантаження відео."""

class AnalysisError(ShortsGenieError):
    """Помилка аналізу відео."""

class CroppingError(ShortsGenieError):
    """Помилка кадрування."""
```

#### 2.4 Логування
- Використовувати стандартний `logging` модуль Python
- Формат: `%(asctime)s | %(name)s | %(levelname)s | %(message)s`
- Кожен сервіс створює свій логер: `logger = logging.getLogger(__name__)`
- Рівні: `DEBUG` для розробки, `INFO` для production, `ERROR` для критичних збоїв

---

### 3. Архітектурні вказівки

#### 3.1 Структура модулів
Кожен новий сервіс створювати як окремий файл у `app/services/`. Підтримувати таку структуру:

```text
app/
├── api/v1/
│   └── endpoints.py          # Всі REST ендпоінти (розширювати тут)
├── core/
│   ├── config.py              # Pydantic Settings (вже існує)
│   ├── exceptions.py          # Кастомні виключення (СТВОРИТИ)
│   └── logging_config.py      # Конфігурація логування (СТВОРИТИ)
├── schemas/
│   ├── video_request.py       # Вже існує — VideoRequest, VideoResponse, ShortInfo
│   └── task_schemas.py        # Схеми для статусів Celery тасків (СТВОРИТИ)
├── services/
│   ├── video_downloader.py    # Вже існує — завантаження через yt-dlp
│   ├── video_analyzer.py      # Аналіз вірусних моментів (СТВОРИТИ)
│   ├── smart_cropper.py       # Кадрування 9:16 з face tracking (СТВОРИТИ)
│   └── shorts_generator.py    # Оркестрація повного пайплайну (СТВОРИТИ)
├── tasks/
│   ├── celery_app.py          # Ініціалізація Celery (СТВОРИТИ)
│   └── worker.py              # Визначення тасків (СТВОРИТИ)
└── main.py                    # Точка входу (вже існує)
```

#### 3.2 Принцип створення нових сервісів
Кожен сервіс — це клас з чітко визначеним інтерфейсом. Шаблон:

```python
# app/services/{service_name}.py
import logging
from app.core.config import settings
from app.core.exceptions import ShortsGenieError

logger = logging.getLogger(__name__)

class ServiceName:
    """Опис призначення сервісу."""

    def __init__(self, **kwargs):
        # Ініціалізація ресурсів
        pass

    def process(self, input_data: InputType) -> OutputType:
        """Основний метод обробки."""
        logger.info(f"Processing: {input_data}")
        try:
            result = self._do_work(input_data)
            return result
        except Exception as e:
            logger.error(f"Failed: {e}")
            raise ShortsGenieError(str(e)) from e

    def cleanup(self) -> None:
        """Очистка тимчасових файлів."""
        pass

# Глобальний інстанс (singleton)
service_name = ServiceName()
```

#### 3.3 Правила для docker-compose
- Кожен новий сервіс (worker, beat) додавати як окремий service у `docker-compose.yml`
- Всі сервіси мають спільні volumes: `downloads`, `output`
- Worker повинен мати доступ до FFmpeg (використовувати той самий Dockerfile)

---

### 4. Пріоритетна дорожня карта імплементації

#### КРОК 1: Налаштування Celery Worker (ПРІОРИТЕТ: КРИТИЧНИЙ)

**Мета:** Перевести обробку відео з mock-відповідей на реальну фонову обробку.

**Файли для створення:**

**`app/tasks/celery_app.py`** — ініціалізація Celery:
```python
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "viralmind",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,       # 10 хвилин макс на таск
    task_soft_time_limit=540,  # soft limit — 9 хв
    worker_max_tasks_per_child=50,  # перезапуск worker після 50 тасків (memory leak захист)
)
```

**`app/tasks/worker.py`** — визначення тасків:
```python
from app.tasks.celery_app import celery_app
from app.services.video_downloader import downloader

@celery_app.task(bind=True, name="process_video")
def process_video_task(self, video_url: str, num_shorts: int = 3) -> dict:
    self.update_state(state="DOWNLOADING")
    file_path = downloader.download(video_url)
    # Далі буде: аналіз, кадрування, генерація
    return {"status": "completed", "file": file_path}
```

**Зміни в `docker-compose.yml`** — додати worker сервіс:
```yaml
  worker:
    build: .
    command: celery -A app.tasks.celery_app worker --loglevel=info --concurrency=2
    volumes:
      - .:/app
      - downloads:/app/downloads
      - output:/app/output
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis
```

**Зміни в `app/api/v1/endpoints.py`** — замінити mock на реальний виклик Celery.

---

#### КРОК 2: Сервіс аналізу відео (ПРІОРИТЕТ: ВИСОКИЙ)

**Мета:** Знаходити "вірусні" моменти на основі зміни сцен та піків аудіо.

**Файл: `app/services/video_analyzer.py`**

Логіка:
1. **PySceneDetect** — знайти моменти різких змін сцени (`ContentDetector` з threshold ~27.0)
2. **Librosa** — виділити аудіо, знайти піки гучності (onset detection + RMS energy)
3. **Комбінований скоринг** — зважити обидва сигнали та повернути топ-N моментів

```python
from scenedetect import detect, ContentDetector
import librosa
import numpy as np

class VideoAnalyzer:
    def __init__(self, scene_threshold: float = 27.0, audio_hop_length: int = 512):
        self.scene_threshold = scene_threshold
        self.audio_hop_length = audio_hop_length

    def find_viral_moments(
        self,
        video_path: str,
        num_moments: int = 3,
        target_duration: int = 30
    ) -> list[dict]:
        """
        Повертає список найкращих моментів:
        [{"start": float, "end": float, "score": float}, ...]
        """
        scenes = self._detect_scenes(video_path)
        audio_peaks = self._analyze_audio(video_path)
        moments = self._combine_and_rank(scenes, audio_peaks, num_moments, target_duration)
        return moments
```

**Важливо:**
- `librosa.load()` вміє читати аудіо з відеофайлів через ffmpeg backend — окреме виділення аудіо не потрібне
- Threshold для `ContentDetector` підбирати емпірично: 20-35 для різного контенту
- Додати параметр `min_scene_duration` щоб відфільтрувати надто короткі сцени (< 2 сек)

---

#### КРОК 3: Сервіс розумного кадрування (ПРІОРИТЕТ: ВИСОКИЙ)

**Мета:** Обрізати горизонтальне відео (16:9) у вертикальне (9:16) з фокусом на обличчях.

**Файл: `app/services/smart_cropper.py`**

Логіка:
1. **MediaPipe Face Detection** — знайти обличчя на ключових кадрах (кожні 0.5-1 сек)
2. **Розрахунок crop region** — центрувати на середню позицію обличчя
3. **Плавна інтерполяція** — згладити рух crop вікна між кадрами (уникнути "стрибків")
4. **FFmpeg** — виконати crop + scale з використанням розрахованих координат

```python
import mediapipe as mp
import cv2
import subprocess

class SmartCropper:
    def __init__(self, sample_interval: float = 0.5):
        self.sample_interval = sample_interval
        self.face_detection = mp.solutions.face_detection.FaceDetection(
            model_selection=1,      # 1 = full range model (до 5м)
            min_detection_confidence=0.5
        )

    def crop_segment(
        self,
        input_path: str,
        output_path: str,
        start_time: float,
        duration: float
    ) -> str:
        """Вирізати та обрізати сегмент відео у 9:16."""
        face_positions = self._detect_faces_in_segment(input_path, start_time, duration)
        crop_x = self._calculate_smooth_crop(face_positions, input_path)
        self._execute_ffmpeg_crop(input_path, output_path, start_time, duration, crop_x)
        return output_path
```

**Критичні нюанси MediaPipe:**
- `model_selection=1` — для повнокадрових облич (більша дистанція від камери)
- MediaPipe працює з RGB, а `cv2.VideoCapture` повертає BGR — обов'язково: `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)`
- Закривати `cv2.VideoCapture` через `try/finally`
- Якщо обличчя не знайдено — fallback на центральну частину кадру

---

#### КРОК 4: Інтеграція повного пайплайну (ПРІОРИТЕТ: СЕРЕДНІЙ)

**Файл: `app/services/shorts_generator.py`**

Оркеструє весь процес: `download -> analyze -> crop кожного моменту -> зберегти результати`

Оновити `app/tasks/worker.py` — стани таски: `DOWNLOADING` → `ANALYZING` → `CROPPING` → `COMPLETED`

Додати ендпоінт `GET /api/v1/results/{task_id}` — список згенерованих Shorts з URL для скачування.

---

#### КРОК 5: Frontend (ПРІОРИТЕТ: СЕРЕДНІЙ)

**Директорія: `static/`** — Vanilla JS + CSS (Apple-like дизайн)

Функціонал: поле URL, кнопка "Створити Shorts", прогрес-бар, галерея результатів.

---

#### КРОК 6: Інтеграція з n8n (ПРІОРИТЕТ: НИЗЬКИЙ)

Додати `webhook_url: Optional[HttpUrl]` до `VideoRequest`. Після завершення обробки — POST-запит на webhook через `aiohttp`.

---

### 5. Стратегія тестування

```text
tests/
├── conftest.py           # Фікстури (test client, mock redis, temp dirs)
├── test_api/
│   └── test_endpoints.py # Тести ендпоінтів
├── test_services/
│   ├── test_downloader.py
│   ├── test_analyzer.py
│   └── test_cropper.py
└── test_tasks/
    └── test_worker.py
```

**Принципи:**
- `pytest` + `pytest-asyncio` для async тестів
- `httpx.AsyncClient` для тестування FastAPI ендпоінтів
- Мокати зовнішні залежності: `yt-dlp` через `unittest.mock.patch`, FFmpeg через підміну subprocess
- Для Celery — `celery_app.conf.update(task_always_eager=True)` в тестах
- Тримати тестове відео (5-10 сек, < 5MB) у `tests/fixtures/`

---

### 6. Безпека

#### 6.1 Валідація вхідних даних
- URL валідувати через `pydantic.HttpUrl` (вже є)
- Додати whitelist доменів: `youtube.com`, `youtu.be`, `tiktok.com`
- Обмежити: `num_shorts` — 1-10, `preferred_duration` — 15-60 сек

```python
class VideoRequest(BaseModel):
    video_url: HttpUrl
    num_shorts: int = Field(default=3, ge=1, le=10)
    preferred_duration: int = Field(default=30, ge=15, le=60)

    @field_validator("video_url")
    @classmethod
    def validate_domain(cls, v: HttpUrl) -> HttpUrl:
        allowed = ["youtube.com", "youtu.be", "www.youtube.com"]
        if v.host not in allowed:
            raise ValueError(f"Domain {v.host} not allowed")
        return v
```

#### 6.2 Rate Limiting
- `slowapi` — 5-10 запитів/хвилину на IP

#### 6.3 Очистка файлів
- Після генерації Shorts — видаляти вихідне відео
- TTL для `output/` — 24 години (Celery Beat задача)
- В `app/core/config.py` додати `FILE_RETENTION_HOURS: int = 24`

---

### 7. Оптимізація продуктивності

#### 7.1 Обробка відео
- FFmpeg: `-preset fast` (або `veryfast` для швидкості)
- FFmpeg: `-ss` ПЕРЕД `-i` для input seeking (швидше)
- Обмежити роздільну здатність: `'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]'`

#### 7.2 Управління пам'яттю
- MediaPipe: обробляти кадри по одному, не зберігати весь відеопотік
- Librosa: `sr=22050` (не 44100) — вдвічі менше пам'яті
- NumPy: явно `del array` + `gc.collect()` після обробки
- Celery: `worker_max_tasks_per_child=50`

#### 7.3 Конкурентність
- `--concurrency=2` для 2-4 CPU серверів
- Не ставити concurrency > кількості CPU ядер
- Використовувати `prefork` pool — НЕ `eventlet`/`gevent` для CPU-bound задач

#### 7.4 Тимчасові файли
- `tempfile.mkdtemp()` для проміжних файлів FFmpeg
- `try/finally` з `shutil.rmtree()` для гарантованої очистки

---

### 8. Типові помилки та як їх уникнути

#### 8.1 FFmpeg
| Помилка | Причина | Рішення |
|---------|---------|---------|
| `moov atom not found` | Завантаження перервалось | Перевіряти цілісність файлу перед обробкою |
| `crop out of bounds` | Crop region за межами кадру | Clamp координати: `min(crop_x, width - crop_w)` |
| Зависання subprocess | FFmpeg чекає stdin | Завжди `-y` та `capture_output=True` |
| Великий розмір output | CRF занизький | `-crf 23` для балансу якість/розмір |

#### 8.2 yt-dlp
| Помилка | Причина | Рішення |
|---------|---------|---------|
| `HTTP Error 403` | YouTube блокує IP | Retry з exponential backoff; proxy |
| `Video unavailable` | Приватне/видалене відео | Перехоплювати `yt_dlp.utils.DownloadError` |
| Файл не знайдено після download | `prepare_filename()` без розширення | `glob.glob(f"{base_path}.*")` |

#### 8.3 MediaPipe
| Помилка | Причина | Рішення |
|---------|---------|---------|
| `TypeError: input image is not valid` | BGR замість RGB | `cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)` |
| Обличчя не знайдено | Далеке обличчя | `model_selection=1`, confidence до 0.3 |
| Витік пам'яті | Не закритий FaceDetection | `with` context manager |

#### 8.4 Celery
| Помилка | Причина | Рішення |
|---------|---------|---------|
| `Received unregistered task` | Worker не бачить модуль | Перевірити import та `include` |
| Task зависла назавжди | Немає time limit | `task_time_limit` + `task_soft_time_limit` |
| `ConnectionError: Redis` | Redis недоступний | `retry_on_startup=True`, health check |

---

### 9. Чекліст для додавання нового сервісу

1. Створити `app/services/{service_name}.py` за шаблоном з розділу 3.2
2. Додати кастомні виключення в `app/core/exceptions.py`
3. Якщо потрібні налаштування — додати в `app/core/config.py`
4. Якщо сервіс з API — додати/оновити схеми в `app/schemas/`
5. Якщо фонова робота — додати Celery таск в `app/tasks/worker.py`
6. Додати тести в `tests/test_services/test_{service_name}.py`
7. Оновити `requirements.txt` якщо нова залежність
8. Оновити цей файл `CORE.md`

---

### 10. Контекст для прийняття рішень

- **Сервер**: CPU-only (без GPU) — ML-операції оптимізовані для CPU
- **Стадія**: ранній MVP — краще швидко робоча реалізація ніж ідеальна архітектура
- **Деплой**: Docker на EasyPanel — один сервер, 2-4 CPU, 4-8 GB RAM
- **Масштаб**: 10-50 запитів/день — не потрібен auto-scaling
- **Мова**: код та коментарі англійською, UI та документація українською

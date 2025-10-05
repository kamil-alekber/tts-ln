# TTS Light Novel Processing System

## Architecture Overview

This is a distributed text-to-speech (TTS) processing pipeline for web novels that:
1. Scrapes book/chapter content from novelbin.com using headless Playwright
2. Processes each chapter through a Celery worker chain: **book → metadata → chapter → tts → converter → completed → sync**
3. Stores state in Redis (acting as both Celery broker and application database)
4. Generates audiobook MP4 files with embedded cover images and subtitles
5. Syncs completed files to a remote NAS via rsync

**Critical Design Decision**: Each worker type runs in its own Docker container with dedicated Celery queue. Workers communicate by dispatching tasks to the next queue in the chain (see `app.send_task()` calls in `workers/*/tasks.py`).

## Key Components

- **`libs/models.py`**: Redis-backed dataclasses (`ChapterProcessingData`, `ScrapedBook`, `ScrapedMetadata`, etc.) with ORM-like methods (`.save()`, `.get()`, `.update()`)
- **`libs/db.py`**: Redis abstraction layer - serializes dataclasses to JSON, stores with keys like `chapterprocessingdata:{hash}`
- **`libs/scraper.py`**: Playwright-based scraping connecting to shared browser service at `ws://playwright-browser:3000`
- **`workers/*/tasks.py`**: Celery tasks decorated with `@app.task(bind=True, queue='...')` for retry/error handling
- **`api/main.py`**: FastAPI introspection API for viewing processing state

## Data Flow & Hashing

1. **Book Processing** (`workers/book/tasks.py`): Scrapes chapter list, creates `ChapterProcessingData` for each chapter with MD5 hash from `{title}:{url}`
2. Each chapter transitions through statuses: `PENDING → PROCESSING → COMPLETED`
3. Files are organized as: `static/{format}/{book_slug}/{chapter_slug}.{ext}`

**Hash Strategy**: `chapter_hash = md5(title:url)` ensures idempotent processing - same chapter URL never reprocessed if status is `COMPLETED`.

## Essential Patterns

### Worker Task Chain
Workers **must** call `app.send_task()` to dispatch to next worker, not direct imports:
```python
# ✅ Correct - dispatches to next queue
app.send_task('worker.tasks.process_chapter', 
             args=[chapter_hash], 
             queue='chapter-queue')

# ❌ Wrong - breaks queue routing
from chapter.tasks import process_chapter
process_chapter.delay(chapter_hash)
```

### Error Handling
All tasks use exponential backoff with max 5 retries:
```python
@app.task(bind=True, queue='tts-queue', autoretry_for=(Exception,), 
          retry_kwargs={'max_retries': 5, 'countdown': 60})
def process_tts(self, chapter_hash: str):
    try:
        # ... task logic
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
```

### Redis as ORM
Models inherit save/get methods from dataclass pattern:
```python
chapter = ChapterProcessingData.get(chapter_hash)  # Deserializes from Redis
chapter.status = Status.PROCESSING
chapter.save()  # Serializes back to Redis
```

## Development Workflows

### Running the Stack
```bash
docker compose up --build  # Starts all 10+ services
docker compose watch       # Hot reload for api and libs changes
```

### Monitoring
- **Flower UI**: http://localhost:5555 - Celery task monitoring
- **FastAPI docs**: http://localhost:8000/docs - Introspection API
- **Redis CLI**: `docker exec -it novel-tts-redis redis-cli`

### Triggering Processing
See `main.py` for manual task invocation examples (commented out). Typical flow:
```python
book_input = {
    "book_url": "https://novelbin.com/b/shadow-slave#tab-chapters-title",
    "good_reads_url": "https://www.goodreads.com/book/show/...",
    "short_book_name": "shadow-slave",
    "start_from_url": "https://novelbin.com/b/shadow-slave/chapter-2596",
    "process_until_url": "https://novelbin.com/b/shadow-slave/chapter-2599"
}
```

### Debugging Worker Issues
1. Check container logs: `docker logs -f process-tts-worker`
2. Inspect task state in Flower (http://localhost:5555)
3. Query Redis directly: `redis-cli GET chapterprocessingdata:{hash}`
4. Check FastAPI status endpoints: `/chapters/status/failed`

## Critical Constraints

- **Shared Browser Service**: All workers use `PLAYWRIGHT_BROWSER_URL=ws://playwright-browser:3000` - don't spawn local browsers
- **Shared Volume**: `static_volume:/app/static` must be mounted read-write on all workers for file handoff
- **Metadata Deduplication**: `workers/metadata/tasks.py` uses `ScrapedMetadata.exists(book_hash)` to avoid re-scraping Goodreads for every chapter
- **Sync Deduplication**: `workers/sync/tasks.py` uses Redis locks (`rsync_lock:{book_name}`) to prevent concurrent rsync of same book

## File Locations

- Worker-specific Celery apps: `workers/{worker_type}/celery.py` (imports from `libs.celery`)
- Shared base image Dockerfile: `libs/Dockerfile` (commented out in docker-compose.yml)
- Environment config: `.env.example` (copy to `.env` for SSH credentials)

## Common Modifications

**Adding a new worker type**:
1. Create `workers/new_worker/{tasks.py, celery.py, requirements.txt, Dockerfile}`
2. Add service to `docker-compose.yml` with appropriate queue name
3. Update upstream worker to dispatch with `app.send_task('worker.tasks.process_new_worker', queue='new-queue')`

**Changing scraping logic**: 
- Edit parser functions in `libs/scraper.py` (`content_parser`, `book_chapters_parser`, etc.)
- All scrapers use BeautifulSoup on Playwright-fetched HTML

**Adjusting retry behavior**: 
- Modify `@app.task` decorator parameters in `workers/*/tasks.py`
- Global defaults in `libs/celery.py` (`task_default_retry_delay`, `task_max_retries`)

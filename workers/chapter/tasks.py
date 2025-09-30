import os

from libs.scraper import scrape_chapter_content
from libs.utils import logger
from libs.models import ChapterProcessingData, Status
from .celery import app

# def send_to_tts_queue(chapter_data: ScrapedChapterContent):
#     """Send chapter content to TTS processing queue."""
#     from libs.tasks import tts_process
#     tts_process.apply_async(
#         args=[chapter_data.title, chapter_data.content],
#         queue='tts-queue'
#     )

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 60})
def process_chapter(self, chapter_hash: str):
    try:
        chapter_data = ChapterProcessingData.get(chapter_hash)
        if not chapter_data:
            logger.error(f"ChapterProcessingData not found for hash: {chapter_hash}")
            return
        chapter_data.status = Status.PROCESSING
        chapter_data.save()
        if result := scrape_chapter_content(chapter_data.url):
            result.chapter_hash = chapter_hash
            result.url = chapter_data.url
            result.save()

            app.send_task('worker.tasks.process_tts', 
                     args=[chapter_hash], 
                     queue='tts-queue')

            return True
    except Exception as exc:
        logger.error(f"chapter_content_process failed: {exc}")
        if self.request.retries >= 5:
            # send_to_dead_letter_queue('chapter_content_process', (chapter_url,), {}, str(exc))
            return
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

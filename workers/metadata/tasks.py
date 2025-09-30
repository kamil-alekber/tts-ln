import os
from libs.scraper import scrape_book_metadata
from libs.models import ChapterProcessingData, ScrapedBook, ScrapedMetadata
from libs.utils import logger
import requests
from .celery import app

def download_image(image_url: str, safe_path: str) -> bytes:
    """Download image from URL and return its content."""
    response = requests.get(image_url)
    response.raise_for_status()
    os.makedirs(os.path.dirname(safe_path), exist_ok=True)
    with open(safe_path, 'wb') as f:
        f.write(response.content)
    return True

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 60})
def process_metadata(self, chapter_hash: str):
    print("Processing metadata for chapter:", chapter_hash)

    

    try:
        chapter_data = ChapterProcessingData.get(chapter_hash)
        if chapter_data is None:
            logger.error(f"ChapterProcessingData not found for hash: {chapter_hash}")
            return False

        if ScrapedMetadata.exists(chapter_data.book_hash):
            logger.info(f"Metadata already exists for book hash: {chapter_data.book_hash}")

            app.send_task('worker.tasks.process_chapter', 
                     args=[chapter_hash], 
                     queue='chapter-queue')
            return True

        book = ScrapedBook.get(chapter_data.book_hash)
        if book is None:
            logger.error(f"Book not found for hash: {chapter_data.book_hash}")
            return False

        metadata = scrape_book_metadata(book.metadata_url)
        if result := download_image(metadata.image, chapter_data.cover_image_location) is False:
            logger.error(f"Failed to download image from URL: {metadata.image}")

        metadata.save(chapter_data.book_hash)

        app.send_task('worker.tasks.process_chapter', 
                     args=[chapter_hash], 
                     queue='chapter-queue')

        return True
    except Exception as exc:
        print(f"process_metadata failed: {exc}")
        if self.request.retries >= 5:
            # send_to_dead_letter_queue('process_metadata', (chapter_data_dict,), {}, str(exc))
            return
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

from typing import Dict, List, Tuple
from datetime import datetime

from libs.models import BookChapterLink, ChapterProcessingData, Status
from libs.scraper import scrape_book_chapters
from libs.utils import logger

from .celery import app

def filter_chapters(chapters: list[BookChapterLink], start_from: str, end_at: str) -> list[Tuple[int, BookChapterLink]] | None:
    """Filter chapters based on start_from and end_at URLs."""
    start_index = next((i for i, chapter in enumerate(chapters) if chapter.url == start_from), None)
    if start_index is None:
        print(f"Start URL {start_from} not found in chapters")
        return None

    end_index = next((i for i, chapter in enumerate(chapters) if chapter.url == end_at), None)
    if end_index is None or end_index < start_index:
        print(f"End URL {end_at} not found in chapters or before start.")
        return None

    return [(i, chapters[i]) for i in range(start_index, end_index + 1)]

@app.task(bind=True, queue='book-queue', autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 60})
def process_book(self, input_data: Dict[str, str]) -> bool | List[BookChapterLink]:
    try:
        book_url = input_data.get("book_url", "")
        good_reads_url = input_data.get("good_reads_url", "")
        short_book_name = input_data.get("short_book_name", "")
        start_from_url = input_data.get("start_from_url", "")
        process_until_url = input_data.get("process_until_url", "")
        
        
        book = scrape_book_chapters(book_url, start_from_url, process_until_url)
     
        filtered = filter_chapters(book.chapters, start_from_url, process_until_url)
        
        if filtered is None or len(filtered) == 0:
            logger.error(f"No chapters found between {start_from_url} and {process_until_url}")
            return False
        else:
            chapters_list = [chapter for _, chapter in filtered]
            book.chapters = chapters_list
            book.metadata_url = good_reads_url
            book.save()

        print(f"Chapter to process {len(filtered)}/{len(book.chapters)}")


        chapter = None
        existing_chapter = None
        for chapter_number, scraped_chapter in filtered:
            chapter = ChapterProcessingData(
                book_hash=book.book_hash,
                book_name=short_book_name,
                chapter_number=chapter_number,
                status=Status.PENDING,
                created_at=datetime.utcnow().isoformat(),
                title=scraped_chapter.title,
                url=scraped_chapter.url,
            )
            existing_chapter = ChapterProcessingData.get(chapter.chapter_hash)

            is_completed = existing_chapter is not None and existing_chapter.status == Status.COMPLETED
            if is_completed:
                print(f"Chapter {chapter.title} already processed, skipping.")
                continue
                
            chapter.save()

            app.send_task('worker.tasks.process_metadata', 
                        args=[chapter.chapter_hash], 
                        queue='metadata-queue', 
                        exchange='metadata-queue')

        return book.title
    except Exception as exc:
        logger.error(f"book_chapters_process failed: {exc}")
        # if self.request.retries >= 5:
        #     send_to_dead_letter_queue('book_chapters_process', (book_url, good_reads_url), {}, exc)
        #     return
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

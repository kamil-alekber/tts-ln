from typing import Dict, List, Optional, Tuple
from datetime import datetime

from libs.models import BookChapterLink, ChapterProcessingData, ScrapedBook, ScrapedMetadata, Status
from libs.scraper import scrape_book_chapters
from libs.utils import logger

from .celery import app


def filter_chapters(
    chapters: List[BookChapterLink], 
    start_from: str, 
    end_at: str
) -> Optional[List[Tuple[int, BookChapterLink]]]:
    """
    Filter chapters based on start_from and end_at URLs.
    
    Args:
        chapters: List of all available chapters
        start_from: URL of the starting chapter
        end_at: URL of the ending chapter
        
    Returns:
        List of (chapter_index, chapter) tuples if valid range found, None otherwise
    """
    start_index = _find_chapter_index(chapters, start_from)
    if start_index is None:
        logger.error(f"Start URL {start_from} not found in chapters")
        return None

    end_index = _find_chapter_index(chapters, end_at)
    if end_index is None or end_index < start_index:
        logger.error(f"End URL {end_at} not found in chapters or before start")
        return None

    return [(i, chapters[i]) for i in range(start_index, end_index + 1)]


def _find_chapter_index(chapters: List[BookChapterLink], url: str) -> Optional[int]:
    """Find the index of a chapter by its URL."""
    return next((i for i, chapter in enumerate(chapters) if chapter.url == url), None)


def _extract_input_parameters(input_data: Dict[str, str]) -> Tuple[str, str, str, str, str]:
    """
    Extract and validate input parameters from the input data dictionary.
    
    Returns:
        Tuple of (book_url, good_reads_url, short_book_name, start_from_url, process_until_url)
    """
    return (
        input_data.get("book_url", ""),
        input_data.get("good_reads_url", ""),
        input_data.get("short_book_name", ""),
        input_data.get("start_from_url", ""),
        input_data.get("process_until_url", "")
    )


def _prepare_book_with_filtered_chapters(
    book: ScrapedBook, 
    filtered_chapters: List[Tuple[int, BookChapterLink]], 
    good_reads_url: str
) -> ScrapedBook:
    """
    Update book with filtered chapters and metadata URL, then save to database.
    
    Args:
        book: The scraped book object
        filtered_chapters: List of (chapter_index, chapter) tuples
        good_reads_url: URL to Goodreads metadata
        
    Returns:
        Updated book object
    """
    chapters_list = [chapter for _, chapter in filtered_chapters]
    book.chapters = chapters_list
    book.metadata_url = good_reads_url
    book.save()
    return book


def _create_chapter_processing_data(
    book_hash: str,
    short_book_name: str,
    chapter_number: int,
    scraped_chapter: BookChapterLink
) -> ChapterProcessingData:
    """
    Create a ChapterProcessingData object for a scraped chapter.
    
    Args:
        book_hash: Hash identifier for the book
        short_book_name: Short name/slug for the book
        chapter_number: Sequential chapter number
        scraped_chapter: The scraped chapter data
        
    Returns:
        ChapterProcessingData object
    """
    return ChapterProcessingData(
        book_hash=book_hash,
        book_name=short_book_name,
        chapter_number=chapter_number,
        status=Status.PENDING,
        created_at=datetime.utcnow().isoformat(),
        title=scraped_chapter.title,
        url=scraped_chapter.url,
    )


def _is_chapter_already_completed(chapter_hash: str) -> bool:
    """
    Check if a chapter has already been processed to completion.
    
    Args:
        chapter_hash: Hash identifier for the chapter
        
    Returns:
        True if chapter exists and is completed, False otherwise
    """
    existing_chapter = ChapterProcessingData.get(chapter_hash)
    return existing_chapter is not None and existing_chapter.status == Status.COMPLETED


def _dispatch_chapter_to_next_worker(chapter: ChapterProcessingData, book_hash: str) -> None:
    """
    Dispatch chapter to the appropriate next worker in the pipeline.
    
    If metadata exists for the book, sends directly to chapter worker.
    Otherwise, sends to metadata worker first.
    
    Args:
        chapter: The chapter processing data
        book_hash: Hash identifier for the book
    """
    if ScrapedMetadata.exists(book_hash):
        logger.info(
            f"Metadata exists for book {book_hash}, "
            f"sending chapter '{chapter.title}' directly to chapter worker"
        )
        app.send_task(
            'worker.tasks.process_chapter',
            args=[chapter.chapter_hash],
            queue='chapter-queue',
            exchange='chapter-queue'
        )
    else:
        logger.info(
            f"Metadata not found for book {book_hash}, "
            f"sending chapter '{chapter.title}' to metadata worker"
        )
        app.send_task(
            'worker.tasks.process_metadata',
            args=[chapter.chapter_hash],
            queue='metadata-queue',
            exchange='metadata-queue'
        )


def _process_filtered_chapters(
    filtered_chapters: List[Tuple[int, BookChapterLink]],
    book_hash: str,
    short_book_name: str
) -> None:
    """
    Process each filtered chapter: create processing data and dispatch to workers.
    
    Args:
        filtered_chapters: List of (chapter_index, chapter) tuples to process
        book_hash: Hash identifier for the book
        short_book_name: Short name/slug for the book
    """
    for chapter_number, scraped_chapter in filtered_chapters:
        chapter = _create_chapter_processing_data(
            book_hash=book_hash,
            short_book_name=short_book_name,
            chapter_number=chapter_number,
            scraped_chapter=scraped_chapter
        )
        
        if _is_chapter_already_completed(chapter.chapter_hash):
            logger.info(f"Chapter '{chapter.title}' already processed, skipping")
            continue
        
        chapter.save()
        _dispatch_chapter_to_next_worker(chapter, book_hash)


@app.task(
    bind=True,
    queue='book-queue',
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 5, 'countdown': 60}
)
def process_book(self, input_data: Dict[str, str]) -> str:
    """
    Process a book: scrape chapters, filter range, and dispatch to workers.
    
    This is the entry point for the book processing pipeline. It:
    1. Scrapes the book's chapter list from the source URL
    2. Filters chapters to the specified range
    3. Saves book metadata to Redis
    4. Creates ChapterProcessingData for each chapter
    5. Dispatches chapters to metadata or chapter workers
    
    Args:
        input_data: Dictionary containing:
            - book_url: Source URL for the book
            - good_reads_url: Goodreads URL for metadata
            - short_book_name: Short name/slug for the book
            - start_from_url: URL of first chapter to process
            - process_until_url: URL of last chapter to process
            
    Returns:
        Book title if successful
        
    Raises:
        Retries on any exception up to 5 times with exponential backoff
    """
    try:
        # Extract input parameters
        (book_url, good_reads_url, short_book_name, 
         start_from_url, process_until_url) = _extract_input_parameters(input_data)
        
        # Scrape book chapters from source
        book = scrape_book_chapters(book_url, start_from_url, process_until_url)
        
        # Filter chapters to specified range
        filtered_chapters = filter_chapters(book.chapters, start_from_url, process_until_url)
        
        if not filtered_chapters:
            logger.error(
                f"No chapters found between {start_from_url} and {process_until_url}"
            )
            return ""
        
        # Save book with filtered chapters
        book = _prepare_book_with_filtered_chapters(book, filtered_chapters, good_reads_url)
        
        logger.info(
            f"Processing {len(filtered_chapters)} chapters out of "
            f"{len(book.chapters)} total for book '{book.title}'"
        )
        
        # Process each chapter and dispatch to workers
        _process_filtered_chapters(filtered_chapters, book.book_hash, short_book_name)
        
        return book.title
        
    except Exception as exc:
        logger.error(f"Book processing failed: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

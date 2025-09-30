
book_url = "https://novelbin.com/b/trapped-in-another-world-with-no-magic#tab-chapters-title"
# chapter_url = "https://novelbin.com/b/trapped-in-another-world-with-no-magic/chapter-160-prodding-the-devil-of-the-wood"
# good_reads = "https://www.goodreads.com/book/show/236399954-trapped-in-another-world-with-no-magic-volume-1"
# scrape_book_chapters(
#     "https://novelbin.com/b/trapped-in-another-world-with-no-magic#tab-chapters-title",
#     "https://novelbin.com/b/trapped-in-another-world-with-no-magic/chapter-160-prodding-the-devil-of-the-wood",
#     "https://novelbin.com/b/trapped-in-another-world-with-no-magic/chapter-190-another-step-towards-peace"
# )

import os
from book import worker as book_worker
from chapter import worker as chapter_worker
from tts import worker as tts_worker
from metadata import worker as metadata_worker
from converter import worker as converter_worker
from completed import worker as completed_worker
from rsync import worker as rsync_worker
from libs.models import ScrapedChapterContent

if __name__ == "__main__":
    # 1. Process Book worker
    # book_input = {
    #     "book_url": "https://novelbin.com/b/trapped-in-another-world-with-no-magic#tab-chapters-title",
    #     "good_reads_url": "",
    #     "short_book_name": "trapped-in-another-world-with-no-magic",
    #     "start_from_url": "https://novelbin.com/b/trapped-in-another-world-with-no-magic/chapter-160-prodding-the-devil-of-the-wood",
    #     "process_until_url": "https://novelbin.com/b/trapped-in-another-world-with-no-magic/chapter-162-solo-scouting"
    # }

    # book_input = {
    #     "book_url": "https://novelbin.com/b/shadow-slave#tab-chapters-title",
    #     "good_reads_url": "https://www.goodreads.com/book/show/61859147-shadow-slave",
    #     "short_book_name": "shadow-slave",
    #     "start_from_url": "https://novelbin.com/b/shadow-slave/chapter-2596-weight-of-fate",
    #     "process_until_url":"https://novelbin.com/b/shadow-slave/chapter-2599-the-flaw-in-our-stars" 
    # }
    # book_result = book_worker.process_book(book_input)
    
    # 2. Process Metadata
    # chapter_hash = "b356f4f6cc0cb31d76302eb4bd4aa2fd"
    # metadata_result = metadata_worker.process_metadata(chapter_hash)

    # 3. Process Chapter worker
    # chapter_hash = "b356f4f6cc0cb31d76302eb4bd4aa2fd"
    # chapter_worker.process_chapter(chapter_hash)

    # 4. Process TTS worker
    # chapter_hash = "b356f4f6cc0cb31d76302eb4bd4aa2fd"
    # tts_worker.create_text_audio(chapter_hash)
    
    # 5. Process Converter worker and inject metadata
    # converter_result = converter_worker.process_conversion(chapter_hash)

    # 6. Process Completed worker
    # chapter_hash = "b356f4f6cc0cb31d76302eb4bd4aa2fd"
    # completed_result = completed_worker.process_completed(chapter_hash)

    # 7. Process Rsync worker
    # chapter_hash = "b356f4f6cc0cb31d76302eb4bd4aa2fd"
    # rsync_result = rsync_worker.process_sync(chapter_hash)
import os

from libs.utils import logger
from .tts import generate_tts
from libs.models import ChapterProcessingData, ScrapedChapterContent
from .celery import app

@app.task(bind=True, queue='tts-queue', autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 60})
def process_tts(self, chapter_hash: str) -> bool:
    try:
        chapter = ChapterProcessingData.get(chapter_hash)
        if chapter is None:
            logger.error(f"ChapterProcessingData not found for hash: {chapter_hash}")
            return False

        scraped_content = ScrapedChapterContent.get(chapter_hash)
        if scraped_content is None:
            logger.error(f"ScrapedChapterContent not found for hash: {chapter_hash}")
            return False
        
        print(f"Generating TTS for chapter: {chapter_hash}")

        os.makedirs(os.path.dirname(chapter.wav_file_location), exist_ok=True)
        generate_tts(scraped_content.content, chapter.wav_file_location)

        app.send_task('worker.tasks.process_converter', 
                     args=[chapter_hash], 
                     queue='converter-queue')

        return True
    except Exception as exc:
        logger.error(f"create_text_audio failed: {exc}")
        if self.request.retries >= 5:
            # send_to_dead_letter_queue('create_text_audio', (chapter_data_dict,), {}, str(exc))
            return
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    except:
        print("Unexpected error:", sys.exc_info()[0])
        return False

# create_text_audio("/Users/kalekber/code/node-tts/v2/tts/input.txt")

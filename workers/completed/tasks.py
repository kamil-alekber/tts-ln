from libs.utils import logger
from libs.models import ChapterProcessingData, Status
from .celery import app

@app.task(bind=True, queue='completed-queue', autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 60})
def process_completed(self, chapter_hash: str) -> bool:
    try:
        chapter_data = ChapterProcessingData.get(chapter_hash)
        if not chapter_data:
            raise ValueError(f"Chapter with hash {chapter_hash} not found")

        print(f"Chapter ready: {chapter_data.book_name} - {chapter_data.title}")
        chapter_data.status = Status.COMPLETED
        chapter_data.save()
    
            # Trigger sync task after a delay to ensure all processing is done
        app.send_task('worker.tasks.process_sync', 
                     args=[chapter_hash], 
                     queue='sync-queue',
                     countdown=300) 
        
        return True
    
    except Exception as exc:
        logger.error(f"ready_chapter failed: {exc}")
        if self.request.retries >= 5:
            # send_to_dead_letter_queue('ready_chapter', (chapter_data_dict,), {}, str(exc))
            return
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

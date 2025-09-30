from celery import Celery
import os
from kombu import Exchange, Queue

redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

app = Celery('worker',
            broker=redis_url,
            backend=redis_url,
            include=['worker.tasks'],
             )

# app.conf.task_queues = (
#     Queue('default', Exchange('default'), routing_key='default'),
#     Queue('book-queue', Exchange('book-queue'), routing_key='book-queue'),
#     Queue('chapter-queue', Exchange('chapter-queue'), routing_key='chapter-queue'),
#     Queue('completed-queue', Exchange('completed-queue'), routing_key='completed-queue'),
#     Queue('converter-queue', Exchange('converter-queue'), routing_key='converter-queue'),
#     Queue('metadata-queue', Exchange('metadata-queue'), routing_key='metadata-queue'),
#     Queue('sync-queue', Exchange('sync-queue'), routing_key='sync-queue'),
#     Queue('tts-queue', Exchange('tts-queue'), routing_key='tts-queue'),
# )

# app.conf.task_routes = {
#     'process_book': {'queue': 'book-queue', 'exchange': 'book-queue'},
#     'process_chapter': {'queue': 'chapter-queue', 'exchange': 'chapter-queue'},
#     'process_completed': {'queue': 'completed-queue', 'exchange': 'completed-queue'},
#     'process_converter': {'queue': 'converter-queue', 'exchange': 'converter-queue'},
#     'process_metadata': {'queue': 'metadata-queue', 'exchange': 'metadata-queue'},
#     'process_sync': {'queue': 'sync-queue', 'exchange': 'sync-queue'},
#     'process_tts': {'queue': 'tts-queue', 'exchange': 'tts-queue'},
# }


app.conf.update(
    result_expires=3600,
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    # Retry configuration
    task_acks_late=True,
    worker_prefetch_multiplier=1,  # Process one task at a time to handle retries better
    task_reject_on_worker_lost=True,
    # Default retry settings for all tasks
    task_default_retry_delay=60,  # 60 seconds base delay
    task_max_retries=5,
    # Exponential backoff settings
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # Max 10 minutes
    task_retry_jitter=True,  # Add randomness to prevent thundering herd
)

if __name__ == '__main__':
    app.start()

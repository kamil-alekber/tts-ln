import os
import subprocess

from libs.utils import logger
from libs.db import db
from libs.models import ChapterProcessingData
from .celery import app

RSYNC_PENDING_KEY = 'rsync_pending_books'

@app.task(bind=True, autoretry_for=(Exception,), retry_kwargs={'max_retries': 3, 'countdown': 300})
def process_sync(self, chapter_hash: str):
    """
    Rsync book files to remote server with deduplication based on book name.
    Only one rsync task per book will be executed within a 5-minute window.
    """
    chapter = ChapterProcessingData.get(chapter_hash)
    if chapter is None:
        logger.error(f"ChapterProcessingData not found for hash: {chapter_hash}")
        return False

    try:

        # Check if rsync for this book is already pending or in progress
        lock_key = f"rsync_lock:{chapter.book_name}"
        
        # Try to acquire a lock for this book (expires in 10 minutes)
        lock_acquired = db.redis_client.set(lock_key, "1", ex=600, nx=True)

        if not lock_acquired:
            logger.info(f"Rsync for book '{chapter.book_name}' is already in progress, skipping duplicate request")
            return {"status": "skipped", "reason": "duplicate_request", "book": chapter.book_name}

        try:
            # Add book to pending set
            db.redis_client.sadd(RSYNC_PENDING_KEY, chapter.book_name)

            # Construct the rsync command
            destination = os.getenv('RSYNC_DESTINATION', 'root@192.168.8.184:/srv/samba/k8s-share/media/books/')
            ssh_key = os.getenv('SSH_KEY_PATH', '/app/.ssh/id_rsa')
            rsync_command = [
                "rsync",
                "-avz",
                "--progress", 
                "--update",
                "-e", f"ssh -i {ssh_key} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null",
                chapter.static_base_path,
                destination
            ]

            logger.info(f"Starting rsync for book: {chapter.book_name}")
            logger.info(f"Command: {' '.join(rsync_command)}")
            
            # Execute rsync command
            result = subprocess.run(
                rsync_command,
                capture_output=True,
                text=True,
                # cwd="/app",  # Set working directory
                timeout=1800  # 30 minute timeout
            )
            
            if result.returncode == 0:
                logger.info(f"Rsync completed successfully for book: {chapter.book_name}")
                logger.info(f"Rsync output: {result.stdout}")
                
                # Remove from pending set on success
                db.redis_client.srem(RSYNC_PENDING_KEY, chapter.book_name)

                return {
                    "status": "success",
                    "book": chapter.book_name,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
            else:
                error_msg = f"Rsync failed with return code {result.returncode}: {result.stderr}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        finally:
            # Always release the lock
            db.redis_client.delete(lock_key)
            
    except subprocess.TimeoutExpired:
        error_msg = f"Rsync timeout for book: {chapter.book_name}"
        logger.error(error_msg)
        db.redis_client.srem(RSYNC_PENDING_KEY, chapter.book_name)
        if self.request.retries >= 3:
            # send_to_dead_letter_queue('rsync_book_files', (chapter.book_name,), {}, error_msg)
            return
        raise self.retry(exc=Exception(error_msg), countdown=300)
        
    except Exception as exc:
        logger.error(f"rsync_book_files failed for book '{chapter.book_name}': {exc}")
        db.redis_client.srem(RSYNC_PENDING_KEY, chapter.book_name)
        if self.request.retries >= 3:
            # send_to_dead_letter_queue('rsync_book_files', (chapter.book_name,), {}, str(exc))
            return
        raise self.retry(exc=exc, countdown=300 * (2 ** self.request.retries))

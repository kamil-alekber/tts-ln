FROM tts-base

WORKDIR /app

RUN apt-get update && apt-get install -y sshpass

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY *.py worker/

CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--queues=sync-queue", "--concurrency=1", "-n", "sync_worker@%n"]

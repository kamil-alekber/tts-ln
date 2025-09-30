FROM kalekber/tts-base:0.0.1

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY *.py worker/

CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--queues=completed-queue", "--concurrency=1",  "-n", "completed_worker@%n"]

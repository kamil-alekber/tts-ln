ARG VERSION=latest
FROM kalekber/tts-base:${VERSION}

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY *.py worker/

CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--queues=tts-queue", "--concurrency=2", "-n", "tts_worker@%n"]

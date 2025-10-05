ARG VERSION=latest
FROM kalekber/tts-base:${VERSION}

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY *.py worker/

CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--queues=book-queue", "--concurrency=2", "-n", "book_worker@%n"]

ARG VERSION=latest
FROM kalekber/tts-base:${VERSION}

WORKDIR /app

# Copy worker-specific files
COPY requirements.txt .

# Install requirements
RUN pip install -r requirements.txt

COPY *.py worker/

CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--queues=metadata-queue", "--concurrency=3", "-n", "metadata_worker@%n"]

ARG VERSION=latest
FROM kalekber/tts-base:${VERSION}

WORKDIR /app

# Copy worker-specific files
COPY requirements.txt .

# Install requirements
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py worker/
# Run the worker
CMD ["celery", "-A", "worker", "worker", "--loglevel=info", "--queues=converter-queue", "--concurrency=3", "-n", "converter_worker@%n"]

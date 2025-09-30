FROM python:3.12-slim

# Install system dependencies that might be needed by workers
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libavcodec-extra \
    rsync \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY celery.py worker/

COPY *.py libs/

# # Set Python path to include libs
# ENV PYTHONPATH=/app:/app/libs

# Create SSH directory for sync worker
RUN mkdir -p /app/.ssh && chmod 700 /app/.ssh

CMD ["echo", "Base TTS image - should be overridden by workers"]

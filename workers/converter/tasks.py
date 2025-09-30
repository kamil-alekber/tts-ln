import os
from typing import Dict
from pydub import AudioSegment

import srt
import datetime

from libs.utils import logger
from libs.models import ChapterProcessingData, ScrapedChapterContent, ScrapedMetadata
from .celery import app

def create_subtitles(content: str, audio_length_ms: int, subtitle_path: str):
    """
    Create a simple SRT subtitles file from the content.
    Each sentence is a subtitle, spaced evenly over the audio duration.
    """
    sentences = [s.strip() for s in content.split('.') if s.strip()]
    num_sentences = len(sentences)
    if num_sentences == 0:
        return False
    duration_per_sentence = audio_length_ms // num_sentences
    subs = []
    for i, sentence in enumerate(sentences):
        start = datetime.timedelta(milliseconds=i * duration_per_sentence)
        end = datetime.timedelta(milliseconds=(i + 1) * duration_per_sentence)
        subs.append(srt.Subtitle(index=i+1, start=start, end=end, content=sentence))
    srt_content = srt.compose(subs)
    with open(subtitle_path, 'w', encoding='utf-8') as f:
        f.write(srt_content)
    return True

def build_tags(chapter: ChapterProcessingData, metadata: ScrapedMetadata) -> Dict[str, str]:
    """Return a dictionary of audio tags."""
    return {
        "album": chapter.book_name or "empty",
        "artist": metadata.artist or "empty",
        "album_artist": metadata.album_artist or "empty",
        "comment": metadata.comment or "empty",
        "composer": metadata.composer or "empty",
        "copyright": metadata.copyright or "empty",
        "genre": metadata.genre or "audiobook",
        "compilation": "1",
        "title": chapter.title or "empty",
        "track": chapter.chapter_number or "empty",
        "date": metadata.released_year or "empty"
    }

def build_cover_parameters() -> list:
    """Return ffmpeg parameters for cover image attachment."""
    return [
        "-map", "0:a",
        "-map", "1:v",
        "-c:a", "mp3",
        "-c:v", "mjpeg",
        "-disposition:v:0", "attached_pic"
    ]

def build_subtitle_parameters(subtitle_path: str) -> (list, list):
    """Return ffmpeg parameters for subtitle attachment if subtitle exists."""
    if os.path.exists(subtitle_path):
        return ["-i", subtitle_path], ["-map", "2:s", "-c:s", "mov_text"]
    return [], []

@app.task(bind=True, queue='converter-queue',  autoretry_for=(Exception,), retry_kwargs={'max_retries': 5, 'countdown': 60})
def process_converter(self, chapter_hash: str):
    """
    Convert WAV audio to MP4 with cover image and optional subtitles.
    """
    try:
        processing_data = ChapterProcessingData.get(chapter_hash)
        if processing_data is None:
            logger.error(f"ChapterProcessingData not found for hash: {chapter_hash}")
            return False

        scraped_content = ScrapedChapterContent.get(chapter_hash)
        if scraped_content is None:
            logger.error(f"ScrapedChapterContent not found for hash: {chapter_hash}")
            return False
        
        metadata = ScrapedMetadata.get(processing_data.book_hash)
        if metadata is None:
            logger.error(f"ScrapedMetadata not found for book hash: {processing_data.book_hash}")
            return False

        ensure_path = [processing_data.wav_file_location,
         processing_data.mp3_file_location,
         processing_data.mp4_file_location,
         processing_data.subtitle_file_location]

        for path in ensure_path:
            os.makedirs(os.path.dirname(path), exist_ok=True)

        audio = AudioSegment.from_wav(processing_data.wav_file_location)
        create_subtitles(scraped_content.content, len(audio), processing_data.subtitle_file_location)

        tags = build_tags(processing_data, metadata)
        cover_parameters = build_cover_parameters()
        subtitle_parameters, subtitle_map_codec = build_subtitle_parameters(processing_data.subtitle_file_location)

        print(f"Converting {processing_data.wav_file_location} to {processing_data.mp4_file_location} (MP4 with subtitles)")
        audio.export(
            processing_data.mp4_file_location,
            format="mp4",
            parameters=[
                "-i", processing_data.cover_image_location,
                *subtitle_parameters,
                *cover_parameters,
                *subtitle_map_codec,
                "-b:a", "320k"
            ],
            tags=tags
        )

        print(f"Converting {processing_data.wav_file_location} to {processing_data.mp3_file_location} (MP3 with image only)")
        audio.export(
            processing_data.mp3_file_location,
            format="mp3",
            parameters=[
                "-i", processing_data.cover_image_location,
                *cover_parameters,
                "-b:a", "320k"
            ],
            tags=tags
        )

        app.send_task('worker.tasks.process_completed', 
                     args=[chapter_hash], 
                     queue='completed-queue')
        return True
    except Exception as exc:
        logger.error(f"convert_audio failed: {exc}")
        if self.request.retries >= 5:
            return
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
        

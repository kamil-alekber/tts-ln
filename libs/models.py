import os
import hashlib
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Optional, List
from datetime import datetime

from .db import db

# Processing Entities
class Status(Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ChapterProcessingData:
    """Data required for processing a chapter."""
    chapter_hash: str
    chapter_number: int
    book_hash: str
    status: Status
    created_at: str
    title: str
    url: str
    book_name: str 

    # File related paths
    static_base_path: str
    cover_image_location: str
    text_file_location: str
    subtitle_file_location: str
    wav_file_location: str
    mp3_file_location: str
    mp4_file_location: str

    def __init__(self, book_hash: str, status: Status,
                created_at: str, title: str, url: str,
                book_name: str, chapter_hash: str = None,
                chapter_number: int = None,
                text_file_location: str = None,
                subtitle_file_location: str = None,
                wav_file_location: str = None,
                mp3_file_location: str = None,
                mp4_file_location: str = None,
                static_base_path: str = None,
                cover_image_location: str = None
                ):
        self.book_hash = book_hash
        self.created_at = created_at
        self.title = title
        self.url = url
        self.book_name = book_name
        self.status = status if isinstance(status, Status) else Status(status)
        self.chapter_number = chapter_number

        self.static_base_path = static_base_path or os.getcwd() + '/static' 
        file_name = f"{self.name_to_slug(book_name)}/{self.name_to_slug(title)}"
        self.wav_file_location = wav_file_location or f"{self.static_base_path}/wav/{file_name}.wav"
        self.mp3_file_location = mp3_file_location or f"{self.static_base_path}/mp3/{file_name}.mp3"
        self.subtitle_file_location = subtitle_file_location or f"{self.static_base_path}/mp3/{file_name}.srt"
        self.mp4_file_location = mp4_file_location or f"{self.static_base_path}/mp4/{file_name}.mp4"
        self.text_file_location = text_file_location or f"{self.static_base_path}/txt/{file_name}.txt"
        self.cover_image_location = f"{self.static_base_path}/cover/{self.name_to_slug(book_name)}.jpg"
        self.chapter_hash = chapter_hash or self.generate_hash()
    # convert chapter name to slug
    def name_to_slug(self, name: str) -> str:
        """Convert chapter name to a URL-friendly slug."""
        return name.replace(" ", "_").lower()

    def generate_hash(self) -> str:
        """Generate a unique hash for this chapter processing data."""
        data_str = f"{self.title}:{self.url}"
        return hashlib.md5(data_str.encode()).hexdigest()

    def save_book_chapter(self) -> bool:
        db.redis_client.sadd(f"book:{self.book_hash}:chapters", self.chapter_hash)
        return True

    def save(self) -> bool:
        """Save this chapter data to Redis."""
        db.save(self, self.chapter_hash)
        self.save_book_chapter()
        return True
    
    def update(self) -> bool:
        """Update this chapter data in Redis."""
        
        return db.update(self, self.chapter_hash)
    
    def delete(self) -> bool:
        """Delete this chapter data from Redis."""
        
        return db.delete(self.__class__, self.chapter_hash)
    
    @classmethod
    def get(cls, chapter_hash: str) -> Optional['ChapterProcessingData']:
        """Get chapter data by hash from Redis."""
        
        return db.get(cls, chapter_hash)
    
    @classmethod
    def list_all(cls) -> List['ChapterProcessingData']:
        """List all chapter data from Redis."""
        
        return db.list_all(cls)
    
    @classmethod
    def list_by_book_hash(cls, book_hash: str) -> List['ChapterProcessingData']:
        """List all chapters for a specific book."""
        
        return db.list_by_field(cls, 'book_hash', book_hash)
    
    @classmethod
    def list_by_status(cls, status: Status) -> List['ChapterProcessingData']:
        """List all chapters with a specific status."""
        return db.list_by_field(cls, 'status', status)
    
    @classmethod
    def exists(cls, chapter_hash: str) -> bool:
        """Check if chapter data exists in Redis."""
        
        return db.exists(cls, chapter_hash)
    
    @classmethod
    def count(cls) -> int:
        """Count total chapter entries."""
        
        return db.count(cls) 

@dataclass
class BookProcessingData:
    """Data required for processing a book."""
    book_title: str
    book_hash: str
    
    def save(self) -> bool:
        """Save this book data to Redis."""
        
        return db.save(self, self.book_hash)
    
    def update(self) -> bool:
        """Update this book data in Redis."""
        
        return db.update(self, self.book_hash)
    
    def delete(self) -> bool:
        """Delete this book data from Redis."""
        
        return db.delete(self.__class__, self.book_hash)
    
    @classmethod
    def get(cls, book_hash: str) -> Optional['BookProcessingData']:
        """Get book data by hash from Redis."""
        
        return db.get(cls, book_hash)
    
    @classmethod
    def list_all(cls) -> List['BookProcessingData']:
        """List all book data from Redis."""
        
        return db.list_all(cls)
    
    @classmethod
    def exists(cls, book_hash: str) -> bool:
        """Check if book data exists in Redis."""
        
        return db.exists(cls, book_hash)
    
    @classmethod
    def count(cls) -> int:
        """Count total book entries."""
        
        return db.count(cls)
# End of Processing Entities

# Scraped Entities
@dataclass
class ScrapedChapterContent:
    """Represents a single scraped chapter with title and content."""
    title: str
    content: str
    url: str
    chapter_hash: str

    def __init__(self, title: str, content: str, chapter_hash: str = None, url: str = None):
        self.title = title
        self.content = content
        self.url = url
        self.chapter_hash = chapter_hash

    def save(self) -> bool:
        """Save this chapter content to Redis."""
        return db.save(self, self.chapter_hash)

    def update(self, identifier: str) -> bool:
        """Update this chapter content in Redis."""
        
        return db.update(self, identifier)
    
    def delete(self, identifier: str) -> bool:
        """Delete this chapter content from Redis."""
        
        return db.delete(self.__class__, identifier)
    
    @classmethod
    def get(cls, identifier: str) -> Optional['ScrapedChapterContent']:
        """Get chapter content by identifier from Redis."""
        return db.get(cls, identifier)
    
    # get_all_by_book_hash scan and yiled value one by one
    # @classmethod
    # def get_all_by_book_hash(cls, book_hash: str) -> List['ScrapedChapterContent']:
    #     """Get all chapter content for a specific book."""
    #     book_hash_prefix = f"scrapedchaptercontent:{book_hash}:"
    #     return db.list_by_prefix(cls, book_hash_prefix)
    @classmethod
    def list_all(cls) -> List['ScrapedChapterContent']:
        """List all chapter content from Redis."""
        
        return db.list_all(cls)
    
    @classmethod
    def exists(cls, identifier: str) -> bool:
        """Check if chapter content exists in Redis."""
        
        return db.exists(cls, identifier)
    
    @classmethod
    def count(cls) -> int:
        """Count total chapter content entries."""
        
        return db.count(cls)

@dataclass
class BookChapterLink:
    """Represents a single scraped book chapter with title and URL."""
    title: str
    url: str

@dataclass
class ScrapedBook:
    """Represents a single scraped book with title and chapters."""
    title: str
    chapters: list[BookChapterLink]
    metadata_url: str = None
    book_hash: str = None

    def __init__(self, title: str, chapters: list[BookChapterLink], book_hash: str = None, metadata_url: str = None):
        self.title = title
        self.chapters = chapters
        self.metadata_url = metadata_url
        self.book_hash = book_hash or self.generate_hash()

    def generate_hash(self) -> str:
        """Generate a unique hash for this book."""
        return hashlib.md5(self.title.encode()).hexdigest()
    
    def save(self) -> bool:
        """Save this book to Redis."""
        return db.save(self, self.book_hash)

    @classmethod
    def put_book_chapter(cls, book_hash: str, chapter_hash: str) -> None:
        """Add a chapter hash to the book's chapter list."""
        list_key = f"scrapedbook:{book_hash}:chapters"
        db.redis_client.sadd(list_key, chapter_hash)
        
        return True

    def update(self, identifier: str) -> bool:
        """Update this book in Redis."""
        
        return db.update(self, identifier)
    
    def delete(self, identifier: str) -> bool:
        """Delete this book from Redis."""
        
        return db.delete(self.__class__, identifier)
    
    @classmethod
    def get(cls, identifier: str) -> Optional['ScrapedBook']:
        """Get book by identifier from Redis."""
        
        return db.get(cls, identifier)
    
    @classmethod
    def list_all(cls) -> List['ScrapedBook']:
        """List all books from Redis."""
        
        return db.list_all(cls)
    
    @classmethod
    def list_by_title(cls, title: str) -> List['ScrapedBook']:
        """List all books with a specific title."""
        
        return db.list_by_field(cls, 'title', title)
    
    @classmethod
    def exists(cls, identifier: str) -> bool:
        """Check if book exists in Redis."""
        
        return db.exists(cls, identifier)
    
    @classmethod
    def count(cls) -> int:
        """Count total book entries."""
        
        return db.count(cls)

@dataclass
class ScrapedMetadata:
    """Represents metadata for a book."""
    album: str = None
    artist: str = None
    album_artist: str = None
    comment: str = None
    composer: str = None
    copyright: str = None
    genre: str = None
    compilation: str = None
    title: str = None
    track: str = None
    released_year: str = None
    image: str = None
    description: str = None
    created_at: str = None

    def save(self, book_hash: str) -> bool:
        """Save this metadata to Redis."""

        return db.save(self, book_hash)

    def update(self) -> bool:
        """Update this metadata in Redis."""

        return db.update(self, self.book_hash)
    
    def delete(self) -> bool:
        """Delete this metadata from Redis."""

        return db.delete(self.__class__, self.book_hash)
    
    @classmethod
    def get(cls, book_hash: str) -> Optional['ScrapedMetadata']:
        """Get metadata by hash from Redis."""

        return db.get(cls, book_hash)

    @classmethod
    def list_all(cls) -> List['ScrapedMetadata']:
        """List all metadata from Redis."""
        
        return db.list_all(cls)
    
    @classmethod
    def list_by_book_hash(cls, book_hash: str) -> List['ScrapedMetadata']:
        """List all metadata for a specific book."""
        
        return db.list_by_field(cls, 'book_hash', book_hash)
    
    @classmethod
    def exists(cls, metadata_hash: str) -> bool:
        """Check if metadata exists in Redis."""
        
        return db.exists(cls, metadata_hash)
    
    @classmethod
    def count(cls) -> int:
        """Count total metadata entries."""
        
        return db.count(cls)
# End of Scraped Entities

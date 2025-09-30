#!/usr/bin/env python3
"""
Test script for CRUD operations with Redis database.
This script demonstrates how to use the CRUD methods for all models.
"""
# TODO: rewrite to normal tests
import sys
import os
from datetime import datetime

from libs.models import (
    Status, 
    MetadataProcessingData, 
    ChapterProcessingData, 
    BookProcessingData,
    ScrapedChapterContent,
    BookChapterLink,
    ScrapedBook
)

def test_metadata_processing_data():
    """Test CRUD operations for MetadataProcessingData."""
    print("Testing MetadataProcessingData CRUD operations...")
    
    # Create test data
    metadata = MetadataProcessingData(
        metadata_hash="meta_123",
        book_hash="book_456",
        title="Test Book Title",
        artist="Test Artist",
        image="test_image.jpg",
        description="A test book description",
        genre="Fiction",
        date="2023-01-01",
        created_at=datetime.now().isoformat()
    )
    
    # Test save
    assert metadata.save(), "Failed to save metadata"
    print("✓ Save operation successful")
    
    # Test get
    retrieved_metadata = MetadataProcessingData.get("meta_123")
    assert retrieved_metadata is not None, "Failed to retrieve metadata"
    assert retrieved_metadata.title == "Test Book Title", "Retrieved data doesn't match"
    print("✓ Get operation successful")
    
    # Test update
    metadata.title = "Updated Book Title"
    assert metadata.update(), "Failed to update metadata"
    updated_metadata = MetadataProcessingData.get("meta_123")
    assert updated_metadata.title == "Updated Book Title", "Update didn't work"
    print("✓ Update operation successful")
    
    # Test list operations
    all_metadata = MetadataProcessingData.list_all()
    assert len(all_metadata) >= 1, "List all failed"
    print(f"✓ List all returned {len(all_metadata)} items")
    
    # Test exists
    assert MetadataProcessingData.exists("meta_123"), "Exists check failed"
    print("✓ Exists check successful")
    
    # Test count
    count = MetadataProcessingData.count()
    assert count >= 1, "Count failed"
    print(f"✓ Count returned {count}")
    
    # Test delete
    assert metadata.delete(), "Failed to delete metadata"
    assert not MetadataProcessingData.exists("meta_123"), "Delete didn't work"
    print("✓ Delete operation successful")

def test_chapter_processing_data():
    """Test CRUD operations for ChapterProcessingData."""
    print("\nTesting ChapterProcessingData CRUD operations...")
    
    # Create test data
    chapter = ChapterProcessingData(
        book_hash="book_456",
        chapter_hash="chapter_789",
        status=Status.PENDING,
        created_at=datetime.now().isoformat(),
        chapter_name="Chapter 1",
        text_file_location="/path/to/chapter1.txt",
        wav_file_location="/path/to/chapter1.wav",
        mp3_file_location="/path/to/chapter1.mp3"
    )
    
    # Test save
    assert chapter.save(), "Failed to save chapter"
    print("✓ Save operation successful")
    
    # Test get
    retrieved_chapter = ChapterProcessingData.get("chapter_789")
    assert retrieved_chapter is not None, "Failed to retrieve chapter"
    assert retrieved_chapter.chapter_name == "Chapter 1", "Retrieved data doesn't match"
    print("✓ Get operation successful")
    
    # Test status-based listing
    pending_chapters = ChapterProcessingData.list_by_status(Status.PENDING)
    assert len(pending_chapters) >= 1, "Status filter failed"
    print(f"✓ Status filter returned {len(pending_chapters)} pending chapters")
    
    # Cleanup
    assert chapter.delete(), "Failed to delete chapter"
    print("✓ Delete operation successful")

def test_scraped_book():
    """Test CRUD operations for ScrapedBook."""
    print("\nTesting ScrapedBook CRUD operations...")
    
    # Create test data
    chapters = [
        BookChapterLink(title="Chapter 1", url="http://example.com/ch1"),
        BookChapterLink(title="Chapter 2", url="http://example.com/ch2")
    ]
    
    book = ScrapedBook(
        title="Test Novel",
        chapters=chapters
    )
    
    # Test save with auto-generated hash
    book_hash = book.generate_hash()
    assert book.save(), "Failed to save book"
    print("✓ Save operation successful")
    
    # Test get
    retrieved_book = ScrapedBook.get(book_hash)
    assert retrieved_book is not None, "Failed to retrieve book"
    assert retrieved_book.title == "Test Novel", "Retrieved data doesn't match"
    assert len(retrieved_book.chapters) == 2, "Chapter count doesn't match"
    print("✓ Get operation successful")
    
    # Test list by title
    books_by_title = ScrapedBook.list_by_title("Test Novel")
    assert len(books_by_title) >= 1, "Title filter failed"
    print(f"✓ Title filter returned {len(books_by_title)} books")
    
    # Cleanup
    assert book.delete(book_hash), "Failed to delete book"
    print("✓ Delete operation successful")

def test_book_processing_data():
    """Test CRUD operations for BookProcessingData."""
    print("\nTesting BookProcessingData CRUD operations...")
    
    # Create test data
    book = BookProcessingData(
        book_title="Test Processing Book",
        book_hash="book_proc_123"
    )
    
    # Test save
    assert book.save(), "Failed to save book processing data"
    print("✓ Save operation successful")
    
    # Test get
    retrieved_book = BookProcessingData.get("book_proc_123")
    assert retrieved_book is not None, "Failed to retrieve book processing data"
    assert retrieved_book.book_title == "Test Processing Book", "Retrieved data doesn't match"
    print("✓ Get operation successful")
    
    # Test update
    book.book_title = "Updated Processing Book"
    assert book.update(), "Failed to update book processing data"
    updated_book = BookProcessingData.get("book_proc_123")
    assert updated_book.book_title == "Updated Processing Book", "Update didn't work"
    print("✓ Update operation successful")
    
    # Test list operations
    all_books = BookProcessingData.list_all()
    assert len(all_books) >= 1, "List all failed"
    print(f"✓ List all returned {len(all_books)} items")
    
    # Test exists
    assert BookProcessingData.exists("book_proc_123"), "Exists check failed"
    print("✓ Exists check successful")
    
    # Test count
    count = BookProcessingData.count()
    assert count >= 1, "Count failed"
    print(f"✓ Count returned {count}")
    
    # Test delete
    assert book.delete(), "Failed to delete book processing data"
    assert not BookProcessingData.exists("book_proc_123"), "Delete didn't work"
    print("✓ Delete operation successful")

def test_scraped_chapter_content():
    """Test CRUD operations for ScrapedChapterContent."""
    print("\nTesting ScrapedChapterContent CRUD operations...")
    
    # Create test data
    chapter_content = ScrapedChapterContent(
        title="Test Chapter Title",
        content="This is the test chapter content with some sample text that represents the actual content of a novel chapter.",
        url="http://example.com/test-chapter"
    )
    
    # Test save with auto-generated hash
    content_hash = chapter_content.generate_hash()
    assert chapter_content.save(), "Failed to save chapter content"
    print("✓ Save operation successful")
    
    # Test get
    retrieved_content = ScrapedChapterContent.get(content_hash)
    assert retrieved_content is not None, "Failed to retrieve chapter content"
    assert retrieved_content.title == "Test Chapter Title", "Retrieved data doesn't match"
    assert "sample text" in retrieved_content.content, "Content doesn't match"
    print("✓ Get operation successful")
    
    # Test save with custom identifier
    custom_id = "custom_chapter_001"
    chapter_content2 = ScrapedChapterContent(
        title="Custom Chapter",
        content="Custom chapter content for testing."
        url="http://example.com/custom-chapter"
    )
    assert chapter_content2.save(custom_id), "Failed to save with custom identifier"
    print("✓ Save with custom identifier successful")
    
    # Test update
    chapter_content.content = "Updated chapter content with new information."
    assert chapter_content.update(content_hash), "Failed to update chapter content"
    updated_content = ScrapedChapterContent.get(content_hash)
    assert "new information" in updated_content.content, "Update didn't work"
    print("✓ Update operation successful")
    
    # Test list operations
    all_content = ScrapedChapterContent.list_all()
    assert len(all_content) >= 2, "List all failed"
    print(f"✓ List all returned {len(all_content)} items")
    
    # Test exists
    assert ScrapedChapterContent.exists(content_hash), "Exists check failed"
    assert ScrapedChapterContent.exists(custom_id), "Custom ID exists check failed"
    print("✓ Exists check successful")
    
    # Test count
    count = ScrapedChapterContent.count()
    assert count >= 2, "Count failed"
    print(f"✓ Count returned {count}")
    
    # Test delete
    assert chapter_content.delete(content_hash), "Failed to delete chapter content"
    assert chapter_content2.delete(custom_id), "Failed to delete custom chapter content"
    assert not ScrapedChapterContent.exists(content_hash), "Delete didn't work"
    assert not ScrapedChapterContent.exists(custom_id), "Custom delete didn't work"
    print("✓ Delete operation successful")

def main():
    """Run all tests."""
    print("Starting CRUD operations test...")
    print("=" * 50)
    
    try:
        test_metadata_processing_data()
        test_chapter_processing_data()
        test_book_processing_data()
        test_scraped_chapter_content()
        test_scraped_book()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("\nCRUD operations are working correctly with Redis.")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        print("Make sure Redis server is running and accessible.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from libs.models import (
    ChapterProcessingData,
    BookProcessingData,
    ScrapedChapterContent,
    ScrapedBook,
    ScrapedMetadata,
    Status
)
from libs.db import db
from libs.celery import app as celery_app
from typing import List, Optional
import os

app = FastAPI(title="Node-TTS Data Introspection API", version="1.0.0")

class BookInjectionData(BaseModel):
    book_url: str
    good_reads_url: str
    short_book_name: str
    start_from_url: str
    process_until_url: str

# Mount static files if needed
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Node-TTS Data API"}

# ChapterProcessingData endpoints
@app.get("/chapters/", response_model=List[ChapterProcessingData])
async def list_chapters():
    return ChapterProcessingData.list_all()

@app.get("/chapters/{chapter_hash}", response_model=Optional[ChapterProcessingData])
async def get_chapter(chapter_hash: str):
    chapter = ChapterProcessingData.get(chapter_hash)
    if not chapter:
        raise HTTPException(status_code=404, detail="Chapter not found")
    return chapter

@app.get("/chapters/status/{status}", response_model=List[ChapterProcessingData])
async def list_chapters_by_status(status: Status):
    print("status on the request:", status)
    return ChapterProcessingData.list_by_status(status)

@app.get("/books/{book_hash}/chapters", response_model=List[ChapterProcessingData])
async def list_chapters_by_book(book_hash: str):
    return ChapterProcessingData.list_by_book_hash(book_hash)

# BookProcessingData endpoints
@app.get("/books/", response_model=List[BookProcessingData])
async def list_books():
    return BookProcessingData.list_all()

@app.get("/books/{book_hash}", response_model=Optional[BookProcessingData])
async def get_book(book_hash: str):
    book = BookProcessingData.get(book_hash)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

# ScrapedChapterContent endpoints
@app.get("/scraped-chapters/", response_model=List[ScrapedChapterContent])
async def list_scraped_chapters():
    return ScrapedChapterContent.list_all()

@app.get("/scraped-chapters/{identifier}", response_model=Optional[ScrapedChapterContent])
async def get_scraped_chapter(identifier: str):
    chapter = ScrapedChapterContent.get(identifier)
    if not chapter:
        raise HTTPException(status_code=404, detail="Scraped chapter not found")
    return chapter

# ScrapedBook endpoints
@app.get("/scraped-books/", response_model=List[ScrapedBook])
async def list_scraped_books():
    return ScrapedBook.list_all()

@app.get("/scraped-books/{identifier}", response_model=Optional[ScrapedBook])
async def get_scraped_book(identifier: str):
    book = ScrapedBook.get(identifier)
    if not book:
        raise HTTPException(status_code=404, detail="Scraped book not found")
    return book

# ScrapedMetadata endpoints
@app.get("/metadata/", response_model=List[ScrapedMetadata])
async def list_metadata():
    return ScrapedMetadata.list_all()

@app.get("/metadata/{book_hash}", response_model=Optional[ScrapedMetadata])
async def get_metadata(book_hash: str):
    metadata = ScrapedMetadata.get(book_hash)
    if not metadata:
        raise HTTPException(status_code=404, detail="Metadata not found")
    return metadata

# Inject new book endpoint
@app.post("/inject-book")
async def inject_book(data: BookInjectionData):
    celery_app.send_task('worker.tasks.process_book', 
                  args=[data.dict()], 
                  queue='book-queue')
    return {"message": "Book injection task sent"}

# Serve the UI
@app.get("/ui", response_class=HTMLResponse)
async def get_ui():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Node-TTS Data Introspection</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .section { margin-bottom: 30px; }
        button { padding: 10px 15px; margin: 5px; cursor: pointer; }
        pre { background: #f4f4f4; padding: 10px; border-radius: 5px; overflow-x: auto; }
        .data-display { max-height: 400px; overflow-y: auto; }
    </style>
</head>
<body>
    <h1>Node-TTS Data Introspection</h1>
    
    <div class="section">
        <h2>Chapter Processing Data</h2>
        <button onclick="loadChapters()">Load All Chapters</button>
        <button onclick="loadChaptersByStatus('pending')">Pending</button>
        <button onclick="loadChaptersByStatus('processing')">Processing</button>
        <button onclick="loadChaptersByStatus('completed')">Completed</button>
        <button onclick="loadChaptersByStatus('failed')">Failed</button>
        <div id="chapters-data" class="data-display"></div>
    </div>
    
    <div class="section">
        <h2>Book Processing Data</h2>
        <button onclick="loadBooks()">Load All Books</button>
        <div id="books-data" class="data-display"></div>
    </div>
    
    <div class="section">
        <h2>Scraped Chapters</h2>
        <button onclick="loadScrapedChapters()">Load All Scraped Chapters</button>
        <div id="scraped-chapters-data" class="data-display"></div>
    </div>
    
    <div class="section">
        <h2>Scraped Books</h2>
        <button onclick="loadScrapedBooks()">Load All Scraped Books</button>
        <div id="scraped-books-data" class="data-display"></div>
    </div>
    
    <div class="section">
        <h2>Metadata</h2>
        <button onclick="loadMetadata()">Load All Metadata</button>
        <div id="metadata-data" class="data-display"></div>
    </div>
    
    <div class="section">
        <h2>Inject New Book</h2>
        <form id="inject-book-form">
            <label for="book_url">Book URL:</label><br>
            <input type="text" id="book_url" name="book_url" required><br>
            <label for="good_reads_url">Good Reads URL:</label><br>
            <input type="text" id="good_reads_url" name="good_reads_url" required><br>
            <label for="short_book_name">Short Book Name:</label><br>
            <input type="text" id="short_book_name" name="short_book_name" required><br>
            <label for="start_from_url">Start From URL:</label><br>
            <input type="text" id="start_from_url" name="start_from_url" required><br>
            <label for="process_until_url">Process Until URL:</label><br>
            <input type="text" id="process_until_url" name="process_until_url" required><br>
            <button type="submit">Inject Book</button>
        </form>
        <div id="inject-result"></div>
    </div>

    <script>
        const baseUrl = 'http://localhost:8000';
        
        function displayData(elementId, data) {
            const element = document.getElementById(elementId);
            element.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
        }
        
        async function loadChapters() {
            const response = await fetch(`${baseUrl}/chapters/`);
            const data = await response.json();
            displayData('chapters-data', data);
        }
        
        async function loadChaptersByStatus(status) {
            const response = await fetch(`${baseUrl}/chapters/status/${status}`);
            const data = await response.json();
            displayData('chapters-data', data);
        }
        
        async function loadBooks() {
            const response = await fetch(`${baseUrl}/books/`);
            const data = await response.json();
            displayData('books-data', data);
        }
        
        async function loadScrapedChapters() {
            const response = await fetch(`${baseUrl}/scraped-chapters/`);
            const data = await response.json();
            displayData('scraped-chapters-data', data);
        }
        
        async function loadScrapedBooks() {
            const response = await fetch(`${baseUrl}/scraped-books/`);
            const data = await response.json();
            displayData('scraped-books-data', data);
        }
        
        async function loadMetadata() {
            const response = await fetch(`${baseUrl}/metadata/`);
            const data = await response.json();
            displayData('metadata-data', data);
        }
        
        document.getElementById('inject-book-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            const response = await fetch(`${baseUrl}/inject-book`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            const result = await response.json();
            document.getElementById('inject-result').innerHTML = '<pre>' + JSON.stringify(result, null, 2) + '</pre>';
        });
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

import os

from playwright.sync_api import sync_playwright
from playwright_stealth import Stealth
from bs4 import BeautifulSoup
from datetime import date

from .models import ScrapedBook, BookChapterLink, ScrapedChapterContent, ScrapedMetadata

def content_parser(soup) -> ScrapedChapterContent:
    """Extract content and title from BeautifulSoup object."""
    content_div = soup.find('div', id='chr-content')
    content = content_div.get_text(strip=True) if content_div and len(content_div) > 0 else None

    title_tag = soup.find('a', class_='chr-title')
    title = title_tag.get_text(strip=True) if title_tag and len(title_tag) > 0 else None

    return ScrapedChapterContent(title=title, content=content) if title and content else None

def book_chapters_parser(soup) -> ScrapedBook:
    """Extract book name and chapter links from soup."""
    title_tag = soup.select_one('div.desc > h3.title')
    book_name = title_tag.get_text(strip=True) if title_tag and len(title_tag) > 0 else None

    chapter_links: list[BookChapterLink] = []

    for a_tag in soup.select('ul.list-chapter > li > a'):
        href = a_tag.get('href')
        a_title = a_tag.get('title')

        if href and a_title:
            chapter = BookChapterLink(title=a_title, url=href)
            chapter_links.append(chapter)

    is_book_present = book_name and len(chapter_links) > 0
    return ScrapedBook(title=book_name, chapters=chapter_links) if is_book_present else None

def goodreads_metadata_parser(soup: BeautifulSoup) -> ScrapedMetadata:
    """Extract metadata from Goodreads book page."""
    def multiple_texts(element, separator=', ', default=''):
        if element:
            texts = [text.strip() for text in element.stripped_strings]
            return separator.join(texts)
        return default

    def safe_text(element, default=''):
        return element.get_text(strip=True) if element else default

    def safe_attr(element, attr, default=''):
        if element and hasattr(element, 'get'):
            result = element.get(attr, default)
            return str(result) if result is not None else default
        return default

    title_element = soup.find('h1', class_='Text__title1')
    author_element = soup.find('a', class_='ContributorLink')
    image_element = soup.find('img', class_="ResponsiveImage")
    desc_element = soup.select_one('div', class_='BookPageMetadataSection__description')
    genres = soup.find('div', class_='BookPageMetadataSection__genres')

    return ScrapedMetadata(
        title=safe_text(title_element),
        artist=safe_text(author_element, 'Unknown Artist'),
        image=safe_attr(image_element, 'src'),
        description=safe_text(desc_element),
        genre=multiple_texts(genres, separator=';'),
        released_year=date.today().isoformat().split('-')[0],
        created_at=date.today().isoformat()
    )

def scrape_url(url, handler):
    """Scrape the given URL and return the page content."""
    try:
        with Stealth().use_sync(sync_playwright()) as p:
            browser = p.chromium.connect(os.getenv("PLAYWRIGHT_BROWSER_URL", "ws://localhost:3000"))
            page = browser.new_page()

            page.goto(url)
            page.wait_for_timeout(7000)

            page_html = page.content()
            browser.close()
                
            soup = BeautifulSoup(page_html, 'html.parser')
            return handler(soup)
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return None


def scrape_book_metadata(book_url: str) -> ScrapedMetadata | None:
    """Scrape book metadata from the given Goodreads book URL."""
    result = scrape_url(book_url, goodreads_metadata_parser)
    
    if result is None:
        print(f"Failed to scrape metadata from {book_url}")
        return None

    return result

def scrape_book_chapters(book_url: str, start_from: str, end_at: str) -> ScrapedBook | None:
    """Scrape book chapters from the given book URL."""
    result =  scrape_url(book_url, book_chapters_parser)

    if result is None:
        print(f"Failed to scrape book chapters from {book_url}")
        return None

    print(f"Scraped book: {result.title} with {len(result.chapters)} chapters")
    return result

def scrape_chapter_content(chapter_url: str) -> ScrapedChapterContent | None:
    """Scrape chapter content from the given chapter URL."""
    result = scrape_url(chapter_url, content_parser)
    
    if result is None:
        print(f"Failed to scrape chapter content from {chapter_url}")
        return None

    print(f"Scraped chapter: {result.title} with content length {len(result.content)}")
    return result

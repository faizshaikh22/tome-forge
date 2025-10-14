import logging
import os
import re

from bs4 import BeautifulSoup
import ebooklib
from ebooklib import epub

logger = logging.getLogger(__name__)

class EpubParserService:
    """A service to parse EPUB files and extract chapters as plain text.

    This service scans a source directory for book subdirectories, finds an
    'book.epub' file within each, and extracts its content into individual

    chapter text files.

    Attributes:
        sources_dir: The root directory containing book subfolders to process.
    """

    def __init__(self, sources_dir: str):
        """Initializes the service with the path to the sources directory.

        Args:
            sources_dir: The path to the directory containing book subfolders.
        """
        self.sources_dir = sources_dir

    def _sanitize_filename(self, name: str) -> str:
        """Sanitizes a string to be a valid filename.

        Args:
            name: The input string to sanitize.

        Returns:
            A sanitized string suitable for use as a filename.
        """
        name = re.sub(r'[^\w\s-]', '', name).strip()
        name = re.sub(r'[-\s]+', '_', name)
        return name.lower()[:100]

    def _build_toc_map(self, toc_items):
        """Recursively builds a map from content href to Table of Contents title.

        Args:
            toc_items: A list or tuple of items from an ebooklib book's TOC.

        Returns:
            A dictionary mapping cleaned chapter file hrefs to their titles.
        """
        href_map = {}
        for item in toc_items:
            if isinstance(item, tuple):
                section, children = item
                if hasattr(section, 'href'):
                    href_clean = section.href.split('#')[0]
                    href_map[href_clean] = section.title
                href_map.update(self._build_toc_map(children))
            elif isinstance(item, epub.Link):
                href_clean = item.href.split('#')[0]
                href_map[href_clean] = item.title
        return href_map

    def _extract_and_save_chapters(self, book, chapters_dir: str):
        """Extracts chapter content and saves it to text files.

        Args:
            book: An opened ebooklib.epub.EpubBook object.
            chapters_dir: The directory where the chapter .txt files will be
                saved.
        """
        logger.info(f"Extracting chapters to '{chapters_dir}'")
        toc_map = self._build_toc_map(book.toc)
        chapters = list(book.get_items_of_type(ebooklib.ITEM_DOCUMENT))

        for i, chapter in enumerate(chapters):
            soup = BeautifulSoup(chapter.get_content(), 'html.parser')
            text = soup.get_text(strip=True)

            if not text:
                continue

            title = toc_map.get(chapter.file_name, chapter.title or f"Chapter_{i+1}")
            sanitized_title = self._sanitize_filename(title)
            filename = f"{i:03d}_{sanitized_title}.txt"
            file_path = os.path.join(chapters_dir, filename)

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
            except IOError as e:
                logger.error(f"Could not write to file {file_path}: {e}")

    def process_books(self):
        """Crawls the sources directory and processes all found books.

        For each subdirectory in the main sources directory, this method
        looks for a 'book.epub' file. If found, and if chapters have not
        already been extracted, it orchestrates the parsing and saving of
        the chapter content.
        """
        logger.info(f"Starting to process books in '{self.sources_dir}'")
        for book_name in os.listdir(self.sources_dir):
            book_dir = os.path.join(self.sources_dir, book_name)
            if not os.path.isdir(book_dir):
                continue

            logger.info(f"Checking book: {book_name}")
            epub_path = os.path.join(book_dir, 'book.epub')
            chapters_dir = os.path.join(book_dir, 'chapters')

            if os.path.exists(chapters_dir) and os.listdir(chapters_dir):
                logger.info(f"Chapters already exist for '{book_name}', skipping.")
                continue

            if not os.path.exists(epub_path):
                logger.warning(f"'book.epub' not found in '{book_dir}', skipping.")
                continue

            try:
                logger.info(f"Processing '{epub_path}'")
                os.makedirs(chapters_dir, exist_ok=True)
                book = epub.read_epub(epub_path)
                self._extract_and_save_chapters(book, chapters_dir)
                logger.info(f"Finished processing '{book_name}'.")
            except ebooklib.epub.EpubException as e:
                logger.error(f"Failed to process '{book_name}': {e}")

if __name__ == '__main__':
    # The script will look for books in the 'Sources' directory 
    # relative to the project root.
    project_root = os.path.dirname(os.path.abspath(__file__))
    sources_directory = os.path.join(project_root, 'Sources')
    
    parser_service = EpubParserService(sources_dir=sources_directory)
    parser_service.process_books()

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup
import os
import re
import logging

class EpubParserService:
    """A service to parse EPUB files and extract chapters."""

    def __init__(self, sources_dir: str):
        """
        Initializes the service with the path to the sources directory.

        Args:
            sources_dir (str): The path to the directory containing book subfolders.
        """
        self.sources_dir = sources_dir
        self._setup_logging()

    def _setup_logging(self):
        """Sets up a basic logging configuration."""
        logging.basicConfig(level=logging.INFO, 
                            format='%(asctime)s - %(levelname)s - %(message)s')

    def _sanitize_filename(self, name: str) -> str:
        """
        Takes a string and returns a sanitized version suitable for a filename.
        """
        name = re.sub(r'[^\w\s-]', '', name).strip()
        name = re.sub(r'[-\s]+', '_', name)
        return name.lower()[:100]

    def _build_toc_map(self, toc_items):
        """
        Recursively builds a map from a content file's href to its TOC title.
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
        """
        Extracts plain text from each chapter and saves it to a .txt file.
        """
        logging.info(f"Extracting chapters to '{chapters_dir}'")
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
                logging.error(f"Could not write to file {file_path}: {e}")

    def process_books(self):
        """Crawls the sources directory and processes each book."""
        logging.info(f"Starting to process books in '{self.sources_dir}'")
        for book_name in os.listdir(self.sources_dir):
            book_dir = os.path.join(self.sources_dir, book_name)
            if not os.path.isdir(book_dir):
                continue

            logging.info(f"Checking book: {book_name}")
            epub_path = os.path.join(book_dir, 'book.epub')
            chapters_dir = os.path.join(book_dir, 'chapters')

            if os.path.exists(chapters_dir) and os.listdir(chapters_dir):
                logging.info(f"Chapters already exist for '{book_name}', skipping.")
                continue

            if not os.path.exists(epub_path):
                logging.warning(f"'book.epub' not found in '{book_dir}', skipping.")
                continue

            try:
                logging.info(f"Processing '{epub_path}'")
                os.makedirs(chapters_dir, exist_ok=True)
                book = epub.read_epub(epub_path)
                self._extract_and_save_chapters(book, chapters_dir)
                logging.info(f"Finished processing '{book_name}'.")
            except Exception as e:
                logging.error(f"Failed to process '{book_name}': {e}")

if __name__ == '__main__':
    # The script will look for books in the 'Sources' directory 
    # relative to the project root.
    project_root = os.path.dirname(os.path.abspath(__file__))
    sources_directory = os.path.join(project_root, 'Sources')
    
    parser_service = EpubParserService(sources_dir=sources_directory)
    parser_service.process_books()

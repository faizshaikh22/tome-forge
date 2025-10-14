# utils/file_utils.py
import logging
import os

import config

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def find_first_book_with_chapters(sources_dir=config.SOURCES_DIR):
    """Finds the first book with extracted chapter files.

    Args:
        sources_dir: The directory containing book subdirectories.

    Returns:
        A tuple containing (book_path, book_name, chapter_files) if a
        book with chapters is found, otherwise (None, None, None).
    """
    for book_name in os.listdir(sources_dir):
        book_path = os.path.join(sources_dir, book_name)
        if os.path.isdir(book_path):
            chapters_path = os.path.join(book_path, "chapters")
            if os.path.exists(chapters_path) and os.listdir(chapters_path):
                chapter_files = [
                    f for f in os.listdir(chapters_path) if f.endswith(".txt")
                ]
                if chapter_files:
                    return book_path, book_name, chapter_files
    return None, None, None


def get_author_from_book_name(book_name):
    """Extracts an author's name from a book's directory name.

    Assumes a format like "Book Title by Author".

    Args:
        book_name: The name of the book's directory.

    Returns:
        The extracted author name as a string, or "Unknown Author" if the
        pattern is not found.
    """
    if " by " in book_name:
        parts = book_name.split(" by ")
        if len(parts) > 1:
            return parts[-1]
    return "Unknown Author"


def load_completed_chapters():
    """Reads the progress log file to determine which chapters are complete.

    Returns:
        A set of strings, where each string is the JSON file path of a
        chapter that has already been successfully processed. Returns an
        empty set if the progress file does not exist.
    """
    if not os.path.exists(config.PROGRESS_FILE):
        return set()
    with open(config.PROGRESS_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f}


def log_completed_chapter(json_path):
    """Appends a chapter's JSON path to the progress log file.

    Args:
        json_path: The file path of the successfully generated JSON file.
    """
    with open(config.PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(json_path + "\n")


def get_chapter_stats(sources_dir: str = config.SOURCES_DIR) -> list[dict]:
    """Gathers statistics for every chapter file in the sources directory.

    This function scans all book subdirectories to find chapter text files
    and calculates statistics for each one, such as its word count.

    Args:
        sources_dir: The root directory containing book subdirectories.

    Returns:
        A list of dictionaries, where each dictionary contains the path,
        book name, filename, and word count for a single chapter.
    """
    if not os.path.isdir(sources_dir):
        logging.error(f"Sources directory not found at: {sources_dir}")
        return []

    chapter_stats = []
    for book_name in sorted(os.listdir(sources_dir)):
        book_path = os.path.join(sources_dir, book_name)
        if os.path.isdir(book_path):
            chapters_path = os.path.join(book_path, "chapters")
            if os.path.isdir(chapters_path):
                for chapter_file in sorted(os.listdir(chapters_path)):
                    if chapter_file.endswith(".txt"):
                        chapter_full_path = os.path.join(chapters_path, chapter_file)
                        try:
                            with open(chapter_full_path, "r", encoding="utf-8") as f:
                                content = f.read()
                                word_count = len(content.split())
                                chapter_stats.append(
                                    {
                                        "path": chapter_full_path,
                                        "book": book_name,
                                        "filename": chapter_file,
                                        "word_count": word_count,
                                    }
                                )
                        except (OSError, UnicodeDecodeError) as e:
                            logging.error(
                                f"Could not read or process {chapter_full_path}: {e}"
                            )
    return chapter_stats

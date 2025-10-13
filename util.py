import os
import logging

# Set up basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def count_all_chapters(sources_dir: str = "Sources") -> int:
    """
    Counts the total number of chapter files across all books in the Sources directory.

    This function navigates through each book's subdirectory, finds the 'chapters'
    folder, and counts the number of .txt files within it.

    Args:
        sources_dir (str): The path to the main sources directory containing book folders.

    Returns:
        int: The total count of all chapter files found.
    """
    if not os.path.isdir(sources_dir):
        logging.error(f"Sources directory not found at: {sources_dir}")
        return 0

    total_chapters = 0
    logging.info(f"Starting chapter count in '{sources_dir}'...")

    for book_name in os.listdir(sources_dir):
        book_path = os.path.join(sources_dir, book_name)
        if os.path.isdir(book_path):
            chapters_path = os.path.join(book_path, "chapters")
            if os.path.isdir(chapters_path):
                try:
                    # Count only .txt files to be specific to chapters
                    chapter_files = [
                        f for f in os.listdir(chapters_path) if f.endswith(".txt")
                    ]
                    num_chapters = len(chapter_files)
                    logging.info(f"Found {num_chapters} chapters in '{book_name}'.")
                    total_chapters += num_chapters
                except OSError as e:
                    logging.error(
                        f"Could not access chapters in '{chapters_path}': {e}"
                    )
            else:
                logging.warning(
                    f"No 'chapters' directory found for book '{book_name}'."
                )

    logging.info(f"Total chapter count across all books: {total_chapters}")
    return total_chapters


if __name__ == "__main__":
    # Assuming the script is run from the project root directory
    project_root = os.path.dirname(os.path.abspath(__file__))
    sources_path = os.path.join(project_root, "Sources")

    total_count = count_all_chapters(sources_dir=sources_path)
    print(f"\nTotal number of chapters found: {total_count}")


def get_chapter_stats(sources_dir: str = "Sources") -> list[dict]:
    """
    Gathers statistics (path, book name, filename, and word count) for every chapter file.

    Args:
        sources_dir (str): The path to the main sources directory.

    Returns:
        list[dict]: A list of dictionaries, each containing stats for a chapter.
    """
    if not os.path.isdir(sources_dir):
        logging.error(f"Sources directory not found at: {sources_dir}")
        return []

    chapter_stats = []
    logging.info(f"Gathering stats for all chapters in '{sources_dir}'...")

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

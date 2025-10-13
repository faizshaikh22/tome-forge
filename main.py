import os
import json
from call_llm import LLMService
from prompts import generate_qa_pairs_for_chapter


def find_first_book_with_chapters(sources_dir="Sources"):
    """
    Find the first book in the sources directory that has chapters available.

    Args:
        sources_dir: Directory containing book subdirectories

    Returns:
        tuple: (book_path, book_name, chapter_files) or (None, None, None) if not found
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
    """
    Extract author name from book directory name.
    Assumes format like "Book Title by Author" or just tries to infer from the name.
    """
    # This is a simple heuristic - in a real application you might have a mapping
    # or metadata file with author information
    if " by " in book_name:
        parts = book_name.split(" by ")
        if len(parts) > 1:
            return parts[-1]  # Take the last part after "by"

    # If no "by" is found, we'll just use the book name itself as book title
    # and leave author as blank or use a default
    return "Unknown Author"


from util import get_chapter_stats


PROGRESS_FILE = "_completed_chapters.log"


def load_completed_chapters():
    """Reads the progress file and returns a set of completed JSON paths."""

    if not os.path.exists(PROGRESS_FILE):
        return set()

    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        return {line.strip() for line in f}


def log_completed_chapter(json_path):
    """Appends a successfully completed chapter's JSON path to the progress file."""

    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(json_path + "\n")


def main():
    """


    Main orchestration script to generate Q&A pairs for all books in the Sources directory.


    """

    service = LLMService()

    # --- Load Progress ---

    completed_chapters_set = load_completed_chapters()

    print(f"Found {len(completed_chapters_set)} previously completed chapters.")

    # --- Step 1: Pre-computation ---

    print("Step 1: Analyzing all chapters to determine workload...")

    sources_path = os.path.abspath("Sources")

    all_chapter_stats = get_chapter_stats(sources_dir=sources_path)

    if not all_chapter_stats:
        print("No chapters found. Exiting.")

        return

    total_words = sum(c["word_count"] for c in all_chapter_stats)

    total_chapters = len(all_chapter_stats)

    avg_word_count = total_words / total_chapters

    print(
        f"Found {total_chapters} chapters with an average of {avg_word_count:.0f} words per chapter."
    )

    # --- Step 2: Define Generation Parameters ---

    TARGET_TOTAL_PAIRS = 10000

    baseline_questions = TARGET_TOTAL_PAIRS / total_chapters

    MIN_QUESTIONS = 10

    MAX_QUESTIONS = 100

    print(f"Baseline questions for an average chapter: {baseline_questions:.1f}")

    print(f"Question caps: Min={MIN_QUESTIONS}, Max={MAX_QUESTIONS}")

    # --- Step 3: Main Generation Loop ---

    print("\nStep 3: Planning Q&A generation for all chapters...")

    total_planned_qa = 0

    for i, chapter_info in enumerate(all_chapter_stats):
        # Define output path first to check for completion

        book_path = os.path.dirname(os.path.dirname(chapter_info["path"]))

        output_dir = os.path.join(book_path, "output")

        chapter_name_base = os.path.splitext(chapter_info["filename"])[0]

        safe_chapter_name = "".join(
            c for c in chapter_name_base if c.isalnum() or c in "._- "
        )

        json_filename = f"{safe_chapter_name}.json"

        json_path = os.path.join(output_dir, json_filename)

        # --- Check if chapter is already completed ---

        if json_path in completed_chapters_set:
            print(
                f"\n--- Chapter {i + 1}/{total_chapters}: SKIPPING (Already Completed) ---"
            )

            print(
                f"  Book: {chapter_info['book']}, Chapter: {chapter_info['filename']}"
            )

            continue

        # a. Calculate num_questions for this specific chapter

        scaling_factor = (
            chapter_info["word_count"] / avg_word_count if avg_word_count > 0 else 1
        )

        num_questions = round(baseline_questions * scaling_factor)

        num_questions = max(MIN_QUESTIONS, min(num_questions, MAX_QUESTIONS))

        total_planned_qa += num_questions

        print(f"\n--- Chapter {i + 1}/{total_chapters}: PROCESSING ---")

        print(f"  Book: {chapter_info['book']}")

        print(f"  Chapter: {chapter_info['filename']}")

        print(
            f"  Word count: {chapter_info['word_count']} (Scaling factor: {scaling_factor:.2f}) -> Target Q&A pairs: {num_questions}"
        )

        # b. Get remaining info for generation

        author = get_author_from_book_name(chapter_info["book"])

        chapter_name_for_prompt = (
            "_".join(chapter_name_base.split("_")[1:])
            if "_" in chapter_name_base
            else chapter_name_base
        )

        os.makedirs(output_dir, exist_ok=True)

        # c. Call the generation function
        print(f"  Output will be saved to {json_path}")
        try:
            with open(chapter_info["path"], "r", encoding="utf-8") as f:
                chapter_text = f.read()

            generate_qa_pairs_for_chapter(
                author="Nietzsche",
                book=chapter_info["book"],
                chapter_name=chapter_name_for_prompt,
                chapter_text=chapter_text,
                llm_function=service.generate_text,
                json_path=json_path,
                no_of_questions=num_questions,
            )
            # On success, log the chapter as completed
            log_completed_chapter(json_path)
            print(f"  Successfully completed and logged chapter.")

        except Exception as e:
            print(
                f"  A critical error occurred during Q&A generation for this chapter: {e}"
            )
            # The script will continue to the next chapter

        # Exit after the first chapter as requested for the test run.
        print("\n--- First chapter run complete. Exiting as planned. ---")
        break

    print(f"\n--- Pre-computation Complete ---")

    print(
        f"Total planned Q&A pairs for this run (excluding skipped chapters): {total_planned_qa}"
    )


if __name__ == "__main__":
    main()

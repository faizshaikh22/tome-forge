import os
import json
from services.llm_service import LLMService
from pipelines.qa_generation import generate_qa_pairs_for_chapter
from utils.file_utils import (
    load_completed_chapters,
    log_completed_chapter,
    get_chapter_stats,
    get_author_from_book_name,
)
import config




def plan_generation_workload(all_chapter_stats, completed_chapters_set):
    """
    Analyzes chapters and creates a plan for Q&A generation.
    """
    if not all_chapter_stats:
        print("No chapters found. Exiting.")
        return []

    total_chapters = len(all_chapter_stats)
    total_words = sum(c["word_count"] for c in all_chapter_stats)
    avg_word_count = total_words / total_chapters
    baseline_questions = config.TARGET_TOTAL_PAIRS / total_chapters

    print(f"Found {total_chapters} chapters with an average of {avg_word_count:.0f} words per chapter.")
    print(f"Baseline questions for an average chapter: {baseline_questions:.1f}")
    print(f"Question caps: Min={config.MIN_QUESTIONS_PER_CHAPTER}, Max={config.MAX_QUESTIONS_PER_CHAPTER}")

    generation_plan = []
    for chapter_info in all_chapter_stats:
        book_path = os.path.dirname(os.path.dirname(chapter_info["path"]))
        output_dir = os.path.join(book_path, "output")
        chapter_name_base = os.path.splitext(chapter_info["filename"])[0]
        safe_chapter_name = "".join(c for c in chapter_name_base if c.isalnum() or c in "._- ")
        json_filename = f"{safe_chapter_name}.json"
        json_path = os.path.join(output_dir, json_filename)

        if json_path in completed_chapters_set:
            continue

        scaling_factor = chapter_info["word_count"] / avg_word_count if avg_word_count > 0 else 1
        num_questions = round(baseline_questions * scaling_factor)
        num_questions = max(
            config.MIN_QUESTIONS_PER_CHAPTER,
            min(num_questions, config.MAX_QUESTIONS_PER_CHAPTER),
        )

        generation_plan.append({**chapter_info, "json_path": json_path, "num_questions": num_questions})

    return generation_plan


def execute_generation_workload(generation_plan, service):
    """
    Executes the Q&A generation plan.
    """
    total_chapters = len(generation_plan)
    for i, chapter_info in enumerate(generation_plan):
        print(f"\n--- Chapter {i + 1}/{total_chapters}: PROCESSING ---")
        print(f"  Book: {chapter_info['book']}")
        print(f"  Chapter: {chapter_info['filename']}")
        print(f"  Word count: {chapter_info['word_count']} -> Target Q&A pairs: {chapter_info['num_questions']}")

        chapter_name_base = os.path.splitext(chapter_info["filename"])[0]
        chapter_name_for_prompt = "_".join(chapter_name_base.split("_")[1:]) if "_" in chapter_name_base else chapter_name_base

        output_dir = os.path.dirname(chapter_info["json_path"])
        os.makedirs(output_dir, exist_ok=True)

        print(f"  Output will be saved to {chapter_info['json_path']}")
        try:
            with open(chapter_info["path"], "r", encoding="utf-8") as f:
                chapter_text = f.read()

            generate_qa_pairs_for_chapter(
                author=config.AUTHOR,
                book=chapter_info["book"],
                chapter_name=chapter_name_for_prompt,
                chapter_text=chapter_text,
                llm_function=service.generate_text,
                json_path=chapter_info["json_path"],
                no_of_questions=chapter_info["num_questions"],
            )
            log_completed_chapter(chapter_info["json_path"])
            print("  Successfully completed and logged chapter.")

        except Exception as e:
            print(f"  A critical error occurred during Q&A generation for this chapter: {e}")


def main():
    """
    Main orchestration script.
    """
    service = LLMService()
    completed_chapters_set = load_completed_chapters()
    print(f"Found {len(completed_chapters_set)} previously completed chapters.")

    print("Step 1: Analyzing all chapters to determine workload...")
    all_chapter_stats = get_chapter_stats(sources_dir=config.SOURCES_DIR)
    generation_plan = plan_generation_workload(all_chapter_stats, completed_chapters_set)

    if not generation_plan:
        print("No chapters to process. Exiting.")
        return

    print("\nStep 2: Executing Q&A generation...")
    execute_generation_workload(generation_plan, service)

    print("\n--- Generation Complete ---")


if __name__ == "__main__":
    main()

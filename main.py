import json
import os

import config
from pipelines.qa_generation import generate_qa_pairs_for_chapter
from services.llm_service import LLMService
from utils.file_utils import (
    get_author_from_book_name,
    get_chapter_stats,
    load_completed_chapters,
    log_completed_chapter,
)
from utils.logging_utils import setup_logging

import logging

logger = logging.getLogger(__name__)


def plan_generation_workload(all_chapter_stats, completed_chapters_set):
    """Analyzes chapter statistics to create a Q&A generation plan.

    This function calculates the number of questions to generate for each chapter
    based on its word count relative to the average. It filters out chapters
    that have already been completed.

    Args:
        all_chapter_stats: A list of dictionaries, where each dictionary contains
            statistics for a chapter (e.g., path, word_count).
        completed_chapters_set: A set of JSON file paths for chapters that
            have already been processed and saved.

    Returns:
        A list of dictionaries, representing the generation plan. Each dictionary
        extends the original chapter stats with 'json_path' and 'num_questions'
        to generate for that chapter. Returns an empty list if no chapters
        are found.
    """
    if not all_chapter_stats:
        logger.info("No chapters found. Exiting.")
        return []

    total_chapters = len(all_chapter_stats)
    total_words = sum(c["word_count"] for c in all_chapter_stats)
    avg_word_count = total_words / total_chapters
    baseline_questions = config.TARGET_TOTAL_PAIRS / total_chapters

    logger.info(f"Found {total_chapters} chapters with an average of {avg_word_count:.0f} words per chapter.")
    logger.info(f"Baseline questions for an average chapter: {baseline_questions:.1f}")
    logger.info(f"Question caps: Min={config.MIN_QUESTIONS_PER_CHAPTER}, Max={config.MAX_QUESTIONS_PER_CHAPTER}")

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
    """Executes the Q&A generation plan for each chapter.

    Iterates through the generation plan and calls the Q&A generation
    pipeline for each chapter. It handles reading the chapter text,
    calling the LLM service, and logging completion.

    Args:
        generation_plan: A list of dictionaries, where each dictionary
            represents a chapter to be processed and contains all necessary
            information (e.g., file path, number of questions).
        service: An instance of the LLMService to be used for generating text.
    """
    total_chapters = len(generation_plan)
    for i, chapter_info in enumerate(generation_plan):
        logger.info(f"--- Chapter {i + 1}/{total_chapters}: PROCESSING ---")
        logger.info(f"  Book: {chapter_info['book']}")
        logger.info(f"  Chapter: {chapter_info['filename']}")
        logger.info(f"  Word count: {chapter_info['word_count']} -> Target Q&A pairs: {chapter_info['num_questions']}")

        chapter_name_base = os.path.splitext(chapter_info["filename"])[0]
        chapter_name_for_prompt = "_".join(chapter_name_base.split("_")[1:]) if "_" in chapter_name_base else chapter_name_base

        output_dir = os.path.dirname(chapter_info["json_path"])
        os.makedirs(output_dir, exist_ok=True)

        logger.info(f"  Output will be saved to {chapter_info['json_path']}")
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
            logger.info("  Successfully completed and logged chapter.")

        except IOError as e:
            logger.error(f"  An IO error occurred for chapter {chapter_info['filename']}: {e}")
        except Exception as e:
            logger.error(f"  An unexpected error occurred during Q&A generation for {chapter_info['filename']}: {e}")


def main():
    """Main orchestration script to generate Q&A pairs for all books.

    This script serves as the entry point to the Q&A generation pipeline.
    It initializes the LLM service, loads progress, plans the generation
    workload by analyzing all chapters, and then executes the plan.
    """
    setup_logging()
    service = LLMService()
    completed_chapters_set = load_completed_chapters()
    logger.info(f"Found {len(completed_chapters_set)} previously completed chapters.")

    logger.info("Step 1: Analyzing all chapters to determine workload...")
    all_chapter_stats = get_chapter_stats(sources_dir=config.SOURCES_DIR)
    generation_plan = plan_generation_workload(all_chapter_stats, completed_chapters_set)

    if not generation_plan:
        logger.info("No chapters to process. Exiting.")
        return

    logger.info("Step 2: Executing Q&A generation...")
    execute_generation_workload(generation_plan, service)

    logger.info("--- Generation Complete ---")


if __name__ == "__main__":
    main()

# pipelines/qa_generation.py
import os
import json
from prompts_library import qa_prompts
from utils import parsing_utils
import config


def generate_qa_pairs_for_chapter(
    author: str,
    book: str,
    chapter_name: str,
    chapter_text: str,
    llm_function,
    json_path: str,
    no_of_questions: int,
):
    """
    Complete, resilient pipeline to generate and save Q&A pairs for a chapter.
    """
    qa_pairs = []
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                qa_pairs = json.load(f)
            except json.JSONDecodeError:
                qa_pairs = []

    question_prompt = qa_prompts.get_question_generation_prompt(
        chapter_name, book, author, no_of_questions
    )
    questions_result = llm_function(question_prompt)
    questions_output = questions_result["content"]
    questions = parsing_utils.parse_questions_response(questions_output)

    if not questions:
        print("Could not generate or parse questions. Aborting.")
        return

    for q in questions:
        answer_prompt = qa_prompts.get_answer_generation_prompt(
            author=author,
            chapter_text=chapter_text,
            book=book,
            question=q["text"],
            chapter_name=chapter_name,
        )

        answer_result = llm_function(answer_prompt)
        answer_output = answer_result["content"]
        answer_data = parsing_utils.parse_answer_response(answer_output)

        qa_pair = {
            "metadata": {
                "author": author,
                "book": book,
                "chapter": chapter_name,
                "question_id": q.get("id", "N/A"),
                "layer": q.get("layer", "N/A"),
                "llm_provider": answer_result["provider_name"],
                "llm_model": answer_result["model_name"],
            },
            "question": q.get("text", "Error: Could not parse question text."),
            "thinking": answer_data["thinking"],
            "answer": answer_data["response"],
        }
        qa_pairs.append(qa_pair)

        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"CRITICAL: Could not write to file {json_path}. Error: {e}")
            return

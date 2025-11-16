# Tome Forge

Tome Forge is a sophisticated data generation pipeline designed to create high-quality, nuanced question-and-answer pairs from dense philosophical texts. The primary goal is to produce a rich dataset suitable for fine-tuning smaller, specialized language models, enabling them to capture the unique voice, style, and reasoning of a specific author.

## The Core Problem

Standard language models often provide generic, surface-level answers when confronted with complex philosophical ideas. This project tackles that challenge by generating Q&A pairs that reflect a deep engagement with the source material, capturing the author's characteristic tone, arguments, and even emotional undercurrents.

## The Pipeline

The process is orchestrated as a clear, step-by-step pipeline:

1.  **Download:** Ebooks are downloaded from Project Gutenberg based on a configurable list.
2.  **Parse:** The EPUB files are parsed, and their content is broken down into individual chapter files.
3.  **Generate Q&A:** For each chapter, a powerful Large Language Model (LLM) generates a series of thoughtful questions and then crafts answers in the voice of the original author, grounded specifically in the text of that chapter.

## Project Structure

The codebase is organized into a modular and maintainable structure:

-   `config.py`: A central configuration file for all settings, including the book list and LLM parameters.
-   `services/`: Handles all interactions with external resources (e.g., downloading books, calling LLM APIs).
-   `pipelines/`: Contains the core logic for the Q&A generation workflow.
-   `utils/`: Provides helper functions for tasks like file I/O and response parsing.
-   `prompts_library/`: Stores the detailed prompt templates used to guide the LLM.

## Usage

1.  **Setup:**
    -   Create a `.env` file in the root directory and add your API keys (e.g., `NIM_API_KEY="..."`).
    -   Review `config.py` to customize the pipeline:
        -   **Books:** Modify `BOOKS_TO_DOWNLOAD` to add/remove Gutenberg IDs.
        -   **Q&A Generation:** Adjust `TARGET_TOTAL_PAIRS`, `MIN_QUESTIONS_PER_CHAPTER`, `MAX_QUESTIONS_PER_CHAPTER`.
        -   **LLM Settings:** Configure `RATE_LIMIT`, `MAX_RETRIES`, `TEMPERATURE`, and models (`NIM_MODELS`, `VC_MODEL`).
        -   **Question Types:** Tune `QUESTION_LAYER_DISTRIBUTION` percentages (semantic, episodic, procedural, emotional, structural).
        -   **LLM Provider:** To use a different OpenAI-compatible provider, modify `NIM_BASE_URL` and `VC_BASE_URL` in `config.py`, or add new client configurations in `services/llm_service.py` (lines 45-52).

2.  **Download Books (Optional):**
    ```bash
    python services/book_downloader.py
    ```
    *Alternatively, place `.epub` files manually in `Sources/<Book Name>/book.epub`.*

3.  **Parse Chapters:**
    ```bash
    python services/epub_parser.py
    ```

4.  **Generate Q&A Pairs:**
    ```bash
    python main.py
    ```
    The generated JSON files will be placed in an `output` directory within each book's source folder.

5.  **Convert to Training Format:**
    ```bash
    python csv_to_qa_pair.py
    ```
    Set `with_thinking=True` for reasoning-enhanced format or `False` for simple Q&A pairs.

## Example Data & Models

-   **Dataset:** [Nietzsche Q&A Dataset on Hugging Face](https://huggingface.co/datasets/phase-shake/nietzsche)
-   **Trained Models:**
    -   [Nietzsche Gemma 3 4B (Q4_K_M GGUF)](https://huggingface.co/phase-shake/nietzsche-gemma-3-4b-it-Q4_K_M-GGUF)
    -   [Nietzsche Gemma 3 1B (Q4_K_M GGUF)](https://huggingface.co/phase-shake/nietzsche-gemma-3-1b-it-Q4_K_M-GGUF)

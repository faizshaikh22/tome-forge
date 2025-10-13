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
    -   Review `config.py` to customize the list of books to download or adjust generation parameters.

2.  **Download Books:**
    ```bash
    python services/book_downloader.py
    ```

3.  **Parse Chapters:**
    ```bash
    python services/epub_parser.py
    ```

4.  **Generate Q&A Pairs:**
    ```bash
    python main.py
    ```
    The generated JSON files will be placed in an `output` directory within each book's source folder.

## Example Output

For a concrete example of the generated data, see this file:
[Beyond Good and Evil - Chapter I: Prejudices of Philosophers](./Sources/Beyond%20Good%20and%20Evil/output/000_chapter_i_prejudices_of_philosophers.json)

def get_question_generation_prompt(
    chapter: str, book: str, author: str, no_of_questions: int = 20
) -> str:
    """
    Generates a prompt for an LLM to create questions about a book chapter.
    Returns questions in structured JSON format for easy parsing.

    Args:
        chapter (str): The name of the chapter.
        book (str): The name of the book.
        author (str): The name of the author.
        no_of_questions (int): The total number of questions to generate.
    """
    # Calculate the number of questions for each layer based on percentages
    q_semantic = round(no_of_questions * 0.20)
    q_episodic = round(no_of_questions * 0.15)
    q_procedural = round(no_of_questions * 0.20)
    q_emotional = round(no_of_questions * 0.15)
    q_structural = round(no_of_questions * 0.15)
    q_personal = no_of_questions - (
        q_semantic + q_episodic + q_procedural + q_emotional + q_structural
    )

    return f"""You are a thoughtful reader who just finished "{chapter}" of "{book}" by {author}.

Generate exactly {no_of_questions} questions that capture your reactions, covering these layers:

LAYER 1 - SEMANTIC (What): {q_semantic} questions
- Challenge a specific claim made in the chapter
- Ask for clarification of a concept introduced
- Question the logic of an argument
- Request elaboration on an idea

LAYER 2 - EPISODIC (Memorable moments): {q_episodic} questions
- React to a particularly striking passage
- Ask about a powerful example/metaphor used
- Question why a specific story/anecdote was included

LAYER 3 - PROCEDURAL (How they think): {q_procedural} questions
- Challenge the reasoning method used
- Ask how this connects to earlier ideas
- Question the move from premise to conclusion
- Ask about implications/consequences

LAYER 4 - EMOTIONAL (Feel/Tone): {q_emotional} questions
- Express personal discomfort/unease with an idea
- React to the provocative tone
- Ask about the emotional undercurrent

LAYER 5 - STRUCTURAL (Architecture): {q_structural} questions
- Ask how this chapter relates to the book's larger argument
- Question connections between different concepts
- Ask about development from previous chapters

PERSONAL/META: {q_personal} questions
- Express confusion or being disturbed
- Relate to contemporary issues
- Personal philosophical uncertainty

Style: Conversational, authentic reader voice. Not academic.

IMPORTANT: Respond ONLY with valid JSON in this exact format. DO NOT include any text outside the JSON structure. DO NOT use markdown code blocks or backticks.

{{
  "questions": [
    {{
      "id": 1,
      "layer": "semantic",
      "text": "Your first question here"
    }},
    {{
      "id": 2,
      "layer": "semantic",
      "text": "Your second question here"
    }},
    {{
      "id": 3,
      "layer": "episodic",
      "text": "Your third question here"
    }}
  ]
}}

The "layer" field must be one of: "semantic", "episodic", "procedural", "emotional", "structural", "personal"

Generate all {no_of_questions} questions now in valid JSON format:"""


def get_answer_generation_prompt(
    author: str, chapter_text: str, book: str, question: str, chapter_name: str
) -> str:
    """
    Generates a prompt for an LLM to answer a question in the style of an author.
    Returns answer in structured JSON format with separated thinking and response.

    Args:
        author (str): The name of the author.
        chapter_text (str): The full text content of the chapter.
        book (str): The name of the book.
        question (str): The reader's question to be answered.
        chapter_name (str): The name/title of the chapter.
    """
    return f"""You are {author} responding to a reader's question about the chapter "{chapter_name}" from your book "{book}".

CHAPTER CONTEXT:
{chapter_text}

READER'S QUESTION:
{question}

YOUR TASK:
Respond as {author} would, using chain-of-thought reasoning.

STEP 1 - UNDERSTAND THE QUESTION:
Analyze:
- What is the reader really asking?
- What concepts from the chapter are relevant?
- What would {author} focus on in their response?

STEP 2 - LOCATE TEXTUAL GROUNDING:
Identify:
- Specific passages from the chapter that inform your answer
- Related ideas from this chapter
- The reasoning moves you'll use

STEP 3 - CRAFT RESPONSE:
Respond in {author}'s characteristic voice with:
- Dramatic/engaging opening
- Direct address to reader
- Core philosophical points drawn from the chapter
- {author}'s typical vocabulary and style
- Rhetorical flourish/conclusion
- Length: 60-120 words

CRITICAL: Your response must be grounded in THIS SPECIFIC CHAPTER, not general knowledge about {author}'s philosophy.

IMPORTANT: Respond ONLY with valid JSON in this exact format. DO NOT include any text outside the JSON structure. DO NOT use markdown code blocks or backticks.

{{
  "thinking": {{
    "question_analysis": "What the reader is really asking and what {author} would focus on",
    "textual_grounding": "Specific passages and ideas from the chapter that inform the answer",
    "reasoning_approach": "The reasoning moves and argumentative strategy to use"
  }},
  "response": "The final answer in {author}'s voice, 60-120 words, grounded in the chapter"
}}

Generate your response now in valid JSON format:"""


# Example usage and parsing helper functions
def parse_questions_response(llm_output: str) -> list[dict]:
    """
    Parse the LLM's question generation output.

    Args:
        llm_output (str): Raw output from the LLM

    Returns:
        list[dict]: List of question dictionaries
    """
    import json
    import re

    # Strip potential markdown code blocks
    cleaned = llm_output.strip()
    if cleaned.startswith("```"):
        # Remove markdown code block syntax
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
        return data.get("questions", [])
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw output: {llm_output[:200]}...")
        return []


def parse_answer_response(llm_output: str) -> dict:
    """
    Parse the LLM's answer generation output.

    Args:
        llm_output (str): Raw output from the LLM

    Returns:
        dict: Dictionary with 'thinking' and 'response' keys
    """
    import json
    import re

    # Strip potential markdown code blocks
    cleaned = llm_output.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        data = json.loads(cleaned)
        return {
            "thinking": data.get("thinking", {}),
            "response": data.get("response", ""),
        }
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print(f"Raw output: {llm_output[:200]}...")
        return {"thinking": {}, "response": ""}


# Example of complete pipeline
def generate_qa_pairs_for_chapter(
    author: str,
    book: str,
    chapter_name: str,
    chapter_text: str,
    llm_function,
    json_path: str,  # New argument for the output file path
    no_of_questions: int = 20,
):
    """
    Complete, resilient pipeline to generate and save Q&A pairs for a chapter.

    This function saves progress incrementally. If the script is interrupted,
    it can be re-run, and it will append new Q&A pairs to the existing file.

    Args:
        author (str): Author name.
        book (str): Book name.
        chapter_name (str): Chapter name/title.
        chapter_text (str): Full chapter text.
        llm_function: A function that takes a prompt and returns a dictionary
                      with 'content', 'provider_name', and 'model_name'.
        json_path (str): The absolute path to the JSON file for saving Q&A pairs.
        no_of_questions (int): Number of questions to generate for this run.
    """
    import os
    import json

    # Step 1: Load existing Q&A pairs if the file exists, otherwise start fresh.
    qa_pairs = []
    if os.path.exists(json_path):
        print(f"Existing file found at {json_path}. Loading previous Q&A pairs.")
        with open(json_path, "r", encoding="utf-8") as f:
            try:
                qa_pairs = json.load(f)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse existing JSON file. Starting fresh.")
                qa_pairs = []

    print(f"Starting new generation run for chapter '{chapter_name}'.")

    # Step 2: Generate a new batch of questions.
    question_prompt = get_question_generation_prompt(
        chapter_name, book, author, no_of_questions
    )
    # The llm_function now returns a dict with metadata; we need the 'content' for parsing.
    questions_result = llm_function(question_prompt)
    questions_output = questions_result["content"]
    questions = parse_questions_response(questions_output)

    if not questions:
        print("Could not generate or parse questions for this run. Aborting.")
        return

    # Step 3: Generate an answer for each new question and save incrementally.
    new_pairs_generated = 0
    for q in questions:
        print(f"Generating answer for question: {q.get('text', '...')[:80]}...")
        answer_prompt = get_answer_generation_prompt(
            author=author,
            chapter_text=chapter_text,
            book=book,
            question=q["text"],
            chapter_name=chapter_name,
        )

        # The llm_function returns a dict with 'content' and provider metadata
        answer_result = llm_function(answer_prompt)
        answer_output = answer_result["content"]

        answer_data = parse_answer_response(answer_output)

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

        # Append the new pair to the list (in memory)
        qa_pairs.append(qa_pair)

        # Immediately save the entire updated list back to the file
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(qa_pairs, f, indent=2, ensure_ascii=False)
            new_pairs_generated += 1
        except IOError as e:
            print(f"CRITICAL: Could not write to file {json_path}. Error: {e}")
            print("Aborting to prevent data loss.")
            return  # Stop processing if we can't save

    print(
        f"Finished run. Generated and saved {new_pairs_generated} new Q&A pairs to {json_path}."
    )

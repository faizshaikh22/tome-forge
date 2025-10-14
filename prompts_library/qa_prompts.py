# prompts_library/qa_prompts.py
import textwrap
import config


def get_question_generation_prompt(
    chapter: str,
    book: str,
    author: str,
    no_of_questions: int = config.DEFAULT_QUESTIONS_PER_CHAPTER,
) -> str:
    """Generates a prompt for an LLM to create questions about a book chapter.

    This prompt instructs the LLM to act as a thoughtful reader and generate
    a specific number of questions across several cognitive layers (semantic,
    episodic, etc.). The response is requested in a structured JSON format.

    Args:
        chapter: The title of the chapter.
        book: The title of the book.
        author: The name of the author.
        no_of_questions: The total number of questions to generate.

    Returns:
        A formatted string to be used as a prompt for the LLM.
    """
    dist = config.QUESTION_LAYER_DISTRIBUTION
    q_semantic = round(no_of_questions * dist["semantic"])
    q_episodic = round(no_of_questions * dist["episodic"])
    q_procedural = round(no_of_questions * dist["procedural"])
    q_emotional = round(no_of_questions * dist["emotional"])
    q_structural = round(no_of_questions * dist["structural"])
    q_personal = no_of_questions - (
        q_semantic + q_episodic + q_procedural + q_emotional + q_structural
    )

    return textwrap.dedent(f"""\
        You are a thoughtful reader who just finished "{chapter}" of "{book}" by {author}.

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
    """Generates a prompt for an LLM to answer a question in an author's style.

    This prompt instructs the LLM to embody the specified author and respond to
    a reader's question. It provides the full chapter text for context and
    requires the LLM to use a chain-of-thought process, grounding its answer
    firmly in the provided text. The response is requested in a structured
    JSON format.

    Args:
        author: The name of the author to emulate.
        chapter_text: The full text of the chapter for context.
        book: The title of the book.
        question: The reader's question to be answered.
        chapter_name: The title of the chapter.

    Returns:
        A formatted string to be used as a prompt for the LLM.
    """
    return textwrap.dedent(f"""\
        You are {author} responding to a reader's question about the chapter "{chapter_name}" from your book "{book}".

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

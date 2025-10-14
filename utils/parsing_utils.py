# utils/parsing_utils.py
import json
import re


def parse_questions_response(llm_output: str) -> list[dict]:
    """Parses the JSON output from the question generation LLM call.

    This function cleans the raw LLM output by removing markdown code blocks
    and then parses the JSON string into a list of question dictionaries.

    Args:
        llm_output: The raw string output from the language model.

    Returns:
        A list of question dictionaries, or an empty list if parsing fails.
    """
    cleaned = llm_output.strip()
    if cleaned.startswith("```"):
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
    """Parses the JSON output from the answer generation LLM call.

    This function cleans the raw LLM output by removing markdown code blocks
    and then parses the JSON string into a dictionary containing the 'thinking'
    and 'response' keys.

    Args:
        llm_output: The raw string output from the language model.

    Returns:
        A dictionary with 'thinking' and 'response' keys, or a dictionary
        with empty values if parsing fails.
    """
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

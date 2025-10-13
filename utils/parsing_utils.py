# utils/parsing_utils.py
import json
import re


def parse_questions_response(llm_output: str) -> list[dict]:
    """
    Parse the LLM's question generation output.
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
    """
    Parse the LLM's answer generation output.
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

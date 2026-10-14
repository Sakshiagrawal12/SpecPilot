import json
from typing import Any, Dict


def extract_json(text: str) -> Dict[str, Any]:

    text = text.strip()

    if text.startswith("```"):

        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:

        parsed = json.loads(text)

    except json.JSONDecodeError as e:

        print("JSON PARSING ERROR:", str(e))
        print("LLM response:", text)

        raise RuntimeError(f"LLM returned invalid JSON: {str(e)}")

    if not isinstance(parsed, dict):

        raise RuntimeError(f"LLM returned valid JSON but not an object: {repr(parsed)[:200]}")

    return parsed
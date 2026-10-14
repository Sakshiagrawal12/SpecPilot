from typing import Dict, Any,Optional
import json
import re

from .config import (
    ALL_FIELDS,
    INTERVIEW_FIELDS,
    QUESTION_SIGNAL_PATTERNS,
    FIELD_CONFIDENCE_THRESHOLDS,
)


# =========================================================
# CONFIDENCE THRESHOLD
# =========================================================

def _threshold_for(field_name: str) -> float:

    return FIELD_CONFIDENCE_THRESHOLDS.get(
        field_name,
        0.5,
    )


# =========================================================
# EMPTY REQUIREMENTS
# =========================================================

def create_empty_requirements() -> Dict[str, Dict[str, Any]]:

    return {
        field: {
            "value": None,
            "status": "MISSING",
            "confidence": 0.0,
            "attempts": 0,
            "question_count": 0,
        }
        for field in ALL_FIELDS
    }


# =========================================================
# JSON EXTRACTION
# =========================================================

def _extract_json(text: str) -> Dict[str, Any]:

    if not text:
        raise RuntimeError(
            "LLM returned an empty response."
        )

    text = text.strip()

    # -----------------------------------------------------
    # Remove markdown code fences
    # -----------------------------------------------------

    if text.startswith("```"):

        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

    try:

        parsed = json.loads(text)

    except json.JSONDecodeError as e:

        print("==========================================")
        print("JSON PARSING ERROR")
        print("==========================================")
        print("LLM response:")
        print(text)
        print("==========================================")

        raise RuntimeError(
            f"LLM returned invalid JSON: {str(e)}"
        )

    # -----------------------------------------------------
    # Ensure object
    # -----------------------------------------------------

    if not isinstance(parsed, dict):

        print("==========================================")
        print("JSON SHAPE ERROR")
        print("==========================================")
        print(
            "Expected object but received:",
            type(parsed),
        )
        print("Response:", repr(parsed))
        print("==========================================")

        raise RuntimeError(
            "LLM returned valid JSON but not an object."
        )

    return parsed


# =========================================================
# FIND NEXT MISSING FIELD
# =========================================================

def _find_next_missing_field(
    requirements: Dict[str, Dict[str, Any]]
):

    for field in INTERVIEW_FIELDS:

        field_data = requirements.get(
            field,
            {},
        )

        value = field_data.get("value")

        status = field_data.get(
            "status",
            "MISSING",
        )

        # -------------------------------------------------
        # Explicitly skipped fields are considered handled
        # -------------------------------------------------

        if status == "SKIPPED":
            continue

        # -------------------------------------------------
        # Missing value
        # -------------------------------------------------

        if value is None:
            return field

        # -------------------------------------------------
        # Empty string
        # -------------------------------------------------

        if isinstance(value, str) and not value.strip():
            return field

    return None


# =========================================================
# BUILD CONTEXT SUMMARY
# =========================================================
def _build_context_summary(
    project_name: str,
    requirements: Dict[str, Any],
    exclude_field: Optional[str] = None,
    document_summary: str = "",
) -> str:
    # -------------------------------------------------------------
    # 1. Type Safety Guard: Ensure requirements is a dictionary
    # -------------------------------------------------------------
    if isinstance(requirements, str):
        try:
            requirements = json.loads(requirements)
        except Exception:
            requirements = {}

    if not isinstance(requirements, dict):
        requirements = {}

    lines = []

    # Add Project Name once
    if project_name:
        lines.append(f"Project name: {project_name}")

    # Add Uploaded Document Context
    if document_summary:
        lines.append(f"Uploaded document context: {document_summary}")

    # -------------------------------------------------------------
    # 2. Iterate and format interview fields
    # -------------------------------------------------------------
    for field in INTERVIEW_FIELDS:
        if field == exclude_field:
            continue

        field_data = requirements.get(field, {})

        # Ensure field_data is a dictionary before accessing .get()
        if not isinstance(field_data, dict):
            field_data = {"value": field_data, "status": "PROVIDED"}

        value = field_data.get("value")
        status = field_data.get("status", "MISSING")

        # Skip missing / blank fields
        if value is None:
            continue

        if isinstance(value, str) and not value.strip():
            continue

        # Include skipped fields explicitly
        if status == "SKIPPED":
            lines.append(
                f"{field.replace('_', ' ').title()}: Not specified by the user."
            )
            continue

        lines.append(f"{field.replace('_', ' ').title()}: {value}")

    if not lines:
        return "No other project information has been collected yet."
    return "\n".join(lines)


# =========================================================
# FIELD STRUGGLE MEMORY
# =========================================================

def _build_field_memory(
    field_state: Dict[str, Any]
) -> str:

    question_count = field_state.get(
        "question_count",
        0,
    )

    attempts = field_state.get(
        "attempts",
        0,
    )

    if question_count == 0 and attempts == 0:

        return (
            "No prior struggle on this field."
        )

    parts = []

    if question_count > 0:

        parts.append(
            f"The user has asked "
            f"{question_count} clarification "
            f"question(s) about this field already. "
            f"They may need a concrete explanation "
            f"or example rather than the same definition."
        )

    if attempts > 0:

        parts.append(
            f"The user has given {attempts} "
            f"answer attempt(s) that were not "
            f"sufficiently clear for this field."
        )

    return " ".join(parts)


# =========================================================
# QUESTION DETECTION
# =========================================================

def _looks_like_question(
    text: str
) -> bool:

    if not text:
        return False

    lowered = text.lower().strip()

    return any(
        re.search(
            pattern,
            lowered,
        )
        for pattern in QUESTION_SIGNAL_PATTERNS
    )


# =========================================================
# CLARIFICATION TYPE DETECTION
# =========================================================

def detect_clarification_type(
    text: str
) -> str:

    if not text:
        return "confused"

    lowered = text.lower().strip()

    # -----------------------------------------------------
    # EXAMPLE
    # -----------------------------------------------------

    example_patterns = [
        r"\bexample\b",
        r"\bexamples\b",
        r"\bgive me an example\b",
        r"\bshow me an example\b",
        r"\bcan you give.*example\b",
        r"\bwhat.*example\b",
        r"\bsuggest.*example\b",
    ]

    if any(
        re.search(
            pattern,
            lowered,
        )
        for pattern in example_patterns
    ):

        return "example"

    # -----------------------------------------------------
    # MORE DETAIL
    # -----------------------------------------------------

    more_detail_patterns = [
        r"explain more",
        r"explain this more",
        r"can you explain more",
        r"tell me more",
        r"more detail",
        r"more details",
        r"elaborate",
        r"explain.*detail",
        r"explain.*better",
    ]

    if any(
        re.search(
            pattern,
            lowered,
        )
        for pattern in more_detail_patterns
    ):

        return "more_detail"

    # -----------------------------------------------------
    # WHY
    # -----------------------------------------------------

    why_patterns = [
        r"^why\b",
        r"\bwhy are you asking\b",
        r"\bwhy do you need\b",
        r"\bwhy is this needed\b",
        r"\bwhat.*purpose\b",
        r"\bwhy.*information\b",
    ]

    if any(
        re.search(
            pattern,
            lowered,
        )
        for pattern in why_patterns
    ):

        return "why"

    # -----------------------------------------------------
    # SIMPLE CONFUSION
    # -----------------------------------------------------

    confusion_patterns = [
        r"what do you mean",
        r"what does this mean",
        r"i don't understand",
        r"i dont understand",
        r"i didn't understand",
        r"i didnt understand",
        r"i don't get it",
        r"i dont get it",
        r"i didn't get it",
        r"i didnt get it",
        r"not clear",
        r"confused",
    ]

    if any(
        re.search(
            pattern,
            lowered,
        )
        for pattern in confusion_patterns
    ):

        return "confused"

    return "confused"


# =========================================================
# CLARIFICATION ATTEMPT
# =========================================================

def get_clarification_attempt(
    state,
    field: str,
) -> int:

    attempts = state.get(
        "clarification_attempts",
        {},
    )

    return attempts.get(
        field,
        0,
    )


# =========================================================
# INCREMENT CLARIFICATION ATTEMPT
# =========================================================

def increment_clarification_attempt(
    state,
    field: str,
) -> Dict[str, int]:

    attempts = dict(
        state.get(
            "clarification_attempts",
            {},
        )
    )

    attempts[field] = (
        attempts.get(field, 0) + 1
    )

    return attempts


# =========================================================
# SKIP DETECTION
# =========================================================

def is_skip_message(
    message: str
) -> bool:

    if not message:
        return False

    text = message.strip().lower()

    explicit_skip_phrases = [
        "skip",
        "skip this",
        "skip this field",
        "skip this question",
        "not applicable",
        "n/a",
        "nothing else",
        "nothing to add",
        "no additional instructions",
        "i have no additional instructions",
        "there are no additional instructions",
        "no instructions",
    ]

    return any(
        phrase == text
        for phrase in explicit_skip_phrases
    )


# =========================================================
# GENERATE-FOR-ME DETECTION
# =========================================================

def is_generate_for_me_message(
    message: str
) -> bool:

    if not message:
        return False

    text = message.strip().lower()

    generate_phrases = [
        "write it for me",
        "write this for me",
        "generate it for me",
        "generate this for me",
        "fill it for me",
        "fill this for me",
        "you write it",
        "you can write it",
        "write it according to you",
        "write this according to you",
        "according to you",
        "suggest it for me",
        "suggest one",
        "suggest something",
        "suggest for my project",
        "you decide",
        "decide for me",
        "fill it by yourself",
        "fill it by your own",
        "do it for me",
        "create it for me",
        "make one for me",
        "give me one",
    ]

    return any(
        phrase in text
        for phrase in generate_phrases
    )


# =========================================================
# CONFIRMATION DETECTION
# =========================================================

def is_confirmation_message(message: str) -> bool:
    """Checks if message is accepting a pending suggestion."""
    normalized = message.lower().strip()
    acceptance_keywords = [
        "yes", "yeah", "yep", "sure", "okay", "ok", "sounds good",
        "looks good", "use this", "use that", "go with this", "accept",
        "use it", "can use this", "use option", "that works", "go ahead"
    ]
    return any(kw in normalized for kw in acceptance_keywords)

# =========================================================
# REJECTION DETECTION
# =========================================================

def is_rejection_message(message: str) -> bool:
    """Checks if message is rejecting a pending suggestion."""
    normalized = message.lower().strip()
    rejection_keywords = [
        "no", "nope", "dont use", "don't use", "reject", "change it",
        "give another", "try again", "not this", "different one"
    ]
    return any(kw in normalized for kw in rejection_keywords)


def is_generate_for_me_message(message: str) -> bool:
    """Checks if message is requesting the AI to generate a suggestion."""
    normalized = message.lower().strip()
    generate_keywords = [
        "write it for me", "suggest one", "according to my project",
        "according to you", "generate for me", "can you give",
        "give according", "give me according", "what do you suggest",
        "recommend one", "create one for me"
    ]
    return any(kw in normalized for kw in generate_keywords)


# =========================================================
# DOCUMENT-AWARE REQUIREMENT HELPERS
# =========================================================

def get_document_context(
    state
) -> str:

    summary = state.get(
        "document_summary",
        ""
    )

    if not summary:
        return "No document was uploaded."

    return summary


def get_document_filled_fields(
    state
) -> list:

    return state.get(
        "document_filled_fields",
        []
    )


def is_document_provided(
    requirements,
    field_name: str
) -> bool:

    field = requirements.get(
        field_name,
        {}
    )

    return (
        field.get("source") == "document"
        and field.get("value") is not None
    )


def field_has_value(
    requirements,
    field_name: str
) -> bool:

    field = requirements.get(
        field_name,
        {}
    )

    value = field.get("value")

    if value is None:
        return False

    if isinstance(value, str):
        return bool(value.strip())

    if isinstance(value, list):
        return len(value) > 0

    return True

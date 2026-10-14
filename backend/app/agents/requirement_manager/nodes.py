# app/agents/requirement_manager/nodes.py

from typing import Any, Dict

from .state import RequirementState

from .config import (
    ALL_FIELDS,
    INTERVIEW_FIELDS,
    QUESTIONS,
    MAX_CLARIFICATION_ATTEMPTS,
    FIELD_EXPLANATIONS,
)

from .utils import (
    create_empty_requirements,
    _find_next_missing_field,
    _build_context_summary,
    _build_field_memory,
    _threshold_for,
    detect_clarification_type,
    is_skip_message,
    is_generate_for_me_message,
    is_confirmation_message,
    is_rejection_message,
    get_clarification_attempt,
    increment_clarification_attempt,
)

from .agents.evaluator import evaluate_project

from .agents.extraction_agent import (
    RequirementExtractionAgent,
)

from app.ai.llm import llm

from .agents.question_planner import (
    RequirementQuestionPlanner,
)
from app.agents.requirement_manager.agents.document_agent import document_agent_node
# =========================================================
# AGENT INSTANCE
# =========================================================

extraction_agent = RequirementExtractionAgent()
question_planner = RequirementQuestionPlanner()

# =========================================================
# HELPER
# =========================================================

def _field_label(field_name: str) -> str:

    return field_name.replace(
        "_",
        " ",
    ).strip().title()


def _get_question_text(
    field_name: str,
) -> str:

    question_data = QUESTIONS.get(
        field_name,
        {},
    )

    question_text = question_data.get(
        "text",
        "",
    )

    example = question_data.get(
        "example",
        "",
    )

    if example:

        return (
            f"{question_text}\n\n"
            f"{example}"
        )

    return question_text


def _ensure_field_state(
    requirements: Dict[str, Any],
    field_name: str,
) -> Dict[str, Any]:

    return requirements.setdefault(
        field_name,
        {
            "value": None,
            "status": "MISSING",
            "confidence": 0.0,
            "attempts": 0,
            "question_count": 0,
        },
    )


# =========================================================
# MESSAGE CLASSIFICATION
# =========================================================

def classify_message(
    user_message: str,
    current_field: str,
    context_summary: str,
    field_memory: str,
) -> Dict[str, Any]:

    """
    Classifies a normal user message.

    Explicit commands such as skip/generate/confirmation
    are handled outside this function.

    This function handles:

        answer
        question
        correction
        off_track
    """

    prompt = f"""
You are the intent classifier for a conversational
software-project requirements assistant.

The assistant is currently collecting this field:

CURRENT FIELD:
{current_field}

CURRENT PROJECT CONTEXT:
{context_summary}

FIELD MEMORY:
{field_memory}

USER MESSAGE:
{user_message}

Classify the message into exactly ONE of these categories:

1. answer
   The user is providing information that can answer
   the current requirement field.

2. question
   The user is asking what the field means, asking for
   clarification, or saying they do not understand.

3. correction
   The user wants to change information they previously
   provided.

4. off_track
   The message is unrelated to the project requirement
   conversation.

IMPORTANT:

A message can contain question-like wording but still
be an ANSWER.

For example:

"My fitness project mainly focuses on helping people
maintain fitness and a healthy lifestyle."

This is an answer, not a question.

Another example:

"For my fitness project, the goal is to help users
exercise regularly."

This is an answer.

A message such as:

"What do you mean by business objective?"

is a question.

A message such as:

"I meant college students, not working professionals."

is a correction.

Return ONLY valid JSON:

{{
    "type": "answer | question | correction | off_track",
    "field": null,
    "new_value": null,
    "reason": "short explanation"
}}

If the message is not a correction, keep field and
new_value as null.
"""

    response = llm.generate(prompt)

    content = response.strip()

    # -----------------------------------------------------
    # Parse JSON
    # -----------------------------------------------------

    from .utils import _extract_json

    try:

        result = _extract_json(
            content
        )

    except Exception:

        # Safe fallback:
        # treat unclear input as an answer and let the
        # extraction agent decide whether it is useful.

        return {
            "type": "answer",
            "field": None,
            "new_value": None,
            "reason": "Classifier fallback",
        }

    # -----------------------------------------------------
    # Validate classification
    # -----------------------------------------------------

    allowed_types = {
        "answer",
        "question",
        "correction",
        "off_track",
    }

    message_type = result.get(
        "type",
        "answer",
    )

    if message_type not in allowed_types:

        message_type = "answer"

    return {
        "type": message_type,
        "field": result.get("field"),
        "new_value": result.get("new_value"),
        "reason": result.get(
            "reason",
            "",
        ),
    }


# =========================================================
# NODE 1
# CLASSIFY AND ROUTE
# =========================================================

def classify_and_route(state: RequirementState) -> Dict[str, Any]:
    user_message = state.get("user_message", "").strip()
    requirements = state.get("requirements") or create_empty_requirements()
    project_name = state.get("project_name")

    if project_name:
        project_field = requirements.setdefault(
            "project_name",
            {"value": None, "status": "MISSING", "confidence": 0.0},
        )
        project_field["value"] = project_name
        project_field["status"] = "PROVIDED"
        project_field["confidence"] = 1.0

    if not user_message:
        next_field = _find_next_missing_field(requirements)
        return {
            "requirements": requirements,
            "current_field": next_field,
            "message_type": "no_op",
        }

    # -----------------------------------------------------
    # 1. CHECK PENDING GENERATED CONFIRMATION FIRST
    # -----------------------------------------------------
    if state.get("pending_confirmation", False):
        if is_confirmation_message(user_message):
            return {
                "requirements": requirements,
                "user_message": user_message,
                "current_field": state.get("pending_generated_field"),
                "message_type": "confirmation",
            }

        if is_rejection_message(user_message):
            return {
                "requirements": requirements,
                "user_message": user_message,
                "current_field": state.get("pending_generated_field"),
                "message_type": "rejection",
            }

        # If user provided a explicit new answer instead of yes/no
        return {
            "requirements": requirements,
            "user_message": user_message,
            "current_field": state.get("pending_generated_field"),
            "message_type": "correction",
            "correction_field": state.get("pending_generated_field"),
            "correction_value": user_message,
        }

    # -----------------------------------------------------
    # 2. CHECK EXPLICIT INTENTS
    # -----------------------------------------------------
    current_field = state.get("current_field") or _find_next_missing_field(requirements)

    if not current_field:
        return {
            "requirements": requirements,
            "current_field": None,
            "message_type": "no_op",
        }

    if is_skip_message(user_message):
        return {
            "requirements": requirements,
            "current_field": current_field,
            "user_message": user_message,
            "message_type": "skip",
        }

    if is_generate_for_me_message(user_message):
        return {
            "requirements": requirements,
            "current_field": current_field,
            "user_message": user_message,
            "message_type": "generate_for_me",
        }

    # -----------------------------------------------------
    # 3. RUN LLM CLASSIFICATION FOR NORMAL MESSAGES
    # -----------------------------------------------------
    field_state = _ensure_field_state(requirements, current_field)
    field_memory = _build_field_memory(field_state)
    context_summary = _build_context_summary(
        project_name=project_name or "",
        requirements=requirements,
        exclude_field=current_field,
    )

    classification = classify_message(
        user_message=user_message,
        current_field=current_field,
        context_summary=context_summary,
        field_memory=field_memory,
    )

    message_type = classification.get("type", "answer")

    if message_type == "correction":
        correction_field = classification.get("field") or current_field
        if correction_field not in ALL_FIELDS:
            correction_field = current_field

        return {
            "requirements": requirements,
            "current_field": current_field,
            "user_message": user_message,
            "message_type": "correction",
            "correction_field": correction_field,
            "correction_value": classification.get("new_value"),
        }

    return {
        "requirements": requirements,
        "current_field": current_field,
        "user_message": user_message,
        "message_type": message_type,
    }

# =========================================================
# ROUTE AFTER CLASSIFICATION
# =========================================================

def route_after_classification(state: RequirementState) -> str:
    message_type = state.get("message_type", "answer")

    if message_type == "confirmation":
        return "confirmation"

    if message_type == "rejection":
        return "rejection"

    if message_type == "correction":
        return "correction"

    if message_type == "question":
        return "question"

    if message_type == "generate_for_me":
        return "generate_for_me"

    if message_type == "skip":
        return "skip"

    return "extract"


# =========================================================
# NODE 2
# HANDLE CORRECTION
# =========================================================

def handle_correction(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    target_field = (
        state.get("correction_field")
        or state.get("current_field")
    )

    if not target_field:

        return {
            "requirements": requirements,
            "agent_response": (
                "I couldn't determine which "
                "requirement you want to change."
            ),
            "next_action": "wait_for_user",
        }

    new_value = state.get(
        "correction_value"
    )

    # -----------------------------------------------------
    # If classifier did not extract a new value,
    # use the user's complete message as the correction.
    # -----------------------------------------------------

    if not new_value:

        new_value = state.get(
            "user_message",
            "",
        ).strip()

    field_state = _ensure_field_state(
        requirements,
        target_field,
    )

    # -----------------------------------------------------
    # Store correction
    # -----------------------------------------------------

    if new_value:

        field_state["value"] = new_value
        field_state["status"] = "PROVIDED"
        field_state["confidence"] = 0.8
        field_state["attempts"] = 0
        field_state["question_count"] = 0

        # Clear old clarification state
        clarification_attempts = dict(
            state.get(
                "clarification_attempts",
                {},
            )
        )

        clarification_attempts[
            target_field
        ] = 0

        next_field = (
            _find_next_missing_field(
                requirements
            )
        )

        if next_field:

            return {
                "requirements": requirements,
                "current_field": next_field,
                "clarification_attempts":
                    clarification_attempts,
                "agent_response": (
                    f"Got it — I updated "
                    f"{_field_label(target_field)} "
                    f"to:\n\n"
                    f"{new_value}\n\n"
                    f"{_get_question_text(next_field)}"
                ),
                "next_action": "wait_for_user",
            }

        return {
            "requirements": requirements,
            "current_field": None,
            "clarification_attempts":
                clarification_attempts,
            "agent_response": (
                f"Got it — I updated "
                f"{_field_label(target_field)} "
                f"to:\n\n"
                f"{new_value}\n\n"
                f"I now have all the required "
                f"project information."
            ),
            "next_action": "generate_prd",
        }

    # -----------------------------------------------------
    # No usable correction
    # -----------------------------------------------------

    return {
        "requirements": requirements,
        "current_field": target_field,
        "agent_response": (
            f"No problem. Tell me what you want "
            f"to change about "
            f"{_field_label(target_field)}."
        ),
        "next_action": "wait_for_user",
    }


# =========================================================
# NODE 3
# HANDLE QUESTION / CLARIFICATION
# =========================================================

def handle_question(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    current_field = state.get(
        "current_field"
    )

    if not current_field:

        return {
            "requirements": requirements,
            "agent_response": (
                "All required project information "
                "has already been collected."
            ),
            "next_action": "generate_prd",
        }

    field_state = _ensure_field_state(
        requirements,
        current_field,
    )

    # -----------------------------------------------------
    # Track clarification attempts
    # -----------------------------------------------------

    clarification_attempts = (
        increment_clarification_attempt(
            state,
            current_field,
        )
    )

    clarification_count = (
        clarification_attempts.get(
            current_field,
            1,
        )
    )

    # Keep field-level count too
    field_state["question_count"] = (
        clarification_count
    )

    user_message = state.get(
        "user_message",
        "",
    ).strip()

    clarification_type = (
        detect_clarification_type(
            user_message
        )
    )

    project_name = (
        state.get("project_name")
        or "your project"
    )

    explanation = FIELD_EXPLANATIONS.get(
        current_field,
        "This field helps define your project requirements.",
    )

    context_summary = _build_context_summary(
        project_name=project_name,
        requirements=requirements,
        exclude_field=current_field,
    )

    question_text = _get_question_text(
        current_field
    )

    # =====================================================
    # FIRST CLARIFICATION
    # =====================================================

    if clarification_count == 1:

        if clarification_type == "example":

            example = generate_contextual_example(
                field_name=current_field,
                project_name=project_name,
                context_summary=context_summary,
            )

            response = (
                f"Sure. For {project_name}, "
                f"one possible example is:\n\n"
                f"{example}\n\n"
                f"You can use this as an idea, "
                f"or give me your own answer."
            )

        elif clarification_type == "why":

            response = (
                generate_short_explanation(
                    field_name=current_field,
                    project_name=project_name,
                    context_summary=context_summary,
                    explanation_type="why",
                )
            )

        else:

            response = (
                f"No problem. {explanation}"
            )

    # =====================================================
    # SECOND CLARIFICATION
    # =====================================================

    elif clarification_count == 2:

        example = generate_contextual_example(
            field_name=current_field,
            project_name=project_name,
            context_summary=context_summary,
        )

        response = (
            f"Let me explain it using "
            f"{project_name} as context.\n\n"
            f"{explanation}\n\n"
            f"For example, you could describe it like:\n"
            f"{example}\n\n"
            f"This is only an example — "
            f"you can give your own answer."
        )

    # =====================================================
    # THIRD OR LATER CLARIFICATION
    # =====================================================

    else:

        response = (
            f"I can also suggest an answer for "
            f"{_field_label(current_field)} "
            f"based on what you've told me so far.\n\n"
            f"If you'd like that, say "
            f"\"write it for me\" or "
            f"\"suggest one\"."
        )

    # -----------------------------------------------------
    # Ask original question again
    # -----------------------------------------------------

    final_response = (
        f"{response}\n\n"
        f"{question_text}"
    )

    return {
        "requirements": requirements,
        "current_field": current_field,
        "clarification_attempts":
            clarification_attempts,
        "agent_response": final_response,
        "next_action": "wait_for_user",
    }


# =========================================================
# CONTEXTUAL EXAMPLE
# =========================================================

def generate_contextual_example(
    field_name: str,
    project_name: str,
    context_summary: str,
) -> str:

    field_meanings = {

        "category":
            "the broad domain or type of project",

        "business_objective":
            "the main goal the project is trying to achieve",

        "problem_statement":
            "the specific problem or pain point the project solves",

        "target_users":
            "the people who will actually use the project",

        "expected_features":
            "the main capabilities the project should provide",

        "technology_preferences":
            "technologies, frameworks, or tools the user prefers",

        "timeline":
            "the expected development timeframe",

        "additional_instructions":
            "any additional constraints or requirements",
    }

    field_meaning = field_meanings.get(
        field_name,
        "the project requirement",
    )

    prompt = f"""
You are helping a user answer the
"{field_name}" requirement field.

PROJECT:
{project_name}

KNOWN PROJECT INFORMATION:
{context_summary}

FIELD:
{field_name}

FIELD MEANING:
{field_meaning}

Generate ONE short example answer.

Rules:
- Maximum 2 sentences.
- Use only information supported by the context.
- Do not invent specific requirements.
- Do not claim the example is confirmed.
- The example is only a suggestion.
- Return plain text only.
"""

    response = llm.generate(
        prompt
    )

    return response.strip()


# =========================================================
# SHORT EXPLANATION
# =========================================================

def generate_short_explanation(
    field_name: str,
    project_name: str,
    context_summary: str,
    explanation_type: str,
) -> str:

    if explanation_type == "why":

        return (
            f"We need {_field_label(field_name)} "
            f"so I can understand an important part "
            f"of {project_name} and use it when "
            f"building the project's requirements."
        )

    return FIELD_EXPLANATIONS.get(
        field_name,
        "This information helps define your project.",
    )


# =========================================================
# NODE 4
# GENERATE FOR ME
# =========================================================

def generate_for_me(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    current_field = state.get(
        "current_field"
    )

    if not current_field:

        return {
            "requirements": requirements,
            "agent_response": (
                "I already have all the required "
                "project information."
            ),
            "next_action": "generate_prd",
        }

    project_name = (
        state.get("project_name")
        or "your project"
    )

    context_summary = _build_context_summary(
        project_name=project_name,
        requirements=requirements,
        exclude_field=current_field,
    )

    prompt = f"""
You are a project requirements assistant.

The user has asked you to suggest/write an answer
for the current requirement field.

PROJECT:
{project_name}

CURRENT FIELD:
{current_field}

KNOWN PROJECT INFORMATION:
{context_summary}

Generate ONE reasonable candidate answer for this field.

Rules:
- Use only the information already known.
- Do not invent unsupported project requirements.
- Keep the answer specific enough to be useful.
- Do not present it as confirmed.
- Maximum 3 sentences.
- Return only the candidate answer.
"""

    response = llm.generate(
        prompt
    )

    generated_value = (
        response.strip()
    )

    if not generated_value:

        return {
            "requirements": requirements,
            "current_field": current_field,
            "agent_response": (
                "I couldn't generate a useful "
                "suggestion from the information "
                "I have so far. Please describe "
                "this field in your own words."
            ),
            "next_action": "wait_for_user",
        }

    # -----------------------------------------------------
    # IMPORTANT:
    # Do NOT store it yet.
    # Wait for user confirmation.
    # -----------------------------------------------------

    return {
        "requirements": requirements,
        "current_field": current_field,

        "pending_generated_field":
            current_field,

        "pending_generated_value":
            generated_value,

        "pending_confirmation":
            True,

        "agent_response": (
            f"Based on what you've told me, "
            f"I'd suggest:\n\n"
            f"{generated_value}\n\n"
            f"Would you like me to use this?"
        ),

        "next_action": "wait_for_user",
    }


# =========================================================
# NODE 5
# HANDLE SKIP
# =========================================================

def handle_skip(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    current_field = state.get(
        "current_field"
    )

    if not current_field:

        return {
            "requirements": requirements,
            "next_action": "generate_prd",
        }

    field_state = _ensure_field_state(
        requirements,
        current_field,
    )

    # -----------------------------------------------------
    # Explicitly mark as skipped
    # -----------------------------------------------------

    field_state["value"] = None
    field_state["status"] = "SKIPPED"
    field_state["confidence"] = 0.0
    field_state["attempts"] = 0
    field_state["question_count"] = 0

    # -----------------------------------------------------
    # Clear clarification history
    # -----------------------------------------------------

    clarification_attempts = dict(
        state.get(
            "clarification_attempts",
            {},
        )
    )

    clarification_attempts[
        current_field
    ] = 0

    return {
        "requirements": requirements,
        "current_field": current_field,
        "clarification_attempts":
            clarification_attempts,
        "agent_response": (
            f"Okay, I'll leave "
            f"{_field_label(current_field)} "
            f"unspecified."
        ),
        "next_action": "wait_for_user",
    }


# =========================================================
# NODE 6
# ACCEPT GENERATED VALUE
# =========================================================

def accept_generated_value(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    field_name = state.get(
        "pending_generated_field"
    )

    generated_value = state.get(
        "pending_generated_value"
    )

    if not field_name or not generated_value:

        return {
            "requirements": requirements,
            "pending_confirmation": False,
            "agent_response": (
                "There is no generated suggestion "
                "waiting for confirmation."
            ),
            "next_action": "wait_for_user",
        }

    field_state = _ensure_field_state(
        requirements,
        field_name,
    )

    # -----------------------------------------------------
    # Store generated value
    # -----------------------------------------------------

    field_state["value"] = (
        generated_value
    )

    field_state["status"] = "PROVIDED"

    field_state["confidence"] = 0.75

    field_state["attempts"] = 0

    field_state["question_count"] = 0

    # -----------------------------------------------------
    # Clear pending generated state
    # -----------------------------------------------------

    clarification_attempts = dict(
        state.get(
            "clarification_attempts",
            {},
        )
    )

    clarification_attempts[
        field_name
    ] = 0

    next_field = (
        _find_next_missing_field(
            requirements
        )
    )

    if next_field:

        return {
            "requirements": requirements,
            "current_field": next_field,
            "pending_generated_field": None,
            "pending_generated_value": None,
            "pending_confirmation": False,
            "clarification_attempts":
                clarification_attempts,
            "agent_response": (
                f"Great — I'll use that for "
                f"{_field_label(field_name)}.\n\n"
                f"{_get_question_text(next_field)}"
            ),
            "next_action": "wait_for_user",
        }

    return {
        "requirements": requirements,
        "current_field": None,
        "pending_generated_field": None,
        "pending_generated_value": None,
        "pending_confirmation": False,
        "clarification_attempts":
            clarification_attempts,
        "agent_response": (
            f"Great — I'll use that for "
            f"{_field_label(field_name)}. "
            f"I now have all the required "
            f"project information."
        ),
        "next_action": "generate_prd",
    }


# =========================================================
# NODE 7
# REJECT GENERATED VALUE
# =========================================================

def reject_generated_value(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    current_field = (
        state.get(
            "pending_generated_field"
        )
        or state.get(
            "current_field"
        )
    )

    # -----------------------------------------------------
    # Clear generated candidate
    # -----------------------------------------------------

    return {
        "requirements": requirements,
        "current_field": current_field,
        "pending_generated_field": None,
        "pending_generated_value": None,
        "pending_confirmation": False,
        "agent_response": (
            f"No problem. I won't use that suggestion. "
            f"Tell me what you'd like for "
            f"{_field_label(current_field)}."
        ),
        "next_action": "wait_for_user",
    }


# =========================================================
# NODE 8
# EXTRACT + SCORE
# =========================================================

def extract_and_score(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    current_field = state.get(
        "current_field"
    )

    user_message = (
        state.get(
            "user_message",
            "",
        )
        .strip()
    )

    if not current_field or not user_message:

        return {
            "requirements": requirements,
            "current_field": current_field,
            "extraction_outcome": "no_op",
        }

    field_state = _ensure_field_state(
        requirements,
        current_field,
    )

    field_memory = _build_field_memory(
        field_state
    )

    context_summary = _build_context_summary(
        project_name=state.get(
            "project_name",
            "",
        ),
        requirements=requirements,
        exclude_field=current_field,
    )

    # -----------------------------------------------------
    # Extraction agent
    # -----------------------------------------------------

    extraction = extraction_agent.extract(
        user_message=user_message,
        current_field=current_field,
        context_summary=context_summary,
        field_memory=field_memory,
    )

    return {
        "requirements": requirements,
        "current_field": current_field,

        "extracted_value":
            extraction.get("value"),

        "extracted_confidence":
            extraction.get(
                "confidence",
                0.0,
            ),

        "extracted_reason":
            extraction.get(
                "reason",
                "",
            ),

        "extracted_off_track":
            extraction.get(
                "off_track",
                False,
            ),

        "extracted_off_track_reason":
            extraction.get(
                "off_track_reason",
                "",
            ),

        "attempts_so_far":
            field_state.get(
                "attempts",
                0,
            ),
    }


# =========================================================
# ROUTE AFTER EXTRACTION
# =========================================================

def route_after_extraction(
    state: RequirementState,
) -> str:

    # -----------------------------------------------------
    # Nothing to process
    # -----------------------------------------------------

    if state.get(
        "extraction_outcome"
    ) == "no_op":

        return "evaluate"

    # -----------------------------------------------------
    # Off-track
    # -----------------------------------------------------

    if state.get(
        "extracted_off_track",
        False,
    ):

        return "off_track"

    value = state.get(
        "extracted_value"
    )

    is_blank = (
        value is None
        or (
            isinstance(value, str)
            and not value.strip()
        )
    )

    attempts = state.get(
        "attempts_so_far",
        0,
    )

    # -----------------------------------------------------
    # Blank answer
    # -----------------------------------------------------

    if is_blank:

        if attempts >= MAX_CLARIFICATION_ATTEMPTS:

            return "blank_capped"

        return "blank"

    # -----------------------------------------------------
    # Confidence
    # -----------------------------------------------------

    confidence = state.get(
        "extracted_confidence",
        0.0,
    )

    field = state.get(
        "current_field"
    )

    threshold = _threshold_for(
        field
    )

    if confidence < threshold:

        if attempts >= MAX_CLARIFICATION_ATTEMPTS:

            return "low_conf_capped"

        return "low_conf"

    return "accepted"


# =========================================================
# NODE 9
# OFF-TRACK RESPONSE
# =========================================================

def respond_off_track(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    current_field = state.get(
        "current_field"
    )

    field_state = _ensure_field_state(
        requirements,
        current_field,
    )

    attempts = (
        state.get(
            "attempts_so_far",
            0,
        ) + 1
    )

    field_state["attempts"] = attempts

    reason = state.get(
        "extracted_off_track_reason",
        "",
    )

    question_text = _get_question_text(
        current_field
    )

    response = (
        "Let's keep this focused on "
        f"{_field_label(current_field)}."
    )

    if reason:

        response += f" {reason}"

    response += (
        f"\n\n{question_text}"
    )

    return {
        "requirements": requirements,
        "current_field": current_field,
        "agent_response": response,
        "next_action": "wait_for_user",
    }


# =========================================================
# NODE 10
# BLANK RESPONSE
# =========================================================

def respond_blank(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    current_field = state.get(
        "current_field"
    )

    field_state = _ensure_field_state(
        requirements,
        current_field,
    )

    attempts = (
        state.get(
            "attempts_so_far",
            0,
        ) + 1
    )

    field_state["attempts"] = attempts

    question_text = _get_question_text(
        current_field
    )

    return {
        "requirements": requirements,
        "current_field": current_field,
        "agent_response": (
            f"I didn't get enough information "
            f"for {_field_label(current_field)}.\n\n"
            f"{question_text}\n\n"
            f"You can also say "
            f"\"write it for me\" if you'd like me "
            f"to suggest an answer."
        ),
        "next_action": "wait_for_user",
    }


# =========================================================
# NODE 11
# LOW CONFIDENCE RESPONSE
# =========================================================

def respond_clarify(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    current_field = state.get(
        "current_field"
    )

    field_state = _ensure_field_state(
        requirements,
        current_field,
    )

    attempts = (
        state.get(
            "attempts_so_far",
            0,
        ) + 1
    )

    field_state["attempts"] = attempts

    value = state.get(
        "extracted_value"
    )

    reason = state.get(
        "extracted_reason",
        "",
    )

    return {
        "requirements": requirements,
        "current_field": current_field,
        "agent_response": (
            f'I understood "{value}", but I need '
            f"a little more detail about "
            f"{_field_label(current_field)} "
            f"to make the requirement useful."
            f"{' ' + reason if reason else ''}"
            f"\n\nCould you elaborate a little more?"
        ),
        "next_action": "wait_for_user",
    }


# =========================================================
# NODE 12
# ACCEPT AND STORE NORMAL ANSWER
# =========================================================

def accept_and_store(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    current_field = state.get(
        "current_field"
    )

    field_state = _ensure_field_state(
        requirements,
        current_field,
    )

    value = state.get(
        "extracted_value"
    )

    confidence = state.get(
        "extracted_confidence",
        0.5,
    )

    is_blank = (
        value is None
        or (
            isinstance(value, str)
            and not value.strip()
        )
    )

    # -----------------------------------------------------
    # Blank after maximum attempts
    # -----------------------------------------------------

    if is_blank:

        field_state["value"] = None
        field_state["status"] = "SKIPPED"
        field_state["confidence"] = 0.0

    else:

        field_state["value"] = value
        field_state["status"] = "PROVIDED"
        field_state["confidence"] = confidence

    field_state["attempts"] = 0
    field_state["question_count"] = 0

    # -----------------------------------------------------
    # Reset clarification attempts
    # -----------------------------------------------------

    clarification_attempts = dict(
        state.get(
            "clarification_attempts",
            {},
        )
    )

    clarification_attempts[
        current_field
    ] = 0

    next_field = (
        _find_next_missing_field(
            requirements
        )
    )

    return {
        "requirements": requirements,
        "current_field": next_field,
        "clarification_attempts":
            clarification_attempts,
    }


# =========================================================
# NODE 13
# EVALUATE REQUIREMENTS
# =========================================================

def evaluate_requirements(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    evaluation = evaluate_project(
        requirements
    )

    return {
        "requirements": requirements,

        "missing_fields":
            evaluation.get(
                "missing_fields",
                [],
            ),

        "completeness_status":
            evaluation.get(
                "completeness_status",
                "INCOMPLETE",
            ),

        "completeness_score":
            evaluation.get(
                "completeness_score",
                0.0,
            ),
    }

def requirement_decision(
    state: RequirementState,
) -> str:
    """
    Decide what the Requirement Manager should do
    after evaluating the collected requirements.
    """

    completeness_status = state.get(
        "completeness_status",
        "INCOMPLETE",
    )

    missing_fields = state.get(
        "missing_fields",
        [],
    )

    if (
        completeness_status == "COMPLETE"
        and not missing_fields
    ):
        return "complete"

    return "ask_question"

# =========================================================
# NODE 14
# GENERATE NEXT QUESTION
# =========================================================

def generate_question(
    state: RequirementState,
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        create_empty_requirements(),
    )

    next_field = _find_next_missing_field(
        requirements
    )

    # -----------------------------------------------------
    # Everything complete
    # -----------------------------------------------------

    if next_field is None:

        return {
            "agent_response": (
                "Great! I have all the required "
                "project information. Your project "
                "is ready for PRD generation."
            ),
            "current_field": None,
            "next_action": "generate_prd",
        }

    # -----------------------------------------------------
    # Ask next question
    # -----------------------------------------------------

    return {
        "requirements": requirements,
        "current_field": next_field,
        "agent_response":
            _get_question_text(
                next_field
            ),
        "next_action":
            "wait_for_user",
    }


# =========================================================
# NODE 15
# REQUIREMENTS COMPLETE
# =========================================================

def requirements_complete(
    state: RequirementState,
) -> Dict[str, Any]:

    return {
        "requirements":
            state.get(
                "requirements",
                {},
            ),

        "agent_response": (
            "Great! I have all the required "
            "project information. Your project "
            "is ready for PRD generation."
        ),

        "current_field": None,

        "next_action":
            "generate_prd",
    }

# =========================================================
# DOCUMENT-AWARE QUESTION GENERATION
# =========================================================

def generate_next_question(
    state: RequirementState
) -> Dict[str, Any]:

    requirements = state.get(
        "requirements",
        {}
    )

    document_summary = state.get(
        "document_summary",
        ""
    )

    document_filled_fields = state.get(
        "document_filled_fields",
        []
    )

    current_field = state.get(
        "current_field"
    )

    # -----------------------------------------------------
    # If no current field exists, find the next missing one
    # -----------------------------------------------------

    if not current_field:

        current_field = find_next_missing_field(
            requirements
        )

    # -----------------------------------------------------
    # No fields left
    # -----------------------------------------------------

    if not current_field:

        return {
            "agent_response": (
                "Great! I have all the required "
                "project information. Your project "
                "is ready for PRD generation."
            ),
            "next_action": "generate_prd",
            "current_field": None,
        }

    # -----------------------------------------------------
    # Build evaluation context
    # -----------------------------------------------------

    field_data = requirements.get(
        current_field,
        {}
    )

    existing_value = field_data.get(
        "value"
    )

    field_reason = field_data.get(
        "reason",
        ""
    )

    evaluation_context = ""

    if field_reason:

        evaluation_context = (
            f"The current information may need "
            f"clarification because: {field_reason}"
        )

    elif existing_value is None:

        evaluation_context = (
            "No usable information is currently "
            "available for this field."
        )

    else:

        evaluation_context = (
            "The field has information, but the "
            "requirement manager determined that "
            "additional clarification is needed."
        )

    # -----------------------------------------------------
    # Ask the document-aware planner
    # -----------------------------------------------------

    result = question_planner.generate_question(
        field_name=current_field,
        requirements=requirements,
        document_summary=document_summary,
        document_filled_fields=document_filled_fields,
        evaluation_context=evaluation_context,
    )

    question = result.get(
        "question",
        ""
    ).strip()

    # -----------------------------------------------------
    # Safety fallback
    # -----------------------------------------------------

    if not question:

        question = QUESTIONS.get(
            current_field,
            f"Could you provide more details about "
            f"{current_field.replace('_', ' ')}?"
        )

    return {
        "agent_response": question,
        "next_action": "wait_for_user",
        "current_field": current_field,
    }

# =========================================================
# DOCUMENT PROCESSING
# =========================================================

def process_uploaded_document(state: RequirementState):
    """
    Process an uploaded project document once.

    The document is read and analyzed by document_agent_node.
    Its extracted requirements and summary are stored in state.

    The document must NOT go through the normal
    classify -> extract flow because the document agent
    already performs structured extraction.
    """

    # -----------------------------------------------------
    # Prevent duplicate processing
    # -----------------------------------------------------

    if getattr(state, "document_processed", False):

        return {
            "next_action": "continue_requirement_interview"
        }

    # -----------------------------------------------------
    # Process document
    # -----------------------------------------------------

    result = document_agent_node(state)

    # -----------------------------------------------------
    # Mark document as processed
    # -----------------------------------------------------

    if result is None:
        result = {}

    result["document_processed"] = True
    result["next_action"] = "continue_requirement_interview"

    return result
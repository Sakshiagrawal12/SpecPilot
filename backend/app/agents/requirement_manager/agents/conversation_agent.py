"""
Conversation Agent (Updated & Context-Aware)
===========================================
Fixes:
1. Flexible substring & intent matching for proposal acceptances ("yes you can use it", "sure", etc.).
2. Preserves pending state across turns when LLM suggestions are generated.
3. Correctly commits accepted proposal values to requirements data before moving to missing fields.
"""

from typing import Any, Dict, Optional

from app.agents.requirement_manager.state import RequirementState
from app.ai.llm import llm

from ..config import (
    INTERVIEW_FIELDS,
    FIELD_SYNONYMS,
    QUESTIONS,
    MAX_CLARIFICATION_ATTEMPTS,
)

from ..utils import (
    _extract_json,
    _find_next_missing_field,
    _build_context_summary,
    _build_field_memory,
    _looks_like_question,
    _threshold_for,
    create_empty_requirements,
)


INTENTS = {
    "PROVIDE_ANSWER",
    "ASK_EXPLANATION",
    "ASK_SUGGESTION",
    "GENERATE_FOR_ME",
    "ACCEPT_PROPOSAL",
    "REJECT_PROPOSAL",
    "CORRECT_ANSWER",
    "GO_BACK",
    "SKIP",
    "OFF_TOPIC",
    "UNCLEAR",
}


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _get_current_field(state: RequirementState) -> Optional[str]:
    current_field = state.get("current_field")
    if current_field:
        return current_field

    requirements = state.get("requirements") or {}
    return _find_next_missing_field(requirements)


def _get_recent_messages(state: RequirementState, limit: int = 8) -> list:
    messages = state.get("messages") or []
    if not isinstance(messages, list):
        return []
    return messages[-limit:]


def _format_recent_messages(state: RequirementState, limit: int = 8) -> str:
    messages = _get_recent_messages(state, limit)
    if not messages:
        return "No previous conversation messages."

    lines = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        role = message.get("role", "unknown")
        content = message.get("content", "")
        if content:
            lines.append(f"{role.upper()}: {content}")

    return "\n".join(lines)


def _get_pending_proposal(state: RequirementState) -> Optional[Dict[str, Any]]:
    pending_confirmation = state.get("pending_confirmation", False)
    field = state.get("pending_generated_field")
    value = state.get("pending_generated_value")

    if not pending_confirmation or not field or not value:
        return None

    return {
        "field": field,
        "value": value,
    }


# ============================================================
# DETERMINISTIC GUARDS FOR ACCEPTANCE & REJECTION
# ============================================================
def _looks_like_acceptance(message: str) -> bool:
    """Sub-string and fuzzy matching guard for proposal acceptance."""
    normalized = message.lower().strip()
    
    acceptance_keywords = [
        "yes", "yeah", "yep", "sure", "okay", "ok", "sounds good", "sound good",
        "sounds great", "sound great", "looks good", "use this", "use that",
        "go with this", "accept", "use it", "can use this", "you can use it",
        "use option", "that works", "do it", "great", "perfect", "fine",
        "proceed", "you can proceed", "go ahead", "continue", "yes please"
    ]
    
   
    return any(kw in normalized for kw in acceptance_keywords)

def _looks_like_rejection(message: str) -> bool:
    """Sub-string and fuzzy matching guard for proposal rejection."""
    normalized = message.lower().strip()
    
    rejection_keywords = [
        "no", "nope", "dont use", "don't use", "reject", "change it",
        "give another", "try again", "not this", "different one"
    ]
    
    return any(kw in normalized for kw in rejection_keywords)


# ============================================================
# LLM CONVERSATION CLASSIFICATION
# ============================================================

def _classify_conversation(
    state: RequirementState,
    current_field: str,
    user_message: str,
) -> Dict[str, Any]:
    requirements = state.get("requirements") or {}
    project_name = state.get("project_name", "")
    pending_proposal = _get_pending_proposal(state)
    recent_conversation = _format_recent_messages(state)

    pending_text = "None"
    if pending_proposal:
        pending_text = (
            f"Field: {pending_proposal['field']}\n"
            f"Proposed value: {pending_proposal['value']}"
        )

    prompt = f"""
You are the Conversation Understanding Agent for an AI project requirement-gathering system.

Your job is to understand WHAT THE USER MEANS.

==================================================
PROJECT NAME: {project_name}
CURRENT FIELD: {current_field}
PENDING PROPOSAL:
{pending_text}
==================================================
RECENT CONVERSATION:
{recent_conversation}
==================================================
USER MESSAGE:
"{user_message}"
==================================================

Classify the intent into EXACTLY ONE category:

ACCEPT_PROPOSAL
- User accepts the pending proposal (e.g., "yes you can use it", "yes", "sure", "looks good", "go ahead").

GENERATE_FOR_ME
- User asks the AI to create/write/suggest a response based on the project (e.g., "can you give according to my project?", "write it for me", "suggest something").

ASK_EXPLANATION
- User asks what the field/question means or wants clarification (e.g., "can you explain this?", "what is problem statement?").

ASK_SUGGESTION
- User asks for general ideas or examples (e.g., "what are some examples?").

REJECT_PROPOSAL
- User rejects the proposed value (e.g., "no", "don't use that", "try another").

PROVIDE_ANSWER
- User provides direct information for the field.

SKIP / GO_BACK / OFF_TOPIC / UNCLEAR

==================================================
OUTPUT FORMAT (JSON ONLY)
==================================================
{{
    "intent": "ACCEPT_PROPOSAL | REJECT_PROPOSAL | GENERATE_FOR_ME | ASK_EXPLANATION | ASK_SUGGESTION | PROVIDE_ANSWER | SKIP | GO_BACK | OFF_TOPIC | UNCLEAR",
    "field": "{current_field}",
    "reason": "Short reason for classification."
}}
"""

    try:
        response = llm.generate(prompt)
        raw = getattr(response, "content", response)
        result = _extract_json(raw)

        if not isinstance(result, dict):
            return {"intent": "UNCLEAR", "field": current_field}

        intent = str(result.get("intent", "UNCLEAR")).upper().strip()
        if intent not in INTENTS:
            intent = "UNCLEAR"

        return {
            "intent": intent,
            "field": result.get("field") or current_field,
            "value": result.get("value"),
            "confidence": 1.0,
            "reason": str(result.get("reason", "")),
        }

    except Exception as exc:
        print(f"Classification error: {exc}")
        return {"intent": "UNCLEAR", "field": current_field}


# ============================================================
# CLASSIFY AND ROUTE
# ============================================================

def classify_and_route(state: RequirementState) -> RequirementState:
    requirements = state.get("requirements") or create_empty_requirements()
    state["requirements"] = requirements

    user_message = _safe_text(state.get("user_message"))
    if not user_message:
        state["message_type"] = "no_op"
        return state

    current_field = _get_current_field(state)
    if not current_field:
        state["message_type"] = "already_complete"
        return state

    state["current_field"] = current_field

    # 1. Check Pending Proposal Acceptance First via Deterministic Guard
    pending_proposal = _get_pending_proposal(state)
    if pending_proposal:
        if _looks_like_acceptance(user_message):
            state["message_type"] = "accept_proposal"
            state["correction_field"] = ""
            state["correction_value"] = None
            return state

        if _looks_like_rejection(user_message):
            state["message_type"] = "reject_proposal"
            return state

    # 2. Run LLM Classification
    classification = _classify_conversation(state, current_field, user_message)
    intent = classification["intent"]
    field = classification.get("field") or current_field

    state["correction_field"] = ""
    state["correction_value"] = None

    if intent == "ACCEPT_PROPOSAL" and pending_proposal:
        state["message_type"] = "accept_proposal"
        return state

    if intent == "REJECT_PROPOSAL" and pending_proposal:
        state["message_type"] = "reject_proposal"
        return state

    if intent == "GENERATE_FOR_ME":
        state["message_type"] = "generate_for_me"
        return state

    if intent == "ASK_SUGGESTION":
        state["message_type"] = "suggestion"
        return state

    if intent == "ASK_EXPLANATION":
        state["message_type"] = "question"
        return state

    if intent == "CORRECT_ANSWER":
        state["message_type"] = "correction"
        state["correction_field"] = field
        return state

    if intent == "GO_BACK":
        state["message_type"] = "go_back"
        return state

    if intent == "SKIP":
        state["message_type"] = "skip"
        return state

    if intent == "OFF_TOPIC":
        state["message_type"] = "off_track"
        return state

    if intent == "PROVIDE_ANSWER":
        state["message_type"] = "answer"
        return state

    if _looks_like_question(user_message):
        state["message_type"] = "question"
        return state

    state["message_type"] = "unclear"
    return state


def route_after_classification(state: RequirementState) -> str:
    message_type = state.get("message_type", "unclear")

    if message_type == "already_complete":
        return "already_complete"
    if message_type == "no_op":
        return "no_op"
    if message_type == "accept_proposal":
        return "accept_proposal"
    if message_type == "reject_proposal":
        return "reject_proposal"
    if message_type == "generate_for_me":
        return "generate_for_me"
    if message_type in {"question", "ask_explanation", "suggestion"}:
        return "question"
    if message_type == "correction":
        return "correction"
    if message_type == "go_back":
        return "go_back"
    if message_type == "skip":
        return "skip"
    if message_type == "off_track":
        return "off_track"
    if message_type == "answer":
        return "extract"

    return "unclear"


def accept_pending_generated(state: RequirementState) -> RequirementState:
    field = state.get("pending_generated_field")
    value = state.get("pending_generated_value")

    if not field or not value:
        state["pending_confirmation"] = False
        state["message_type"] = "unclear"
        return state

    requirements = state.get("requirements") or create_empty_requirements()

    # 1. Store in memory requirement dictionary
    if isinstance(requirements.get(field), dict):
        requirements[field]["value"] = value
        requirements[field]["status"] = "PROVIDED"
        requirements[field]["confidence"] = 1.0
        requirements[field]["source"] = "agent_suggestion"
    else:
        requirements[field] = {
            "value": value,
            "status": "PROVIDED",
            "confidence": 1.0,
            "source": "agent_suggestion",
        }

    state["requirements"] = requirements

    # 2. Clear pending state
    state["pending_generated_field"] = ""
    state["pending_generated_value"] = ""
    state["pending_confirmation"] = False

    # 3. PERMANENT DB SYNC: Directly persist updated requirements to SQL Database
    project_id = state.get("project_id")
    if project_id:
        try:
            from app.db.crud import update_project_requirements  # Adjust to your CRUD module name
            update_project_requirements(project_id, requirements)
        except Exception as err:
            print(f"[DB SYNC ERROR] Failed to update project {project_id}: {err}")

    # Move to next missing field
    next_field = _find_next_missing_field(requirements)
    state["current_field"] = next_field if next_field else ""

    return state
    
def reject_pending_generated(state: RequirementState) -> RequirementState:
    state["pending_generated_field"] = ""
    state["pending_generated_value"] = ""
    state["pending_confirmation"] = False
    state["message_type"] = "generate_for_me"
    return state


def handle_correction(state: RequirementState) -> RequirementState:
    field = state.get("correction_field") or state.get("current_field")
    value = state.get("correction_value")
    requirements = state.get("requirements") or create_empty_requirements()

    if value:
        if isinstance(requirements.get(field), dict):
            requirements[field]["value"] = value
            requirements[field]["status"] = "PROVIDED"
        else:
            requirements[field] = value

        state["requirements"] = requirements
        state["extracted_value"] = value
        state["extracted_confidence"] = 1.0
        state["extraction_outcome"] = "accepted"
        state["correction_field"] = ""
        state["correction_value"] = None

        next_field = _find_next_missing_field(requirements)
        state["current_field"] = next_field if next_field else ""
        return state

    state["current_field"] = field
    state["correction_field"] = field
    state["correction_value"] = None
    return state

def _call_llm_for_current_field(
    state: RequirementState,
    current_field: str,
    user_message: str,
) -> Dict[str, Any]:
    requirements = state.get("requirements") or {}
    project_name = state.get("project_name", "")

    context_summary = _build_context_summary(requirements, current_field)
    field_memory = _build_field_memory(requirements, current_field)
    recent_messages = _format_recent_messages(state, limit=8)  # <--- Pass Chat Memory
    
    question_data = QUESTIONS.get(current_field, {})
    question = question_data.get("text", "") if isinstance(question_data, dict) else str(question_data)

    prompt = f"""
You are a requirement extraction agent for SpecPilot.
Extract the user's answer ONLY for the current field: {current_field}.

==================================================
PROJECT NAME: {project_name}
CURRENT FIELD: {current_field}
FIELD QUESTION: {question}
==================================================
GATHERED PROJECT REQUIREMENTS SO FAR:
{context_summary}
==================================================
RECENT CONVERSATION HISTORY (Use this to resolve relative references like "the content you gave", "use that", "previous message"):
{recent_messages}
==================================================
USER MESSAGE:
"{user_message}"
==================================================

INSTRUCTIONS:
1. If the user refers to something previously mentioned in the conversation history (e.g., "use the content you gave me", "yes that one"), extract that proposed value from the chat history.
2. If the user provides new information, extract it directly.
3. If the user message is off-topic or doesn't provide/confirm the requirement, set value to null.

Return ONLY JSON:
{{
    "value": "extracted or referenced requirement text, or null",
    "confidence": 0.0 to 1.0,
    "reason": "explanation of extraction",
    "off_track": false,
    "off_track_reason": ""
}}
"""
    try:
        response = llm.generate(prompt)
        raw = getattr(response, "content", response)
        result = _extract_json(raw)

        if not isinstance(result, dict):
            return {"value": None, "confidence": 0.0, "reason": "Invalid json"}

        return {
            "value": result.get("value"),
            "confidence": float(result.get("confidence", 0.0) or 0.0),
            "reason": str(result.get("reason", "")),
            "off_track": bool(result.get("off_track", False)),
            "off_track_reason": str(result.get("off_track_reason", "")),
        }
    except Exception as exc:
        print(f"Extraction error: {exc}")
        return {"value": None, "confidence": 0.0, "reason": str(exc)}

def handle_user_question_or_suggestion(state: RequirementState) -> RequirementState:
    requirements = state.get("requirements") or {}
    
    if isinstance(requirements, str):
        try:
            requirements = json.loads(requirements)
        except Exception:
            requirements = {}

    if not isinstance(requirements, dict):
        requirements = {}

    project_name = state.get("project_name", "")
    current_field = state.get("current_field", "technology_preferences")
    user_message = _safe_text(state.get("user_message"))

    context_summary = _build_context_summary(project_name, requirements, current_field)
    recent_messages = _format_recent_messages(state, limit=8)

    prompt = f"""
You are SpecPilot, an AI Product Manager.

==================================================
PROJECT NAME: {project_name}
CURRENT FIELD: {current_field}
GATHERED REQUIREMENTS:
{context_summary}
==================================================
RECENT CHAT HISTORY:
{recent_messages}
==================================================
USER MESSAGE:
"{user_message}"
==================================================

INSTRUCTIONS:
1. Address the user's question or agreement directly.
2. If suggesting technologies, keep it lightweight and concrete (e.g. "React for frontend, Node.js/Python for backend, PostgreSQL for database").
3. Ask if they accept this suggestion.

Return JSON ONLY:
{{
    "response_text": "Your direct response + proposed tech stack",
    "suggested_value": "React, Node.js / Python, PostgreSQL"
}}
"""
    try:
        response = llm.generate(prompt)
        raw = getattr(response, "content", response)
        result = _extract_json(raw)

        response_text = result.get("response_text", "")
        suggested_value = result.get("suggested_value")

        state["agent_response"] = response_text

        if suggested_value:
            state["pending_confirmation"] = True
            state["pending_generated_field"] = current_field
            state["pending_generated_value"] = suggested_value

    except Exception as exc:
        print(f"Error handling question/suggestion: {exc}")
        state["agent_response"] = (
            "We can use a modern light stack: React for the frontend, Node.js/FastAPI for the backend, "
            "and PostgreSQL for database. Would you like to use this tech stack?"
        )
        state["pending_confirmation"] = True
        state["pending_generated_field"] = current_field
        state["pending_generated_value"] = "React, Node.js, FastAPI, PostgreSQL"

    return state
def route_after_extraction(state: RequirementState) -> str:
    value = state.get("extracted_value")
    confidence = float(state.get("extracted_confidence", 0.0) or 0.0)
    current_field = state.get("current_field")
    off_track = state.get("extracted_off_track", False)

    if off_track:
        return "off_track"

    if value is None or not str(value).strip():
        return "blank"

    threshold = _threshold_for(current_field)
    if confidence < threshold:
        return "low_confidence"

    return "accepted"


def accept_and_store(state: RequirementState) -> RequirementState:
    field = state.get("current_field")
    value = state.get("extracted_value")

    if not field or value is None:
        return state

    requirements = state.get("requirements") or create_empty_requirements()
    
    if isinstance(requirements.get(field), dict):
        requirements[field]["value"] = value
        requirements[field]["status"] = "PROVIDED"
        requirements[field]["confidence"] = state.get("extracted_confidence", 1.0)
    else:
        requirements[field] = value

    state["requirements"] = requirements
    state["extraction_outcome"] = "accepted"

    next_field = _find_next_missing_field(requirements)
    if next_field:
        state["current_field"] = next_field
        state["missing_fields"] = [f for f in INTERVIEW_FIELDS if not requirements.get(f)]
    else:
        state["current_field"] = ""
        state["missing_fields"] = []
        state["completeness_status"] = "COMPLETE"
        state["completeness_score"] = 1.0

    return state
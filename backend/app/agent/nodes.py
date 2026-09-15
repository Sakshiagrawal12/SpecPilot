from typing import Dict, Any
import json

from app.agent.state import AgentState
from app.agent.evaluator import evaluate_project
from app.ai.llm import llm


# =========================================================
# FIELD DEFINITIONS
# =========================================================

ALL_FIELDS = [
    "project_name",
    "category",
    "business_objective",
    "problem_statement",
    "target_users",
    "expected_features",
    "technology_preferences",
    "timeline",
    "additional_instructions"
]


# IMPORTANT:
# This is the exact order in which the agent interviews
# the user.
INTERVIEW_FIELDS = [
    "category",
    "business_objective",
    "target_users",
    "problem_statement",
    "expected_features",
    "technology_preferences",
    "timeline",
    "additional_instructions"
]


# =========================================================
# QUESTION DEFINITIONS
# =========================================================

QUESTIONS = {
    "category":
        "What category does this project belong to?",

    "business_objective":
        "What is the main goal or objective of this project?",

    "problem_statement":
        "What specific problem should this project solve?",

    "target_users":
        "Who are the main target users of this project?",

    "expected_features":
        "What key features would you like this project to provide?",

    "technology_preferences":
        "Do you have any preferred technologies, frameworks, "
        "databases, or tools for this project?",

    "timeline":
        "Do you have a target timeline or deadline for completing "
        "this project?",

    "additional_instructions":
        "Is there anything else you would like me to consider "
        "while defining the project requirements?"
}


# =========================================================
# EMPTY REQUIREMENTS
# =========================================================

def create_empty_requirements() -> Dict[str, Dict[str, Any]]:

    return {
        field: {
            "value": None,
            "status": "MISSING",
            "confidence": 0.0
        }
        for field in ALL_FIELDS
    }


# =========================================================
# JSON EXTRACTION
# =========================================================

def _extract_json(text: str) -> Dict[str, Any]:

    text = text.strip()

    # Remove markdown code fences
    if text.startswith("```"):

        lines = text.splitlines()

        if lines and lines[0].startswith("```"):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        text = "\n".join(lines).strip()

    try:

        return json.loads(text)

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


# =========================================================
# EXTRACT REQUIREMENTS
# =========================================================

def extract_requirements(state: AgentState):

    user_message = state.get(
        "user_message",
        ""
    ).strip()

    existing_requirements = state.get(
        "requirements"
    )

    # =====================================================
    # SAFETY
    # =====================================================

    if not existing_requirements:
        existing_requirements = create_empty_requirements()

    # =====================================================
    # PRESERVE PROJECT NAME
    # =====================================================

    project_name = state.get("project_name")

    if project_name:

        if "project_name" not in existing_requirements:

            existing_requirements["project_name"] = {
                "value": None,
                "status": "MISSING",
                "confidence": 0.0
            }

        existing_requirements["project_name"]["value"] = project_name
        existing_requirements["project_name"]["status"] = "PROVIDED"
        existing_requirements["project_name"]["confidence"] = 1.0

    # =====================================================
    # NO USER MESSAGE
    #
    # This happens during /agent/start.
    # We only initialize the requirements.
    # =====================================================

    if not user_message:

        next_field = _find_next_missing_field(
            existing_requirements
        )

        print("==========================================")
        print("INITIAL REQUIREMENT STATE")
        print("==========================================")
        print("NEXT FIELD:", next_field)
        print("==========================================")

        return {
            "requirements": existing_requirements,
            "current_field": next_field
        }

    # =====================================================
    # DETERMINE WHICH FIELD THE USER IS ANSWERING
    # =====================================================

    current_field = state.get(
        "current_field"
    )

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # If current_field is not available in the graph state,
    # recover it from the requirements.
    # -----------------------------------------------------

    if not current_field:

        current_field = _find_next_missing_field(
            existing_requirements
        )

        print("==========================================")
        print("CURRENT FIELD RECOVERED")
        print("==========================================")
        print("FIELD:", current_field)
        print("==========================================")
    else:

        print("==========================================")
        print("CURRENT FIELD FROM API STATE")
        print("==========================================")
        print("FIELD:", current_field)
        print("==========================================")
    # =====================================================
    # NOTHING LEFT TO ANSWER
    # =====================================================

    if not current_field:

        return {
            "requirements": existing_requirements,
            "current_field": ""
        }

    # =====================================================
    # VALIDATE FIELD
    # =====================================================

    if current_field not in INTERVIEW_FIELDS:

        print(
            f"WARNING: Invalid current_field: {current_field}"
        )

        return {
            "requirements": existing_requirements
        }

    print("==========================================")
    print("EXTRACTION INPUT")
    print("==========================================")
    print("CURRENT FIELD:", current_field)
    print("USER MESSAGE:", repr(user_message))
    print("==========================================")

    # =====================================================
    # EXTRACT ONLY CURRENT FIELD
    # =====================================================
    '''
    extracted_value = _call_llm_for_current_field(
        user_message=user_message,
        current_field=current_field
    )

    print("==========================================")
    print("EXTRACTION OUTPUT")
    print("==========================================")
    print("CURRENT FIELD:", current_field)
    print("EXTRACTED VALUE:", repr(extracted_value))
    print("==========================================")
    
    # =====================================================
    # INVALID / EMPTY ANSWER
    # =====================================================

    if extracted_value is None:

        print("==========================================")
        print("NO VALID VALUE EXTRACTED")
        print("==========================================")
        print("FIELD:", current_field)
        print("USER MESSAGE:", user_message)
        print("==========================================")

        return {
            "requirements": existing_requirements,
            "current_field": current_field
        }

    if isinstance(extracted_value, str):

        if not extracted_value.strip():

            return {
                "requirements": existing_requirements,
                "current_field": current_field
            }

        extracted_value = extracted_value.strip()

    # =====================================================
    # STORE ANSWER
    # =====================================================

    existing_requirements[current_field]["value"] = extracted_value

    existing_requirements[current_field]["status"] = "PROVIDED"

    existing_requirements[current_field]["confidence"] = 1.0

    # =====================================================
    # FIND NEXT FIELD
    # =====================================================

    next_field = _find_next_missing_field(
        existing_requirements
    )

    print("==========================================")
    print("REQUIREMENT UPDATED")
    print("==========================================")
    print("ANSWERED FIELD:", current_field)
    print("VALUE:", extracted_value)
    print("NEXT FIELD:", next_field)
    print("==========================================")

    # =====================================================
    # RETURN UPDATED STATE
    # =====================================================

    return {
        "requirements": existing_requirements,
        "current_field": next_field
    }
'''     # =====================================================
    # EXTRACT + JUDGE CURRENT FIELD
    # =====================================================

    extraction = _call_llm_for_current_field(
        user_message=user_message,
        current_field=current_field
    )

    extracted_value = extraction["value"]
    confidence = extraction["confidence"]
    reason = extraction["reason"]

    print("==========================================")
    print("EXTRACTION OUTPUT")
    print("==========================================")
    print("FIELD:", current_field)
    print("VALUE:", repr(extracted_value))
    print("CONFIDENCE:", confidence)
    print("REASON:", reason)
    print("==========================================")

    field_state = existing_requirements.setdefault(
        current_field,
        {"value": None, "status": "MISSING", "confidence": 0.0}
    )

    attempts_so_far = field_state.get("attempts", 0)

    is_blank = (
        extracted_value is None
        or (isinstance(extracted_value, str) and not extracted_value.strip())
    )

    # =====================================================
    # NOTHING USABLE EXTRACTED
    # =====================================================

    if is_blank:

        previous_value = field_state.get("value")

        has_previous_value = (
            previous_value is not None
            and not (isinstance(previous_value, str) and not previous_value.strip())
        )

        if has_previous_value:

            # A follow-up message that doesn't restate this field
            # shouldn't wipe out an answer we already accepted.

            next_field = _find_next_missing_field(existing_requirements)

            return {
                "requirements": existing_requirements,
                "current_field": next_field
            }

        attempts_so_far += 1
        field_state["attempts"] = attempts_so_far

        if attempts_so_far > MAX_CLARIFICATION_ATTEMPTS:

            field_state["value"] = "Not specified"
            field_state["status"] = "PROVIDED"
            field_state["confidence"] = 0.3
            field_state["attempts"] = 0

            next_field = _find_next_missing_field(existing_requirements)

            return {
                "requirements": existing_requirements,
                "current_field": next_field
            }

        return {
            "requirements": existing_requirements,
            "current_field": current_field,
            "agent_response": (
                f"I didn't catch anything usable for "
                f"{current_field.replace('_', ' ')}. "
                f"{QUESTIONS.get(current_field, 'Could you provide more detail?')}"
            ),
            "next_action": "wait_for_user"
        }

    # =====================================================
    # LOW CONFIDENCE — ASK FOR MORE DETAIL
    # =====================================================

    if confidence < _threshold_for(current_field):

        attempts_so_far += 1
        field_state["attempts"] = attempts_so_far

        if attempts_so_far <= MAX_CLARIFICATION_ATTEMPTS:

            clarifying_message = (
                f"I got \"{extracted_value}\" but I need a bit more "
                f"detail to write a solid PRD section for this. "
                f"{reason + ' ' if reason else ''}"
                f"Could you elaborate a little more?"
            )

            return {
                "requirements": existing_requirements,
                "current_field": current_field,
                "agent_response": clarifying_message,
                "next_action": "wait_for_user"
            }

        # Max attempts used up — fall through and accept it anyway
        # rather than loop forever.

    # =====================================================
    # STORE ACCEPTED ANSWER
    # =====================================================

    field_state["value"] = extracted_value
    field_state["status"] = "PROVIDED"
    field_state["confidence"] = confidence
    field_state["attempts"] = 0

    next_field = _find_next_missing_field(existing_requirements)

    print("==========================================")
    print("REQUIREMENT UPDATED")
    print("==========================================")
    print("ANSWERED FIELD:", current_field)
    print("VALUE:", extracted_value)
    print("NEXT FIELD:", next_field)
    print("==========================================")

    return {
        "requirements": existing_requirements,
        "current_field": next_field
    }


FIELD_CONFIDENCE_THRESHOLDS = {
    "category": 0.3,
    "business_objective": 0.55,
    "target_users": 0.45,
    "problem_statement": 0.55,
    "expected_features": 0.5,
    "technology_preferences": 0.35,
    "timeline": 0.3,
    "additional_instructions": 0.0,
}

MAX_CLARIFICATION_ATTEMPTS = 2

def _threshold_for(field_name: str) -> float:

    return FIELD_CONFIDENCE_THRESHOLDS.get(field_name, 0.5)

def _call_llm_for_current_field(
    user_message: str,
    current_field: str
):

    field_description = {
        # ... unchanged, same dict as before ...
    }

    description = field_description.get(
        current_field,
        "project requirement information"
    )

    prompt = f"""
You are the requirement extraction component of SpecPilot.

The user was asked ONE specific requirement question.

=========================================================
CURRENT REQUIREMENT FIELD
=========================================================
{current_field}

=========================================================
WHAT THIS FIELD MEANS
=========================================================
{description}

=========================================================
USER'S ANSWER
=========================================================
{user_message}

=========================================================
YOUR TASK
=========================================================

1. Extract ONLY the answer relevant to this field.
2. Do NOT infer, guess, or use outside knowledge.
3. Judge how SPECIFIC and USABLE this answer is for writing
   a professional PRD section, on a 0.0-1.0 confidence scale.

A LOW confidence (below 0.5) means the answer is:
- vague, generic, or a placeholder ("users", "normal features", "soon")
- too short to build a real PRD section from
- missing concrete specifics (who exactly, what exactly, which tech exactly)

A HIGH confidence (0.8+) means the answer gives concrete,
specific, usable detail.

If the answer gives NOTHING relevant to this field, return
value: null and confidence: 0.0.

=========================================================
RETURN FORMAT (JSON ONLY)
=========================================================

{{
    "value": "extracted answer, or a list for multi-item fields, or null",
    "confidence": 0.0,
    "reason": "one short sentence on what's missing or why it's vague, or empty string if confidence is high"
}}
"""

    response = llm.generate(prompt)

    result = _extract_json(response)

    return {
        "value": result.get("value"),
        "confidence": float(result.get("confidence", 0.0)),
        "reason": result.get("reason", "")
    }

# =========================================================
# LLM EXTRACTION FOR CURRENT FIELD
# =========================================================
'''
def _call_llm_for_current_field(
    user_message: str,
    current_field: str
):

    field_description = {
         "category":
        "the broad category or type of project, such as travel, "
        "education, healthcare, finance, e-commerce, social media, "
        "productivity, or another category explicitly stated by the user",


        "business_objective":
            "the main goal, purpose, or desired outcome of the project",

        "problem_statement":
            "the specific problem or difficulty that the project should solve",

        "target_users":
            "the specific people, groups, organizations, or audience who will use the project",

        "expected_features":
            "the functionality or capabilities the project should provide",

        "technology_preferences":
            "technologies, programming languages, frameworks, databases, "
            "platforms, libraries, or tools explicitly preferred by the user",

        "timeline":
            "the explicit project duration, target date, or deadline",

        "additional_instructions":
            "additional constraints, preferences, requirements, or instructions"
    }

    description = field_description.get(
        current_field,
        "project requirement information"
    )

    prompt = f"""
You are the requirement extraction component of SpecPilot.

The user was asked ONE specific requirement question.

Your job is to extract ONLY the answer to that question.

=========================================================
CURRENT REQUIREMENT FIELD
=========================================================

{current_field}

=========================================================
WHAT THIS FIELD MEANS
=========================================================

{description}

=========================================================
USER'S ANSWER
=========================================================

{user_message}

=========================================================
IMPORTANT RULES
=========================================================

1. Extract ONLY information relevant to the current field.

2. Do NOT extract information for any other field.

3. Do NOT infer missing information.

4. Do NOT guess.

5. Do NOT use previous conversation messages.

6. Do NOT use general knowledge.

7. Preserve the user's actual meaning.

8. Preserve specific details.

9. If the user gives multiple items that belong to this field,
   preserve all of them.

10. Do not replace specific information with generic words.

11. If the answer does not provide meaningful information
    for the current field, return null.

12. Do not ask another question.

13. Do not generate a PRD.

14. Return ONLY valid JSON.

=========================================================
FIELD-SPECIFIC GUIDANCE
=========================================================
category:

Extract the broad category or type of project explicitly stated
by the user.

Examples:

User:
"This is a travel planning application."

Return:

{{
    "value": "travel"
}}

User:
"It is an education platform for students."

Return:

{{
    "value": "education"
}}

business_objective:

Extract the user's stated goal or desired outcome.

problem_statement:

Extract the actual problem the user describes.

target_users:

Extract the specific users or audience.

For example:

User:
"College students and young professionals who want to
manage their books."

Return:
"college students and young professionals"

Do not return:
"users"

expected_features:

Extract all explicitly requested features.

If multiple features are mentioned, return them as a list.

Example:

User:
"It should allow users to add books, search books,
and track reading progress."

Return:

[
    "add books",
    "search books",
    "track reading progress"
]

technology_preferences:

Extract explicitly mentioned technologies.

If multiple technologies are mentioned, return them as a list.

timeline:

Extract only the explicitly stated timeline or deadline.

additional_instructions:

Extract explicit constraints, preferences, or instructions
that do not belong to another requirement field.

=========================================================
RETURN FORMAT
=========================================================

Return exactly:

{{
    "value": null
}}

OR:

{{
    "value": "extracted answer"
}}

OR, for fields containing multiple items:

{{
    "value": [
        "item 1",
        "item 2"
    ]
}}
"""

    response = llm.generate(prompt)

    result = _extract_json(response)

    return result.get("value")
'''


# =========================================================
# EVALUATE REQUIREMENTS
# =========================================================

def evaluate_requirements(state: AgentState):

    requirements = state.get(
        "requirements",
        create_empty_requirements()
    )

    project_data = {}

    for field in ALL_FIELDS:

        field_data = requirements.get(
            field,
            {}
        )

        project_data[field] = field_data.get(
            "value"
        )

    # =====================================================
    # DETERMINE MISSING FIELDS
    # =====================================================

    missing_fields = []

    for field in INTERVIEW_FIELDS:

        value = project_data.get(field)

        if value is None:
            missing_fields.append(field)
            continue

        if isinstance(value, str) and not value.strip():
            missing_fields.append(field)
            continue

        if isinstance(value, list) and len(value) == 0:
            missing_fields.append(field)
            continue

    # =====================================================
    # CALCULATE COMPLETENESS
    # =====================================================

    total_fields = len(INTERVIEW_FIELDS)
    provided_fields = total_fields - len(missing_fields)

    completeness_score = int(
        (provided_fields / total_fields) * 100
    )

    if missing_fields:

        completeness_status = "INCOMPLETE"

    else:

        completeness_status = "COMPLETE"

    # =====================================================
    # DEBUG
    # =====================================================

    print("==========================================")
    print("REQUIREMENT EVALUATION")
    print("==========================================")
    print("TOTAL FIELDS:", total_fields)
    print("PROVIDED FIELDS:", provided_fields)
    print("MISSING FIELDS:", missing_fields)
    print("STATUS:", completeness_status)
    print("SCORE:", completeness_score)
    print("==========================================")

    return {

        "missing_fields":
            missing_fields,

        "completeness_status":
            completeness_status,

        "completeness_score":
            completeness_score
    }

# =========================================================
# FIND NEXT MISSING FIELD
# =========================================================

def _find_next_missing_field(
    requirements: Dict[str, Dict[str, Any]]
):

    for field in INTERVIEW_FIELDS:

        field_data = requirements.get(
            field,
            {}
        )

        value = field_data.get(
            "value"
        )

        if value is None:

            return field

        if isinstance(value, str) and not value.strip():

            return field

    return None


# =========================================================
# GENERATE NEXT QUESTION
# =========================================================

def generate_question(state: AgentState):

    requirements = state.get(
        "requirements",
        create_empty_requirements()
    )

    # -----------------------------------------------------
    # FIND FIRST MISSING FIELD
    # -----------------------------------------------------

    next_field = _find_next_missing_field(
        requirements
    )

    # -----------------------------------------------------
    # ALL REQUIREMENTS COMPLETE
    # -----------------------------------------------------

    if next_field is None:

        return {

            "agent_response":
                "Great! I have all the required project "
                "information. Your project is ready for "
                "PRD generation.",

            "next_action":
                "generate_prd",

            "current_field":
                None
        }

    # -----------------------------------------------------
    # GET QUESTION
    # -----------------------------------------------------

    question = QUESTIONS.get(
        next_field
    )

    # -----------------------------------------------------
    # RETURN QUESTION
    # -----------------------------------------------------

    print("==========================================")
    print("NEXT INTERVIEW FIELD")
    print("==========================================")
    print("FIELD:", next_field)
    print("QUESTION:", question)
    print("==========================================")

    return {

        "agent_response":
            question,

        "next_action":
            "wait_for_user",

        "current_field":
            next_field
    }


# =========================================================
# REQUIREMENTS COMPLETE
# =========================================================

def requirements_complete(state: AgentState):

    return {

        "agent_response":
            "Great! I have all the required project "
            "information. Your project is ready for PRD generation.",

        "next_action":
            "generate_prd",

        "current_field":
            None
    }
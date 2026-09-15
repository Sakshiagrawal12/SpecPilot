# =========================================================
# EVALUATOR
# =========================================================
#
# Deterministic validation layer for SpecPilot.
#
# The conversational interview is considered complete only
# when every field in INTERVIEW_FIELDS has meaningful data.
#
# =========================================================

from typing import Any, Dict, List


# =========================================================
# CONFIGURATION
# =========================================================

MIN_TEXT_LENGTH = 3

EMPTY_VALUES = {
    "",
    "none",
    "null",
    "n/a",
    "na",
    "not provided",
    "not specified",
    "unknown"
}


# =========================================================
# REQUIRED INTERVIEW FIELDS
# =========================================================

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
# HELPER FUNCTIONS
# =========================================================

def _normalize_value(value: Any) -> str:
    """
    Convert a field value into a normalized string.
    """

    if value is None:
        return ""

    if isinstance(value, str):
        return value.strip()

    if isinstance(value, list):

        return ", ".join(
            str(item).strip()
            for item in value
            if str(item).strip()
        )

    if isinstance(value, dict):

        return " ".join(
            str(item).strip()
            for item in value.values()
            if str(item).strip()
        )

    return str(value).strip()


def _is_empty(value: Any) -> bool:
    """
    Determine whether a field contains meaningful information.
    """

    normalized = _normalize_value(value)

    if not normalized:
        return True

    if normalized.lower() in EMPTY_VALUES:
        return True

    if len(normalized) < MIN_TEXT_LENGTH:
        return True

    return False


# =========================================================
# FIELD EVALUATION
# =========================================================

def evaluate_field(
    field_name: str,
    value: Any
) -> Dict[str, Any]:
    """
    Evaluate one interview field.
    """

    if _is_empty(value):

        return {
            "field": field_name,
            "valid": False,
            "status": "MISSING",
            "required": True,
            "message": (
                f"{field_name.replace('_', ' ').title()} "
                "is required."
            )
        }

    return {
        "field": field_name,
        "valid": True,
        "status": "PROVIDED",
        "required": True,
        "value": value,
        "message": (
            f"{field_name.replace('_', ' ').title()} "
            "has been provided."
        )
    }


# =========================================================
# PROJECT EVALUATION
# =========================================================

def evaluate_project(
    project_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate whether ALL interview fields have been provided.
    """

    if not isinstance(project_data, dict):

        return {
            "ready": False,
            "status": "INVALID_INPUT",
            "score": 0.0,
            "total_required_fields": 0,
            "provided_required_fields": 0,
            "missing_fields": [],
            "fields": {},
            "message": "Project data must be a dictionary."
        }

    results = {}

    missing_fields = []

    total_required = len(INTERVIEW_FIELDS)
    provided_required = 0

    # =====================================================
    # EVALUATE INTERVIEW FIELDS
    # =====================================================

    for field_name in INTERVIEW_FIELDS:

        value = project_data.get(field_name)

        result = evaluate_field(
            field_name=field_name,
            value=value
        )

        results[field_name] = result

        if result["valid"]:

            provided_required += 1

        else:

            missing_fields.append(field_name)

    # =====================================================
    # CALCULATE SCORE
    # =====================================================

    if total_required > 0:

        score = round(
            (provided_required / total_required) * 100,
            2
        )

    else:

        score = 0.0

    # =====================================================
    # DETERMINE STATUS
    # =====================================================

    if missing_fields:

        ready = False
        status = "INCOMPLETE"

        message = (
            "The project information is incomplete. "
            "Please provide the remaining required fields."
        )

    else:

        ready = True
        status = "COMPLETE"

        message = (
            "All project requirements have been provided. "
            "The project is ready for PRD generation."
        )

    # =====================================================
    # FINAL RESULT
    # =====================================================

    return {
        "ready": ready,
        "status": status,
        "score": score,

        "total_required_fields":
            total_required,

        "provided_required_fields":
            provided_required,

        "missing_fields":
            missing_fields,

        "fields":
            results,

        "message":
            message
    }


# =========================================================
# GET MISSING FIELDS
# =========================================================

def get_missing_fields(
    project_data: Dict[str, Any]
) -> List[str]:

    evaluation = evaluate_project(
        project_data
    )

    return evaluation.get(
        "missing_fields",
        []
    )


# =========================================================
# CHECK GENERATION READINESS
# =========================================================

def is_ready_for_generation(
    project_data: Dict[str, Any]
) -> bool:

    evaluation = evaluate_project(
        project_data
    )

    return evaluation.get(
        "ready",
        False
    )
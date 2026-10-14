# app/agents/requirement_manager/evaluator.py

from typing import Any, Dict

from app.agents.requirement_manager.config import (
    ALL_FIELDS,
    INTERVIEW_FIELDS,
)


def evaluate_project(
    requirements: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Evaluate the completeness of project requirements.

    A field is considered handled when it either:
    - contains a usable value, or
    - has explicitly been marked as SKIPPED.

    Returns:
        missing_fields
        completeness_status
        completeness_score
    """

    missing_fields = []

    for field in INTERVIEW_FIELDS:

        field_data = requirements.get(
            field,
            {},
        )

        value = field_data.get(
            "value"
        )

        status = field_data.get(
            "status",
            "MISSING",
        )

        # =================================================
        # EXPLICITLY SKIPPED
        # =================================================

        if status == "SKIPPED":
            continue

        # =================================================
        # MISSING
        # =================================================

        if value is None:

            missing_fields.append(
                field
            )

            continue

        # =================================================
        # STRING VALIDATION
        # =================================================

        if isinstance(value, str):

            cleaned_value = (
                value.strip().lower()
            )

            if (
                not cleaned_value
                or cleaned_value in {
                    "none",
                    "n/a",
                    "na",
                    "null",
                    "-",
                }
            ):

                missing_fields.append(
                    field
                )

                continue

        # =================================================
        # LIST VALIDATION
        # =================================================

        if isinstance(value, list):

            if len(value) == 0:

                missing_fields.append(
                    field
                )

                continue

    # =====================================================
    # COMPLETENESS
    # =====================================================

    total_fields = len(
        INTERVIEW_FIELDS
    )

    provided_fields = (
        total_fields
        - len(missing_fields)
    )

    if total_fields == 0:

        completeness_score = 0

    else:

        completeness_score = int(
            (
                provided_fields
                / total_fields
            )
            * 100
        )

    completeness_status = (
        "COMPLETE"
        if not missing_fields
        else "INCOMPLETE"
    )

    return {
        "missing_fields":
            missing_fields,

        "completeness_status":
            completeness_status,

        "completeness_score":
            completeness_score,
    }
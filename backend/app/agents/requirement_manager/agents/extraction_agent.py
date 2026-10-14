# app/agents/requirement_manager/agents/extraction_agent.py

from typing import Any, Dict

from app.ai.llm import llm
from ..utils import _extract_json


class RequirementExtractionAgent:
    """
    Extracts the answer for the currently active requirement field.

    Responsibilities:
    - Extract only information relevant to the current field
    - Assign a confidence score
    - Explain why confidence may be low
    - Detect whether the answer is inconsistent/off-track
    """

    FIELD_DESCRIPTIONS = {
        "category": (
            "the broad category or type of project, such as travel, "
            "education, healthcare, finance, e-commerce, social media, "
            "productivity, or another category explicitly stated by the user, you should be flexible enough to take the category"
        ),

        "business_objective": (
            "the main goal, purpose, or desired outcome of the project"
        ),

        "problem_statement": (
            "the specific problem or difficulty that the project should solve"
        ),

        "target_users": (
            "the specific people, groups, organizations, or audience "
            "who will use the project"
        ),

        "expected_features": (
            "the functionality or capabilities the project should provide"
        ),

        "technology_preferences": (
            "technologies, programming languages, frameworks, databases, "
            "platforms, libraries, or tools explicitly preferred by the user"
        ),

        "timeline": (
            "the explicit project duration, target date, or deadline"
        ),

        "additional_instructions": (
            "additional constraints, preferences, requirements, or instructions"
        ),
    }

    def extract(
        self,
        user_message: str,
        current_field: str,
        context_summary: str,
        field_memory: str,
    ) -> Dict[str, Any]:

        field_description = self.FIELD_DESCRIPTIONS.get(
            current_field,
            "project requirement information"
        )

        prompt = f"""
You are the requirement extraction component of SpecPilot.

=========================================================
PROJECT CONTEXT SO FAR
=========================================================
{context_summary}

=========================================================
HISTORY ON THIS FIELD
=========================================================
{field_memory}

=========================================================
CURRENT REQUIREMENT FIELD
=========================================================
{current_field}

=========================================================
WHAT THIS FIELD MEANS
=========================================================
{field_description}

=========================================================
USER'S ANSWER
=========================================================
{user_message}

=========================================================
YOUR TASK
=========================================================

1. Extract ONLY the answer relevant to this field.

2. Do NOT infer, guess, or use outside knowledge.

3. Judge confidence from 0.0 to 1.0 based on how
   specific and usable this answer is for writing a PRD section.

4. If the user's message contains BOTH relevant information
   and unrelated content, extract only the relevant part.

5. If the message is off-topic or does not attempt to answer
   the question, return value: null and confidence: 0.0.

6. Separately check whether the answer is CONSISTENT with
   the project context above.

7. Set off_track to true only if the answer clearly
   contradicts or has nothing to do with the established
   project.

8. Do NOT flag an answer as off_track simply because it is
   vague. Vague answers are a confidence problem.

=========================================================
RETURN FORMAT
=========================================================

Return JSON only:

{{
    "value": "extracted answer, a list for multi-item fields, or null",
    "confidence": 0.0,
    "reason": "one short sentence explaining what is missing or vague, or empty string",
    "off_track": false,
    "off_track_reason": "one short sentence if off_track is true, otherwise empty string"
}}
"""

        response = llm.generate(prompt)

        result = _extract_json(response)

        return {
            "value": result.get("value"),
            "confidence": float(
                result.get("confidence", 0.0) or 0.0
            ),
            "reason": result.get("reason", ""),
            "off_track": bool(
                result.get("off_track", False)
            ),
            "off_track_reason": result.get(
                "off_track_reason",
                ""
            ),
        }
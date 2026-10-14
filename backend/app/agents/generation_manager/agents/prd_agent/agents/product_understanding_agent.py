import json
from typing import Any, Dict

from app.ai.llm import llm


class ProductUnderstandingAgent:
    """
    Understands the product context from the project and the
    finalized user requirements.

    This agent does NOT generate the final PRD.
    """

    def _get_requirement(
        self,
        requirements: Dict[str, Any],
        field: str
    ) -> str:

        field_data = requirements.get(field, {})

        if isinstance(field_data, dict):
            value = field_data.get("value")
        else:
            value = field_data

        if value is None:
            return "Not specified"

        if isinstance(value, list):
            return "\n".join(
                f"- {item}"
                for item in value
            )

        if isinstance(value, dict):
            return json.dumps(
                value,
                ensure_ascii=False
            )

        return str(value)

    def _build_prompt(
        self,
        project: Any,
        requirements: Dict[str, Any]
    ) -> str:

        return f"""
You are a Product Understanding Agent working inside
an AI-powered project management system.

Your responsibility is to understand the product context
before a PRD is generated.

The user's collected requirements are the PRIMARY SOURCE
OF TRUTH.

You may clarify and organize the supplied information,
but you MUST NOT invent unsupported functionality,
technologies, users, business rules, or requirements.

=========================================================
PROJECT
=========================================================

PROJECT NAME:
{getattr(project, "project_name", "Not specified")}

=========================================================
USER-COLLECTED REQUIREMENTS
=========================================================

CATEGORY:
{self._get_requirement(requirements, "category")}

BUSINESS OBJECTIVE:
{self._get_requirement(requirements, "business_objective")}

TARGET USERS:
{self._get_requirement(requirements, "target_users")}

PROBLEM STATEMENT:
{self._get_requirement(requirements, "problem_statement")}

EXPECTED FEATURES:
{self._get_requirement(requirements, "expected_features")}

TECHNOLOGY PREFERENCES:
{self._get_requirement(requirements, "technology_preferences")}

TIMELINE:
{self._get_requirement(requirements, "timeline")}

ADDITIONAL INSTRUCTIONS:
{self._get_requirement(requirements, "additional_instructions")}

=========================================================
EXISTING PROJECT INFORMATION
=========================================================

PROJECT DESCRIPTION:
{getattr(project, "overview", None) or "Not specified"}

AI PROBLEM STATEMENT:
{getattr(project, "ai_problem_statement", None) or "Not specified"}

PROPOSED SOLUTION:
{getattr(project, "proposed_solution", None) or "Not specified"}

TARGET AUDIENCE:
{getattr(project, "target_audience", None) or "Not specified"}

BUSINESS VALUE:
{getattr(project, "business_value", None) or "Not specified"}

MAJOR FEATURES:
{getattr(project, "major_features", None) or "Not specified"}

EXPECTED OUTCOME:
{getattr(project, "expected_outcome", None) or "Not specified"}

BUSINESS RULES:
{self._get_requirement(
    requirements,
    "business_rules"
)}

NON-FUNCTIONAL REQUIREMENTS:
{self._get_requirement(
    requirements,
    "non_functional_requirements"
)}

ASSUMPTIONS:
{self._get_requirement(
    requirements,
    "assumptions"
)}

DEPENDENCIES:
{self._get_requirement(
    requirements,
    "dependencies"
)}
=========================================================
TASK
=========================================================

Create a structured understanding of the product.

Identify:

1. Product summary
2. Core problem
3. Business objective
4. Target users
5. Proposed solution
6. Business value
7. Expected outcome
8. Product scope
9. Important constraints

Do NOT invent information.

If information is unavailable, use:

"Not specified"

=========================================================
RETURN ONLY VALID JSON
=========================================================

Return exactly:

{{
    "product_summary": "...",
    "core_problem": "...",
    "business_objective": "...",
    "target_users": "...",
    "proposed_solution": "...",
    "business_value": "...",
    "expected_outcome": "...",
    "product_scope": "...",
    "constraints": "..."
}}
"""

    def generate(
        self,
        project: Any,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:

        prompt = self._build_prompt(
            project,
            requirements
        )

        response = llm.generate(prompt).strip()

        if response.startswith("```"):
            response = (
                response
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        try:
            data = json.loads(response)
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Product Understanding Agent returned invalid JSON."
            ) from exc

        required_fields = [
            "product_summary",
            "core_problem",
            "business_objective",
            "target_users",
            "proposed_solution",
            "business_value",
            "expected_outcome",
            "product_scope",
            "constraints"
        ]

        for field in required_fields:
            if field not in data:
                raise RuntimeError(
                    f"Product Understanding missing field: {field}"
                )

        return data


product_understanding_agent = ProductUnderstandingAgent()
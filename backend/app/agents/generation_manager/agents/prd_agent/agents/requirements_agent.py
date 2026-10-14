import json
from typing import Any, Dict

from app.ai.llm import llm


class RequirementsAgent:
    """
    Analyzes the finalized requirements and organizes them
    for PRD generation.

    It does not invent new requirements.
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
        requirements: Dict[str, Any]
    ) -> str:

        return f"""
You are a Requirements Analysis Agent.

Your task is to analyze the finalized requirements collected
during the SpecPilot requirement interview.

The supplied requirements are the ONLY source of truth.

You may organize and clarify them, but you MUST NOT invent:

- features
- users
- technologies
- business rules
- integrations
- constraints

=========================================================
REQUIREMENTS
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

Organize the supplied information into:

1. Functional requirements
2. Non-functional requirements
3. Business rules
4. Technology constraints
5. Assumptions
6. Dependencies
7. Acceptance criteria inputs

Do not create unsupported requirements.

If information is missing, use an empty list.

=========================================================
RETURN ONLY VALID JSON
=========================================================

{{
    "functional_requirements": [],
    "non_functional_requirements": [],
    "business_rules": [],
    "technology_constraints": [],
    "assumptions": [],
    "dependencies": [],
    "acceptance_criteria_inputs": []
}}
"""

    def generate(
        self,
        requirements: Dict[str, Any]
    ) -> Dict[str, Any]:

        prompt = self._build_prompt(requirements)

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
                "Requirements Agent returned invalid JSON."
            ) from exc

        required_fields = [
            "functional_requirements",
            "non_functional_requirements",
            "business_rules",
            "technology_constraints",
            "assumptions",
            "dependencies",
            "acceptance_criteria_inputs"
        ]

        for field in required_fields:
            if field not in data:
                raise RuntimeError(
                    f"Requirements Agent missing field: {field}"
                )

        return data


requirements_agent = RequirementsAgent()
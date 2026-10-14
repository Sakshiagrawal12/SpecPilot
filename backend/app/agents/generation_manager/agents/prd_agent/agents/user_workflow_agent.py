import json
from typing import Any, Dict

from app.ai.llm import llm


class UserWorkflowAgent:
    """
    Generates user workflows based only on the supplied
    project requirements and expected features.

    The workflow produced here can later be consumed by
    the separate Diagram Agent.
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
        requirements: Dict[str, Any],
        product_understanding: Dict[str, Any]
    ) -> str:

        return f"""
You are a User Workflow Analysis Agent.

Your responsibility is to identify the user workflows
supported by the supplied project requirements.

The user's requirements are the source of truth.

Do NOT invent workflows or functionality.

=========================================================
PRODUCT UNDERSTANDING
=========================================================

{json.dumps(
    product_understanding,
    ensure_ascii=False,
    indent=2
)}

=========================================================
EXPECTED FEATURES
=========================================================

{self._get_requirement(
    requirements,
    "expected_features"
)}

=========================================================
TARGET USERS
=========================================================

{self._get_requirement(
    requirements,
    "target_users"
)}

=========================================================
PROBLEM STATEMENT
=========================================================

{self._get_requirement(
    requirements,
    "problem_statement"
)}

=========================================================
TASK
=========================================================

Identify the main user workflows.

For each workflow provide:

- workflow name
- actor
- trigger
- ordered steps
- expected result

Keep the workflow strictly grounded in the supplied
requirements.

Do not add unsupported functionality.

If workflows cannot be determined from the supplied
information, return an empty list.

=========================================================
RETURN ONLY VALID JSON
=========================================================

{{
    "workflows": [
        {{
            "name": "...",
            "actor": "...",
            "trigger": "...",
            "steps": [
                "..."
            ],
            "expected_result": "..."
        }}
    ]
}}
"""

    def generate(
        self,
        requirements: Dict[str, Any],
        product_understanding: Dict[str, Any]
    ) -> Dict[str, Any]:

        prompt = self._build_prompt(
            requirements,
            product_understanding
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
                "User Workflow Agent returned invalid JSON."
            ) from exc

        if "workflows" not in data:
            raise RuntimeError(
                "User Workflow Agent missing workflows."
            )

        if not isinstance(data["workflows"], list):
            raise RuntimeError(
                "User Workflow Agent workflows must be a list."
            )

        return data


user_workflow_agent = UserWorkflowAgent()
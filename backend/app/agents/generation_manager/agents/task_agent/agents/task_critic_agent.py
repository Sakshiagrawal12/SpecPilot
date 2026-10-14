import json
from typing import Any, Dict, List

from app.ai.llm import llm


class TaskCriticAgent:
    """
    Reviews generated tasks against the approved PRD.

    Checks:
    - PRD traceability
    - unsupported tasks
    - missing requirements
    - duplicate tasks
    - unclear acceptance criteria
    - invalid dependencies
    - scope creep
    """

    def _extract_json(self, response: str) -> Dict[str, Any]:

        response = response.strip()

        if response.startswith("```"):
            response = response.replace("```json", "")
            response = response.replace("```", "")
            response = response.strip()

        try:
            return json.loads(response)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Task Critic Agent returned invalid JSON: {exc}"
            )

    def review(
        self,
        prd: Dict[str, Any],
        tasks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        prompt = f"""
You are a Task Critic Agent.

Review the generated implementation tasks against the approved PRD.

APPROVED PRD:
{json.dumps(prd, indent=2, default=str)}

GENERATED TASKS:
{json.dumps(tasks, indent=2, default=str)}

Check for:

1. Tasks that are not supported by the PRD
2. Missing implementation coverage for important functional requirements
3. Duplicate tasks
4. Tasks that are too vague
5. Missing acceptance criteria
6. Invalid or unclear dependencies
7. Unsupported technologies
8. Scope creep
9. Tasks that cannot be traced to a PRD requirement

A task should not be rejected merely because the exact wording
differs from the PRD.

Return ONLY valid JSON.

If the tasks are acceptable:

{{
    "status": "PASS",
    "issues": [],
    "suggestions": []
}}

If problems exist:

{{
    "status": "FAIL",
    "issues": [],
    "suggestions": []
}}
"""

        response = llm.generate(prompt)

        result = self._extract_json(response)

        status = result.get("status", "FAIL")

        if status not in {"PASS", "FAIL"}:
            status = "FAIL"

        return {
            "status": status,
            "issues": result.get("issues", []),
            "suggestions": result.get("suggestions", []),
        }


task_critic_agent = TaskCriticAgent()
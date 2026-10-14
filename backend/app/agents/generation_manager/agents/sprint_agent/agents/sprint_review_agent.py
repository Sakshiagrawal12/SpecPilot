import json
from typing import Any, Dict

from app.ai.llm import llm


class SprintReviewAgent:

    def _extract_json(
        self,
        response: str,
    ) -> Dict[str, Any]:

        response = response.strip()

        if response.startswith("```"):

            response = (
                response
                .replace("```json", "")
                .replace("```", "")
                .strip()
            )

        try:

            return json.loads(response)

        except json.JSONDecodeError as exc:

            raise ValueError(
                f"Sprint Review Agent returned invalid JSON: {exc}"
            )

    def review(
        self,
        tasks,
        prioritized_tasks,
        capacity_plan,
        dependency_plan,
    ) -> Dict[str, Any]:

        prompt = f"""
You are a Sprint Plan Review Agent.

Review the proposed sprint planning information.

ORIGINAL TASKS:
{json.dumps(tasks, indent=2, default=str)}

PRIORITIZED TASKS:
{json.dumps(prioritized_tasks, indent=2, default=str)}

CAPACITY PLAN:
{json.dumps(capacity_plan, indent=2, default=str)}

DEPENDENCY PLAN:
{json.dumps(dependency_plan, indent=2, default=str)}

Check:

1. Every task is included.
2. No task was invented.
3. No task was silently removed.
4. Sprint ordering respects dependencies.
5. High-priority tasks are appropriately scheduled.
6. Capacity is reasonable.
7. Dependency conflicts are not ignored.
8. Sprint goals are understandable.
9. Tasks are assigned to valid sprints.

Return:

PASS if the plan is acceptable.

FAIL if meaningful problems exist.

Return ONLY valid JSON.

Structure:

{{
    "status": "PASS",
    "issues": [],
    "suggestions": []
}}
"""

        response = llm.generate(prompt)

        result = self._extract_json(response)

        status = result.get(
            "status",
            "FAIL",
        )

        if status not in {"PASS", "FAIL"}:
            status = "FAIL"

        return {
            "status": status,
            "issues": result.get("issues", []),
            "suggestions": result.get("suggestions", []),
        }


sprint_review_agent = SprintReviewAgent()
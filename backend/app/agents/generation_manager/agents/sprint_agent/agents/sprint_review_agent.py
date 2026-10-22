import json
from typing import Any, Dict

from app.ai.llm import llm


class SprintReviewAgent:

    @staticmethod
    def _strip_fences(text: str) -> str:
        text = text.strip()

        if text.startswith("```"):
            text = (
                text.replace("```json", "")
                .replace("```", "")
                .strip()
            )

        return text

    def _extract_json(self, response: str) -> Dict[str, Any]:
        text = self._strip_fences(response)

        candidates = [text]

        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            candidates.append(text[start:end + 1])

        last_error = None

        for candidate in candidates:
            try:
                result = json.loads(candidate)
            except json.JSONDecodeError as exc:
                last_error = exc
                continue

            if isinstance(result, dict):
                return result

        raise ValueError(
            f"Sprint Review Agent returned invalid JSON: {last_error}"
        )

    @staticmethod
    def _failed(issue: str, suggestion: str) -> Dict[str, Any]:
        return {
            "status": "FAIL",
            "issues": [issue],
            "suggestions": [suggestion],
        }

    def review(
        self,
        tasks,
        prioritized_tasks,
        capacity_plan,
        dependency_plan,
    ) -> Dict[str, Any]:

        # A missing input is reported clearly instead of crashing the flow
        if dependency_plan is None:
            return self._failed(
                "No dependency plan was provided to the review.",
                "Run dependency analysis before the sprint review.",
            )

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

Keep each issue and suggestion to one short sentence.

Return ONLY valid JSON.

Structure:

{{
    "status": "PASS",
    "issues": [],
    "suggestions": []
}}
"""

        result = None

        for attempt in (1, 2):
            try:
                result = self._extract_json(llm.generate(prompt))
                break
            except ValueError as exc:
                print(f"SPRINT REVIEW attempt {attempt} failed: {exc}")

        if result is None:
            return self._failed(
                "The review could not be completed because the reply was invalid.",
                "Run the review again.",
            )

        status = result.get("status", "FAIL")

        if status not in {"PASS", "FAIL"}:
            status = "FAIL"

        issues = result.get("issues", [])
        suggestions = result.get("suggestions", [])

        return {
            "status": status,
            "issues": issues if isinstance(issues, list) else [str(issues)],
            "suggestions": (
                suggestions if isinstance(suggestions, list) else [str(suggestions)]
            ),
        }


sprint_review_agent = SprintReviewAgent()
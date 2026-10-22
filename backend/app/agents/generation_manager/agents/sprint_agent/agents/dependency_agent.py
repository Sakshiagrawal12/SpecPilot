import json
from typing import Any, Dict, List

from app.ai.llm import llm


class DependencyAgent:

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

        raise ValueError(f"Dependency Agent returned invalid JSON: {last_error}")

    @staticmethod
    def _normalize(result: Dict[str, Any]) -> Dict[str, Any]:
        """Guarantee every key the rest of the pipeline may read."""

        dependencies = result.get("dependencies")
        independent = result.get("independent_tasks")
        conflicts = result.get("conflicts")

        return {
            "dependencies": dependencies if isinstance(dependencies, list) else [],
            "independent_tasks": independent if isinstance(independent, list) else [],
            "conflicts": conflicts if isinstance(conflicts, list) else [],
        }

    def analyze(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        # Send only what dependency analysis needs, to keep input and output short
        compact = [
            {
                "task_title": t.get("task_title"),
                "module": t.get("module"),
                "description": str(t.get("description", ""))[:200],
                "dependencies": t.get("dependencies", []),
            }
            for t in tasks
        ]

        prompt = f"""
You are a Software Dependency Analysis Agent.

Analyze dependencies between the supplied implementation tasks.

TASKS:
{json.dumps(compact, indent=2, default=str)}

Identify:

1. Task dependencies
2. Blocking relationships
3. Tasks that should happen before another task
4. Potential dependency conflicts
5. Tasks that can run independently

Rules:

1. Use only dependencies supported by the task information.
2. Do not invent external dependencies.
3. Do not invent technologies.
4. Do not create dependencies simply because tasks
   belong to the same module.
5. List in "dependencies" ONLY tasks that actually depend on another task.
   Put every other task title in "independent_tasks".
6. Use the exact task_title text from the input. Keep "reason" to one short sentence.

Return ONLY valid JSON.

Structure:

{{
    "dependencies": [
        {{
            "task": "",
            "depends_on": [],
            "reason": ""
        }}
    ],
    "independent_tasks": [],
    "conflicts": []
}}
"""

        last_error = None

        for attempt in (1, 2):
            try:
                response = llm.generate(prompt)
                return self._normalize(self._extract_json(response))
            except ValueError as exc:
                last_error = exc
                print(f"DEPENDENCY AGENT attempt {attempt} failed: {exc}")

        raise ValueError(str(last_error))


dependency_agent = DependencyAgent()
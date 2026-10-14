import json
from typing import Any, Dict, List

from app.ai.llm import llm


class PriorityAgent:

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
                f"Priority Agent returned invalid JSON: {exc}"
            )

    def prioritize(
        self,
        tasks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        prompt = f"""
You are a software project planning Priority Agent.

Your job is to analyze the supplied implementation tasks
and determine their implementation priority.

TASKS:
{json.dumps(tasks, indent=2, default=str)}

Rules:

1. Do not invent new tasks.
2. Do not remove tasks.
3. Preserve every task.
4. Consider dependencies when determining priority.
5. Foundational tasks should generally come before tasks
   that depend on them.
6. Do not change the actual task scope.

Assign:

- priority
- priority_reason
- execution_order

Priority must be one of:

High
Medium
Low

Return ONLY valid JSON.

Structure:

{{
    "tasks": [
        {{
            "task_title": "",
            "priority": "",
            "priority_reason": "",
            "execution_order": 1
        }}
    ]
}}
"""

        response = llm.generate(prompt)

        result = self._extract_json(response)

        prioritized = result.get("tasks")

        if not isinstance(prioritized, list):

            raise ValueError(
                "Priority Agent did not return a task list."
            )

        return prioritized


priority_agent = PriorityAgent()
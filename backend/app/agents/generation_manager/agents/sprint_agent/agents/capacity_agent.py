import json
from typing import Any, Dict, List

from app.ai.llm import llm


class CapacityAgent:

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
                f"Capacity Agent returned invalid JSON: {exc}"
            )

    def plan_capacity(
        self,
        tasks: List[Dict[str, Any]],
        project: Any,
    ) -> Dict[str, Any]:

        project_timeline = getattr(
            project,
            "timeline",
            None,
        )

        prompt = f"""
You are a Software Project Capacity Planning Agent.

Determine how the supplied implementation tasks can be
distributed across development sprints.

PROJECT TIMELINE:
{project_timeline or "Not specified"}

TASKS:
{json.dumps(tasks, indent=2, default=str)}

Rules:

1. Do not invent tasks.
2. Do not remove tasks.
3. Every task must appear in a sprint.
4. Do not overload a sprint unnecessarily.
5. Consider estimated complexity.
6. Consider task dependencies.
7. If team capacity is not specified, make a
   conservative planning assumption and explicitly
   record that assumption.
8. Do not invent a specific team size unless the
   project information provides one.

Return ONLY valid JSON.

Structure:

{{
    "capacity_assumptions": [],
    "sprints": [
        {{
            "sprint_number": 1,
            "goal": "",
            "task_titles": []
        }}
    ]
}}
"""

        response = llm.generate(prompt)

        return self._extract_json(response)


capacity_agent = CapacityAgent()
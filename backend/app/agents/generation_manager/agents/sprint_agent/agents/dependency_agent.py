import json
from typing import Any, Dict, List

from app.ai.llm import llm


class DependencyAgent:

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
                f"Dependency Agent returned invalid JSON: {exc}"
            )

    def analyze(
        self,
        tasks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        prompt = f"""
You are a Software Dependency Analysis Agent.

Analyze dependencies between the supplied implementation tasks.

TASKS:
{json.dumps(tasks, indent=2, default=str)}

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

        response = llm.generate(prompt)

        return self._extract_json(response)


dependency_agent = DependencyAgent()
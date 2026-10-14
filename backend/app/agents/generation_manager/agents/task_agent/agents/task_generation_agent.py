
import json
from typing import Any, Dict, List

from app.ai.llm import llm


class TaskGenerationAgent:
    """Generates implementation tasks from the approved PRD."""

    def _extract_json(self, response: str) -> Dict[str, Any]:
        response = response.strip()

        if response.startswith("```"):
            lines = response.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            response = "\n".join(lines).strip()

        try:
            result = json.loads(response)
        except json.JSONDecodeError as original_error:
            start = response.find("{")
            end = response.rfind("}")

            if start == -1 or end == -1 or start >= end:
                raise ValueError(
                    "Task Generation Agent returned no JSON object. "
                    f"Response preview: {response[:1000]}"
                ) from original_error

            candidate = response[start:end + 1]

            try:
                result = json.loads(candidate)
            except json.JSONDecodeError as exc:
                error_position = exc.pos
                snippet_start = max(0, error_position - 150)
                snippet_end = min(len(candidate), error_position + 150)

                raise ValueError(
                    "Task Generation Agent returned invalid JSON. "
                    f"Line {exc.lineno}, column {exc.colno}: {exc.msg}\n"
                    f"Problematic response snippet:\n"
                    f"{candidate[snippet_start:snippet_end]}"
                ) from exc

        if not isinstance(result, dict):
            raise ValueError(
                "Task Generation Agent response must be a JSON object."
            )

        return result

    def generate(
        self,
        project: Any,
        prd: Dict[str, Any],
        task_analysis: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        project_name = getattr(
            project,
            "project_name",
            "Unnamed Project",
        )

        prompt = f"""
You are a Task Generation Agent.

Generate implementation tasks for the following project.

PROJECT:
{project_name}

APPROVED PRD:
{json.dumps(prd, indent=2, default=str)}

TASK ANALYSIS:
{json.dumps(task_analysis, indent=2, default=str)}

The PRD is the source of truth.
Generate only tasks supported by the PRD.
Do not invent features, technologies, integrations, users,
unrelated functionality, or unsupported business rules.

Each task must contain:
- task_title
- description
- task_type
- module
- priority
- acceptance_criteria
- owner_role
- dependencies
- estimated_complexity
- source_requirement

Priority must be High, Medium, or Low.
Estimated complexity must be Small, Medium, or Large.

Return ONLY valid JSON in this structure:
{{
    "tasks": [
        {{
            "task_title": "",
            "description": "",
            "task_type": "",
            "module": "",
            "priority": "",
            "acceptance_criteria": "",
            "owner_role": "",
            "dependencies": [],
            "estimated_complexity": "",
            "source_requirement": ""
        }}
    ]
}}
"""

        response = llm.generate(prompt)
        result = self._extract_json(response)
        tasks = result.get("tasks")

        if not isinstance(tasks, list):
            raise ValueError(
                "Task Generation Agent did not return a task list."
            )

        return tasks


task_generation_agent = TaskGenerationAgent()

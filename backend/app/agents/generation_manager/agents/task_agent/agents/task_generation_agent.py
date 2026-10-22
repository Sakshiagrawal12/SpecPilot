import json
from typing import Any, Dict, List, Tuple

from app.ai.llm import llm

MAX_ROUNDS = 4


class TaskGenerationAgent:
    """Generates implementation tasks from the approved PRD."""

    @staticmethod
    def _strip_fences(text: str) -> str:
        text = text.strip()

        if text.startswith("```"):
            lines = text.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            text = "\n".join(lines).strip()

        return text

    @staticmethod
    def _salvage_tasks(text: str) -> List[Dict[str, Any]]:
        """Collect every COMPLETE task object from a cut-off or malformed reply."""

        key = text.find('"tasks"')
        if key == -1:
            return []

        start = text.find("[", key)
        if start == -1:
            return []

        decoder = json.JSONDecoder()
        tasks: List[Dict[str, Any]] = []
        i, n = start + 1, len(text)

        while i < n:
            while i < n and text[i] in " \n\r\t,":
                i += 1

            if i >= n or text[i] != "{":
                break

            try:
                obj, end = decoder.raw_decode(text, i)
            except json.JSONDecodeError:
                break  # last object was incomplete

            tasks.append(obj)
            i = end

        return tasks

    def _parse_tasks(self, response: str) -> Tuple[List[Dict[str, Any]], bool]:
        """Returns (tasks, complete). complete=False means the reply was cut off or broken."""

        text = self._strip_fences(response)

        candidates = [text]
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            candidates.append(text[start:end + 1])

        for candidate in candidates:
            try:
                result = json.loads(candidate)
            except json.JSONDecodeError:
                continue

            if isinstance(result, dict) and isinstance(result.get("tasks"), list):
                return result["tasks"], True

            raise ValueError("Task Generation Agent did not return a task list.")

        return self._salvage_tasks(text), False

    def _build_prompt(
        self,
        project_name: str,
        prd: Dict[str, Any],
        task_analysis: Dict[str, Any],
    ) -> str:
        return f"""
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

Keep every task compact: description at most 2 sentences,
acceptance_criteria at most 3 short criteria in a single string.

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

    def generate(
        self,
        project: Any,
        prd: Dict[str, Any],
        task_analysis: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        project_name = getattr(project, "project_name", "Unnamed Project")
        base_prompt = self._build_prompt(project_name, prd, task_analysis)

        tasks: List[Dict[str, Any]] = []
        seen = set()
        prompt = base_prompt
        last_response = ""
        finished = False

        for round_no in range(1, MAX_ROUNDS + 1):
            last_response = llm.generate(prompt)
            batch, complete = self._parse_tasks(last_response)

            added = 0
            for task in batch:
                title = str(task.get("task_title", "")).strip().lower()
                if title and title not in seen:
                    seen.add(title)
                    tasks.append(task)
                    added += 1

            print(
                f"TASK GEN round {round_no}: complete={complete}, "
                f"new tasks={added}, total={len(tasks)}"
            )

            if complete:
                finished = True
                break

            if added == 0:
                break  # no progress, stop instead of looping

            done_titles = "\n".join(f"- {t.get('task_title', '')}" for t in tasks)
            prompt = (
                base_prompt
                + "\nTASKS ALREADY GENERATED (do not repeat them):\n"
                + done_titles
                + "\n\nGenerate ONLY the remaining tasks needed to cover the PRD, "
                "in the same JSON structure. If every PRD requirement is already "
                'covered, return {"tasks": []}.\n'
            )

        if not tasks:
            raise ValueError(
                "Task Generation Agent returned no usable tasks. "
                f"Response preview: {last_response[:1000]}"
            )

        if not finished:
            print("TASK GEN WARNING: stopped before the model confirmed completion")

        return tasks


task_generation_agent = TaskGenerationAgent()
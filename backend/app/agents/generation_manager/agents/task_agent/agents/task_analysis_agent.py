import json
from typing import Any, Dict

from app.ai.llm import llm


class TaskAnalysisAgent:
    """
    Analyzes the PRD before task generation.

    Responsibilities:
    - Identify major implementation areas
    - Identify modules/components
    - Identify dependencies
    - Identify implementation constraints
    - Preserve PRD scope
    - Avoid inventing functionality
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
                f"Task Analysis Agent returned invalid JSON: {exc}"
            )

    def analyze(
        self,
        project: Any,
        prd: Dict[str, Any],
    ) -> Dict[str, Any]:

        project_name = getattr(
            project,
            "project_name",
            "Unnamed Project",
        )

        prompt = f"""
You are a Task Analysis Agent.

Your job is to analyze an approved Product Requirements Document
before implementation tasks are generated.

PROJECT:
{project_name}

PRD:
{json.dumps(prd, indent=2, default=str)}

Analyze ONLY the information present in the PRD.

Do not invent:
- features
- modules
- technologies
- users
- integrations
- business rules
- implementation requirements

Identify:

1. major implementation areas
2. modules/components
3. functional requirements that need implementation
4. dependencies between implementation areas
5. technical constraints explicitly present in the PRD
6. important acceptance criteria that should influence task creation

Return ONLY valid JSON.

Use exactly this structure:

{{
    "implementation_areas": [],
    "modules": [],
    "functional_requirements": [],
    "dependencies": [],
    "technical_constraints": [],
    "important_acceptance_criteria": []
}}
"""

        response = llm.generate(prompt)

        result = self._extract_json(response)

        required_keys = [
            "implementation_areas",
            "modules",
            "functional_requirements",
            "dependencies",
            "technical_constraints",
            "important_acceptance_criteria",
        ]

        for key in required_keys:
            if key not in result:
                result[key] = []

        return result


task_analysis_agent = TaskAnalysisAgent()
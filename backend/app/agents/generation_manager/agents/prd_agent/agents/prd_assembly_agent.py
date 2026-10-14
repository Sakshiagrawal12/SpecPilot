import json
from typing import Any, Dict

from app.ai.llm import llm


class PRDAssemblyAgent:

    REQUIRED_FIELDS = [
        "product_overview",
        "problem_statement",
        "goals_and_objectives",
        "target_users",
        "functional_requirements",
        "user_workflows",
        "business_rules",
        "non_functional_requirements",
        "assumptions_and_dependencies",
        "acceptance_criteria",
    ]

    def _build_prompt(
        self,
        project: Any,
        requirements: Dict[str, Any],
        product_understanding: Dict[str, Any],
        requirement_analysis: Dict[str, Any],
        user_workflows: list,
        critique: Dict[str, Any] | None = None,
    ) -> str:

        critique_text = "No previous critique."

        if critique:
            critique_text = json.dumps(
                critique,
                ensure_ascii=False,
                indent=2,
            )

        workflows_text = json.dumps(
            user_workflows,
            ensure_ascii=False,
            indent=2,
        )

        return f"""
You are a Senior Product Manager and PRD Assembly Agent.

Your responsibility is to assemble a professional Software
Product Requirements Document from structured analysis
performed by other agents.

The original user requirements are the PRIMARY SOURCE OF TRUTH.

Do not invent requirements.

============================================================
PROJECT
============================================================

{json.dumps(project, ensure_ascii=False, indent=2, default=str)}

============================================================
ORIGINAL USER REQUIREMENTS
============================================================

{json.dumps(requirements, ensure_ascii=False, indent=2)}

============================================================
PRODUCT UNDERSTANDING
============================================================

{json.dumps(product_understanding, ensure_ascii=False, indent=2)}

============================================================
REQUIREMENT ANALYSIS
============================================================

{json.dumps(requirement_analysis, ensure_ascii=False, indent=2)}

============================================================
STRUCTURED USER WORKFLOWS
============================================================

{workflows_text}

============================================================
PREVIOUS CRITIQUE
============================================================

{critique_text}

============================================================
PRD SECTIONS
============================================================

1. Product Overview
2. Problem Statement
3. Goals and Objectives
4. Target Users
5. Functional Requirements
6. User Workflows
7. Business Rules
8. Non-Functional Requirements
9. Assumptions and Dependencies
10. Acceptance Criteria

============================================================
ASSEMBLY RULES
============================================================

1. The original user requirements are the source of truth.

2. Do NOT invent unsupported functionality.

3. Do NOT invent unsupported technologies.

4. Do NOT invent unsupported users.

5. Do NOT invent unsupported business rules.

6. Do NOT invent unsupported non-functional requirements.

7. Do NOT invent unsupported assumptions.

8. Do NOT invent unsupported dependencies.

9. Preserve information supplied by Requirement Analysis.

10. Preserve the structure of User Workflows.

11. Do NOT convert workflows into a comma-separated string.

12. Every functional requirement must be traceable to a supplied
    requirement or requirement-analysis item.

13. Give functional requirements stable IDs such as FR-001,
    FR-002, FR-003.

14. Every acceptance criterion must reference a functional
    requirement ID.

15. Do not create acceptance criteria for unsupported features.

16. If business rules are empty in the requirement analysis,
    return an empty list.

17. If non-functional requirements are empty in the requirement
    analysis, return an empty list.

18. If assumptions are empty, return an empty list.

19. If dependencies are empty, return an empty list.

20. Preserve the actual workflow structure:

    name
    actor
    trigger
    steps
    expected_result

21. Do not replace detailed requirements with vague labels.

For example, do NOT convert:

"Users can create an event by entering title, date, location,
description and ticket information."

into:

"Create Event"

The detailed requirement must be preserved.

22. If a previous critique exists, fix only the identified issues.

23. Keep the entire PRD internally consistent.

24. Return ONLY valid JSON.

25. Do NOT use Markdown code fences.

26. Do NOT add explanations before or after JSON.

============================================================
RETURN EXACTLY THIS JSON STRUCTURE
============================================================

{{
    "product_overview": "",
    "problem_statement": "",
    "goals_and_objectives": [],
    "target_users": [],

    "functional_requirements": [
        {{
            "id": "FR-001",
            "requirement": "",
            "source": ""
        }}
    ],

    "user_workflows": [
        {{
            "name": "",
            "actor": "",
            "trigger": "",
            "steps": [],
            "expected_result": ""
        }}
    ],

    "business_rules": [],

    "non_functional_requirements": [],

    "assumptions_and_dependencies": {{
        "assumptions": [],
        "dependencies": []
    }},

    "acceptance_criteria": [
        {{
            "requirement_id": "FR-001",
            "criteria": []
        }}
    ]
}}
"""

    def generate(
        self,
        project: Any,
        requirements: Dict[str, Any],
        product_understanding: Dict[str, Any],
        requirement_analysis: Dict[str, Any],
        user_workflows: list,
        critique: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:

        prompt = self._build_prompt(
            project=project,
            requirements=requirements,
            product_understanding=product_understanding,
            requirement_analysis=requirement_analysis,
            user_workflows=user_workflows,
            critique=critique,
        )

        response = llm.generate(prompt).strip()

        # Remove accidental markdown fences
        if response.startswith("```json"):
            response = response[7:]

        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        data = json.loads(response)

        # ----------------------------------------------------
        # Required top-level fields
        # ----------------------------------------------------

        for field in self.REQUIRED_FIELDS:
            if field not in data:
                raise ValueError(
                    f"PRD assembly missing required field: {field}"
                )

        # ----------------------------------------------------
        # Type validation
        # ----------------------------------------------------

        if not isinstance(
            data["functional_requirements"],
            list,
        ):
            raise ValueError(
                "functional_requirements must be a list"
            )

        if not isinstance(
            data["user_workflows"],
            list,
        ):
            raise ValueError(
                "user_workflows must be a list"
            )

        if not isinstance(
            data["business_rules"],
            list,
        ):
            raise ValueError(
                "business_rules must be a list"
            )

        if not isinstance(
            data["non_functional_requirements"],
            list,
        ):
            raise ValueError(
                "non_functional_requirements must be a list"
            )

        if not isinstance(
            data["assumptions_and_dependencies"],
            dict,
        ):
            raise ValueError(
                "assumptions_and_dependencies must be an object"
            )

        if not isinstance(
            data["acceptance_criteria"],
            list,
        ):
            raise ValueError(
                "acceptance_criteria must be a list"
            )

        # ----------------------------------------------------
        # Functional requirement validation
        # ----------------------------------------------------

        for index, item in enumerate(
            data["functional_requirements"]
        ):

            if not isinstance(item, dict):
                raise ValueError(
                    f"Functional requirement {index} must be an object"
                )

            required_keys = [
                "id",
                "requirement",
                "source",
            ]

            for key in required_keys:
                if key not in item:
                    raise ValueError(
                        f"Functional requirement {index} "
                        f"missing '{key}'"
                    )

        # ----------------------------------------------------
        # Workflow validation
        # ----------------------------------------------------

        for index, workflow in enumerate(
            data["user_workflows"]
        ):

            if not isinstance(workflow, dict):
                raise ValueError(
                    f"Workflow {index} must be an object"
                )

            required_keys = [
                "name",
                "actor",
                "trigger",
                "steps",
                "expected_result",
            ]

            for key in required_keys:
                if key not in workflow:
                    raise ValueError(
                        f"Workflow {index} missing '{key}'"
                    )

            if not isinstance(
                workflow["steps"],
                list,
            ):
                raise ValueError(
                    f"Workflow {index} steps must be a list"
                )

        # ----------------------------------------------------
        # Assumptions / dependencies
        # ----------------------------------------------------

        assumptions_dependencies = (
            data["assumptions_and_dependencies"]
        )

        assumptions_dependencies.setdefault(
            "assumptions",
            [],
        )

        assumptions_dependencies.setdefault(
            "dependencies",
            [],
        )

        # ----------------------------------------------------
        # Acceptance criteria validation
        # ----------------------------------------------------

        for index, item in enumerate(
            data["acceptance_criteria"]
        ):

            if not isinstance(item, dict):
                raise ValueError(
                    f"Acceptance criteria {index} "
                    f"must be an object"
                )

            if "requirement_id" not in item:
                raise ValueError(
                    f"Acceptance criteria {index} "
                    f"missing requirement_id"
                )

            if "criteria" not in item:
                raise ValueError(
                    f"Acceptance criteria {index} "
                    f"missing criteria"
                )

            if not isinstance(
                item["criteria"],
                list,
            ):
                raise ValueError(
                    f"Acceptance criteria {index} "
                    f"criteria must be a list"
                )

        return data


prd_assembly_agent = PRDAssemblyAgent()
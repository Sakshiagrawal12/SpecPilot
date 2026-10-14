import json
from typing import Any, Dict

from app.ai.llm import llm


class PRDCriticAgent:

    def _build_prompt(
        self,
        requirements: Dict[str, Any],
        requirement_analysis: Dict[str, Any],
        user_workflows: list,
        prd: Dict[str, Any],
    ) -> str:

        return f"""
You are a strict PRD Quality and Consistency Critic.

Your job is to verify that the generated PRD faithfully
represents the supplied requirements and structured analysis.

Do NOT judge whether the product idea is good or bad.

Only check correctness, traceability, completeness and
consistency.

============================================================
ORIGINAL REQUIREMENTS
============================================================

{json.dumps(
    requirements,
    ensure_ascii=False,
    indent=2
)}

============================================================
REQUIREMENT ANALYSIS
============================================================

{json.dumps(
    requirement_analysis,
    ensure_ascii=False,
    indent=2
)}

============================================================
ORIGINAL STRUCTURED WORKFLOWS
============================================================

{json.dumps(
    user_workflows,
    ensure_ascii=False,
    indent=2
)}

============================================================
GENERATED PRD
============================================================

{json.dumps(
    prd,
    ensure_ascii=False,
    indent=2
)}

============================================================
CHECK THE FOLLOWING
============================================================

1. Unsupported functionality

2. Unsupported technologies

3. Unsupported users

4. Unsupported business rules

5. Unsupported non-functional requirements

6. Unsupported assumptions

7. Unsupported dependencies

8. Functional requirements that cannot be traced
   to the supplied requirements.

9. Functional requirements that were unnecessarily
   simplified or lost.

10. Workflows that do not correspond to supplied
    workflows or expected features.

11. Workflow structure being lost.

12. Missing workflow steps.

13. Acceptance criteria that do not correspond
    to functional requirements.

14. Acceptance criteria referencing unknown
    requirement IDs.

15. Business rules supplied by the analysis but
    missing from the PRD.

16. Non-functional requirements supplied by the
    analysis but missing from the PRD.

17. Assumptions supplied by the analysis but
    missing from the PRD.

18. Dependencies supplied by the analysis but
    missing from the PRD.

19. Contradictions between PRD sections.

20. Important information from the original
    requirements being lost.

============================================================
IMPORTANT
============================================================

Do NOT mark a missing field as an error when the original
requirements genuinely contain no information for that field.

For example:

If business_rules = []

then an empty PRD business_rules list is correct.

Do NOT ask the assembly agent to invent information.

============================================================
PASS CONDITION
============================================================

Return PASS only when:

- the PRD follows the source requirements
- no unsupported functionality was added
- structured workflows are preserved
- functional requirements are traceable
- acceptance criteria map to functional requirements
- supplied NFRs/business rules/assumptions/dependencies
  are preserved
- there are no important contradictions

============================================================
RETURN ONLY JSON
============================================================

{{
    "status": "PASS",
    "issues": [],
    "suggestions": []
}}

OR

{{
    "status": "FAIL",
    "issues": [
        "..."
    ],
    "suggestions": [
        "..."
    ]
}}

Do NOT use Markdown code fences.
Do NOT add explanations outside JSON.
"""

    def review(
        self,
        requirements: Dict[str, Any],
        requirement_analysis: Dict[str, Any],
        user_workflows: list,
        prd: Dict[str, Any],
    ) -> Dict[str, Any]:

        prompt = self._build_prompt(
            requirements=requirements,
            requirement_analysis=requirement_analysis,
            user_workflows=user_workflows,
            prd=prd,
        )

        response = llm.generate(prompt).strip()

        if response.startswith("```json"):
            response = response[7:]

        elif response.startswith("```"):
            response = response[3:]

        if response.endswith("```"):
            response = response[:-3]

        response = response.strip()

        data = json.loads(response)

        status = data.get("status")

        if status not in {"PASS", "FAIL"}:
            raise ValueError(
                "PRD critic returned invalid status"
            )

        data.setdefault("issues", [])
        data.setdefault("suggestions", [])

        return data


prd_critic_agent = PRDCriticAgent()
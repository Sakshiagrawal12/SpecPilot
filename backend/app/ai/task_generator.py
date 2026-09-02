import json

from app.ai.llm import llm


# =========================================================
# TASK PROMPT
# =========================================================

def task_prompt(project):

    return f"""
You are a Senior Technical Project Manager.

Generate a practical set of implementation tasks for the
software project below.

The tasks will be used by a development team to implement
the project described in the PRD.


=========================================================
PROJECT INFORMATION
=========================================================

PROJECT NAME:
{project.project_name}

CATEGORY:
{project.category}

BUSINESS OBJECTIVE:
{project.business_objective}

ORIGINAL TARGET USERS:
{project.target_users}

ORIGINAL PROBLEM STATEMENT:
{project.problem_statement}

EXPECTED FEATURES:
{project.expected_features}

TECHNOLOGY PREFERENCES:
{project.technology_preferences}

TIMELINE:
{project.timeline}


=========================================================
AI PROJECT DESCRIPTION
=========================================================

OVERVIEW:
{project.overview or "Not available."}

PROPOSED SOLUTION:
{project.proposed_solution or "Not available."}

MAJOR FEATURES:
{project.major_features or "Not available."}

EXPECTED OUTCOME:
{project.expected_outcome or "Not available."}


=========================================================
PRD
=========================================================

PRODUCT OVERVIEW:
{project.product_overview or "Not available."}

PRD PROBLEM STATEMENT:
{project.prd_problem_statement or project.problem_statement or "Not available."}

GOALS AND OBJECTIVES:
{project.goals_and_objectives or "Not available."}

TARGET USERS:
{project.prd_target_users or project.target_users or "Not available."}

FUNCTIONAL REQUIREMENTS:
{project.functional_requirements or "Not available."}

USER WORKFLOWS:
{project.user_workflows or "Not available."}

BUSINESS RULES:
{project.business_rules or "Not available."}

NON-FUNCTIONAL REQUIREMENTS:
{project.non_functional_requirements or "Not available."}

ASSUMPTIONS AND DEPENDENCIES:
{project.assumptions_and_dependencies or "Not available."}

ACCEPTANCE CRITERIA:
{project.acceptance_criteria or "Not available."}


=========================================================
TASK GENERATION REQUIREMENTS
=========================================================

Generate approximately 10 to 15 implementation tasks.

Tasks should cover the actual development work required
for the supplied project.

Organize tasks logically across areas such as:

- Project setup
- Backend
- Frontend
- Database
- AI/ML functionality
- API integration
- Testing
- Deployment

Only include areas that are actually relevant to the
provided project.


=========================================================
IMPORTANT RULES
=========================================================

1. Use ONLY the supplied project and PRD information.
2. Do not invent unrelated features.
3. Do not invent unsupported technologies.
4. Do not create tasks for functionality that is not required.
5. Tasks must be specific to this project.
6. Tasks should be implementation-oriented.
7. Respect the stated technology preferences.
8. Respect the project timeline.
9. Create tasks in a logical dependency order.
10. Foundational tasks should come before dependent tasks.
11. Each task must have a clear purpose.
12. Return ONLY valid JSON.
13. Do not use Markdown code fences.
14. Do not add explanations outside the JSON.


=========================================================
RETURN EXACTLY THIS JSON STRUCTURE
=========================================================

[
    {{
        "task_title": "...",
        "description": "...",
        "task_type": "...",
        "module": "...",
        "priority": "...",
        "acceptance_criteria": "...",
        "owner_role": "...",
        "dependencies": "...",
        "estimated_complexity": "..."
    }}
]
"""


# =========================================================
# TASK GENERATOR
# =========================================================

class TaskGenerator:

    def generate_tasks(self, project):

        prompt = task_prompt(project)

        print(
            "TASK PROMPT LENGTH:",
            len(prompt)
        )

        response = llm.generate(prompt)

        try:

            response = response.strip()

            # -------------------------------------------------
            # Remove Markdown code fences if present
            # -------------------------------------------------

            if response.startswith("```"):

                response = response.replace(
                    "```json",
                    ""
                ).replace(
                    "```",
                    ""
                ).strip()

            # -------------------------------------------------
            # Parse JSON
            # -------------------------------------------------

            data = json.loads(response)

            # -------------------------------------------------
            # Validate response type
            # -------------------------------------------------

            if not isinstance(data, list):

                raise RuntimeError(
                    "Task generator must return a JSON array."
                )

            # -------------------------------------------------
            # Required task fields
            # -------------------------------------------------

            required_fields = [
                "task_title",
                "description",
                "task_type",
                "module",
                "priority",
                "acceptance_criteria",
                "owner_role",
                "dependencies",
                "estimated_complexity"
            ]

            # -------------------------------------------------
            # Validate every task
            # -------------------------------------------------

            for index, task in enumerate(data):

                if not isinstance(task, dict):

                    raise RuntimeError(
                        f"Task {index + 1} is not a valid object."
                    )

                for field in required_fields:

                    if field not in task:

                        raise RuntimeError(
                            f"Task {index + 1} missing field: {field}"
                        )

            return data

        except json.JSONDecodeError as e:

            print(
                "TASK JSON ERROR:",
                e
            )

            print(
                "RAW AI RESPONSE:",
                response
            )

            raise RuntimeError(
                "AI returned invalid JSON for task generation."
            )


# =========================================================
# INSTANCE
# =========================================================

task_generator = TaskGenerator()
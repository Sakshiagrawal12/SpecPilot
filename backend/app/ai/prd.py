import json

from app.ai.llm import llm


# =========================================================
# PRD PROMPT
# =========================================================

def prd_prompt(project):

    return f"""
You are a Senior Product Manager creating a Software Product
Requirements Document (PRD).

Your job is to convert the supplied project information into
a professional and project-specific PRD.

Use ONLY the information provided below.

=========================================================
ORIGINAL PROJECT INFORMATION
=========================================================

PROJECT NAME:
{project.project_name}

CATEGORY:
{project.category}

BUSINESS OBJECTIVE:
{project.business_objective}

TARGET USERS:
{project.target_users}

PROBLEM STATEMENT:
{project.problem_statement}

EXPECTED FEATURES:
{project.expected_features}

TECHNOLOGY PREFERENCES:
{project.technology_preferences}

TIMELINE:
{project.timeline}

ADDITIONAL INSTRUCTIONS:
{project.additional_instructions or "None"}


=========================================================
AI GENERATED PROJECT DESCRIPTION
=========================================================

OVERVIEW:
{project.overview or "Not generated yet."}

AI PROBLEM STATEMENT:
{project.ai_problem_statement or "Not generated yet."}

PROPOSED SOLUTION:
{project.proposed_solution or "Not generated yet."}

TARGET AUDIENCE:
{project.target_audience or "Not generated yet."}

BUSINESS VALUE:
{project.business_value or "Not generated yet."}

MAJOR FEATURES:
{project.major_features or "Not generated yet."}

EXPECTED OUTCOME:
{project.expected_outcome or "Not generated yet."}


=========================================================
PRD REQUIREMENTS
=========================================================

Create a detailed PRD specific to this project.

The PRD must clearly describe:

1. Product overview
2. Problem being solved
3. Goals and objectives
4. Target users
5. Functional requirements
6. User workflows
7. Business rules
8. Non-functional requirements
9. Assumptions and dependencies
10. Acceptance criteria


=========================================================
IMPORTANT RULES
=========================================================

1. Use ONLY the supplied project information.
2. Do not invent unsupported features.
3. Do not invent unsupported technologies.
4. Do not invent unsupported users.
5. Do not invent business requirements.
6. Do not introduce unrelated functionality.
7. Keep all requirements specific to this project.
8. Use the original project information as the source of truth.
9. The AI-generated description may be used to professionally organize
   the information, but it must not introduce unsupported requirements.
10. Keep the PRD internally consistent.
11. Return ONLY valid JSON.
12. Do not use Markdown code fences.
13. Do not add explanations before or after the JSON.


=========================================================
RETURN EXACTLY THIS JSON STRUCTURE
=========================================================

{{
    "product_overview": "...",
    "problem_statement": "...",
    "goals_and_objectives": "...",
    "target_users": "...",
    "functional_requirements": "...",
    "user_workflows": "...",
    "business_rules": "...",
    "non_functional_requirements": "...",
    "assumptions_and_dependencies": "...",
    "acceptance_criteria": "..."
}}
"""


# =========================================================
# PRD GENERATOR
# =========================================================

class PRDGenerator:

    def generate_prd(self, project):

        prompt = prd_prompt(project)

        print(
            "PRD PROMPT LENGTH:",
            len(prompt)
        )

        response = llm.generate(prompt)

        try:

            response = response.strip()

            # -------------------------------------------------
            # Remove Markdown code fences if the LLM adds them
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
            # Validate required fields
            # -------------------------------------------------

            required_fields = [
                "product_overview",
                "problem_statement",
                "goals_and_objectives",
                "target_users",
                "functional_requirements",
                "user_workflows",
                "business_rules",
                "non_functional_requirements",
                "assumptions_and_dependencies",
                "acceptance_criteria"
            ]

            for field in required_fields:

                if field not in data:

                    raise RuntimeError(
                        f"PRD missing field: {field}"
                    )

            return data

        except json.JSONDecodeError as e:

            print(
                "PRD JSON ERROR:",
                e
            )

            print(
                "RAW AI RESPONSE:",
                response
            )

            raise RuntimeError(
                "AI returned invalid JSON for PRD generation."
            )


# =========================================================
# INSTANCE
# =========================================================

prd_generator = PRDGenerator()
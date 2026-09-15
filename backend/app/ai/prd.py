
import json

from app.ai.llm import llm


# =========================================================
# PRD PROMPT
# =========================================================

def prd_prompt(project, requirements):

    def get_requirement(field):

        field_data = requirements.get(
            field,
            {}
        )

        value = field_data.get("value")

        if value is None:
            return "Not specified"

        if isinstance(value, list):

            return "\n".join(
                f"- {item}"
                for item in value
            )

        if isinstance(value, dict):

            return json.dumps(
                value,
                ensure_ascii=False
            )

        return str(value)


    return f"""
You are a Senior Product Manager creating a professional
Software Product Requirements Document (PRD).

Your job is to transform the requirements collected from
the user through the SpecPilot requirement interview into
a clear, structured and project-specific PRD.

The user's collected requirements are the PRIMARY SOURCE
OF TRUTH.

You may improve wording, organization, clarity and structure,
but you MUST NOT invent unsupported requirements.

=========================================================
PROJECT
=========================================================

PROJECT NAME:
{project.project_name}

=========================================================
USER-COLLECTED REQUIREMENTS
=========================================================

CATEGORY:
{get_requirement("category")}

BUSINESS OBJECTIVE:
{get_requirement("business_objective")}

TARGET USERS:
{get_requirement("target_users")}

PROBLEM STATEMENT:
{get_requirement("problem_statement")}

EXPECTED FEATURES:
{get_requirement("expected_features")}

TECHNOLOGY PREFERENCES:
{get_requirement("technology_preferences")}

TIMELINE:
{get_requirement("timeline")}

ADDITIONAL INSTRUCTIONS:
{get_requirement("additional_instructions")}


=========================================================
EXISTING PROJECT INFORMATION
=========================================================

PROJECT DESCRIPTION:
{project.overview or "Not specified"}

AI PROBLEM STATEMENT:
{project.ai_problem_statement or "Not specified"}

PROPOSED SOLUTION:
{project.proposed_solution or "Not specified"}

TARGET AUDIENCE:
{project.target_audience or "Not specified"}

BUSINESS VALUE:
{project.business_value or "Not specified"}

MAJOR FEATURES:
{project.major_features or "Not specified"}

EXPECTED OUTCOME:
{project.expected_outcome or "Not specified"}


=========================================================
PRD SECTIONS
=========================================================

Generate the following sections:

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


=========================================================
IMPORTANT RULES
=========================================================

1. The user's collected requirements are the source of truth.

2. Refine the user's wording professionally.

3. Improve clarity and organization where appropriate.

4. Do NOT invent unsupported features.

5. Do NOT invent unsupported technologies.

6. Do NOT invent unsupported users.

7. Do NOT invent business rules.

8. Do NOT introduce unrelated functionality.

9. Every functional requirement must be traceable
   to the supplied project requirements.

10. Technology preferences must only contain technologies
    explicitly supplied by the user or existing project
    information.

11. If information is genuinely missing, write:
    "Not specified"

12. Keep the PRD internally consistent.

13. The acceptance criteria must correspond to the
    functional requirements.

14. User workflows must correspond to the supplied
    expected features.

15. Return ONLY valid JSON.

16. Do NOT use Markdown code fences.

17. Do NOT add explanations before or after the JSON.


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

    def generate_prd(
        self,
        project,
        requirements
    ):

        prompt = prd_prompt(
            project,
            requirements
        )

        print(
            "========================================"
        )

        print(
            "GENERATING PRD"
        )

        print(
            "PROJECT:",
            project.project_name
        )

        print(
            "PRD PROMPT LENGTH:",
            len(prompt)
        )

        print(
            "========================================"
        )

        response = llm.generate(prompt)

        try:

            response = response.strip()

            # -------------------------------------------------
            # Remove Markdown code fences
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


import json

from app.ai.llm import llm


def project_description_prompt(project):

    return f"""
You are a Senior Product Manager and Business Analyst.

Generate a professional project description for the software project below.

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

IMPORTANT RULES:

1. Use ONLY the information provided above.
2. Do not invent features, technologies, users, or requirements.
3. Do not add unsupported information.
4. Expand the supplied information professionally.
5. Make the content specific to this project.
6. Do not use generic marketing language.
7. Return ONLY valid JSON.
8. Do not use Markdown code fences.
9. Do not add any explanation before or after the JSON.

Return JSON using EXACTLY this structure:

{{
    "overview": "...",
    "problem_statement": "...",
    "proposed_solution": "...",
    "target_audience": "...",
    "business_value": "...",
    "major_features": "...",
    "expected_outcome": "..."
}}
"""


class DescriptionGenerator:

    def generate(self, project):

        prompt = project_description_prompt(project)

        print(
            "DESCRIPTION PROMPT LENGTH:",
            len(prompt)
        )

        response = llm.generate(prompt)

        try:

            response = response.strip()

            if response.startswith("```"):
                response = response.replace(
                    "```json",
                    ""
                ).replace(
                    "```",
                    ""
                ).strip()

            data = json.loads(response)

            required_fields = [
                "overview",
                "problem_statement",
                "proposed_solution",
                "target_audience",
                "business_value",
                "major_features",
                "expected_outcome"
            ]

            for field in required_fields:

                if field not in data:
                    raise RuntimeError(
                        f"Description missing field: {field}"
                    )

            return data

        except json.JSONDecodeError as e:

            print(
                "DESCRIPTION JSON ERROR:",
                e
            )

            print(
                "RAW AI RESPONSE:",
                response
            )

            raise RuntimeError(
                "AI returned invalid JSON for description generation."
            )


description_generator = DescriptionGenerator()

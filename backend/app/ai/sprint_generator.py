
from app.ai.llm import llm


def sprint_prompt(project, tasks):

    return f"""
You are a Senior Agile Project Manager.

Create a practical sprint plan for this software project.

PROJECT:
{project.project_name}

OBJECTIVE:
{project.business_objective}

TIMELINE:
{project.timeline}

TECHNOLOGY:
{project.technology_preferences}

PROJECT TASKS:
{tasks}

Organize the supplied tasks into logical development sprints.

Rules:

1. Use ONLY the supplied project and tasks.
2. Do not invent unrelated features.
3. Prioritize foundational work before dependent work.
4. Keep the sprint sequence realistic.
5. Use the supplied timeline.
6. Every sprint must contain relevant tasks.
7. Return ONLY the final sprint plan.
8. Use Markdown headings.

For each sprint use:

# Sprint Name

## Sprint Goal

## Tasks

## Deliverables

## Dependencies

## Definition of Done
"""


class SprintGenerator:

    def generate_sprint_plan(
        self,
        project,
        tasks
    ):

        prompt = sprint_prompt(
            project,
            tasks
        )

        print(
            "SPRINT PROMPT LENGTH:",
            len(prompt)
        )

        return llm.generate(prompt)


sprint_generator = SprintGenerator()

"""
Each node here wraps ONE of your existing app/ai/ generators as a
pipeline stage. The prompts and generation logic already live in
app.ai.description / app.ai.prd / app.ai.task_generator /
app.ai.sprint_generator — nothing here duplicates that. This file is
just the sequencing, error handling, and state hand-off between stages
that app/routers/ai.py currently does by hand across four separate
endpoints.
"""

from typing import Any, Dict

from app.agents.generation_manager.state import GenerationState

from app.ai.description import description_generator
from app.agents.generation_manager.agents.prd_agent.graph import (
    prd_agent,
)
from app.agents.generation_manager.agents.task_agent.graph import (
    task_agent,
)
from app.agents.generation_manager.agents.sprint_agent.graph import (
    sprint_agent,
)
# =========================================================
# STAGE: DESCRIPTION
# =========================================================

def generate_description(
    state: GenerationState,
) -> Dict[str, Any]:

    project = state["project"]

    try:

        description = description_generator.generate(
            project
        )

    except Exception as exc:

        return {
            "stage": "description",
            "status": "failed",
            "error": (
                f"Description generation failed: {exc}"
            ),
        }

    return {
        "stage": "description",
        "description": description,
        "status": "in_progress",
        "error": None,
    }

# =========================================================
# STAGE: PRD
# =========================================================
def generate_prd(state: GenerationState) -> Dict[str, Any]:

    project = state["project"]
    requirements = state.get("requirements", {})

    try:

        result = prd_agent.invoke(
            {
                "project": project,
                "requirements": requirements,
                "revision_count": 0,
                "status": "in_progress",
            }
        )

    except Exception as e:

        return {
            "stage": "prd",
            "status": "failed",
            "error": f"PRD generation failed: {e}",
        }

    if result.get("status") == "failed":

        return {
            "stage": "prd",
            "status": "failed",
            "error": result.get(
                "error",
                "PRD Agent failed."
            ),
        }

    return {
        "stage": "prd",
        "prd": result.get("prd"),
        "status": "in_progress",
    }

# =========================================================
# STAGE: TASKS
# =========================================================

def generate_tasks(state: GenerationState) -> Dict[str, Any]:

    project = state["project"]

    requirements = state.get(
        "requirements",
        {},
    )

    prd = state.get(
        "prd",
    )

    if not prd:
        return {
            "stage": "tasks",
            "status": "failed",
            "error": "Cannot generate tasks because PRD is missing.",
        }

    try:

        result = task_agent.invoke(
            {
                "project": project,
                "requirements": requirements,
                "prd": prd,
                "revision_count": 0,
                "status": "in_progress",
            }
        )

    except Exception as exc:

        return {
            "stage": "tasks",
            "status": "failed",
            "error": f"Task Agent failed: {exc}",
        }

    if result.get("status") == "failed":

        return {
            "stage": "tasks",
            "status": "failed",
            "error": result.get(
                "error",
                "Task Agent failed.",
            ),
        }

    tasks = result.get(
        "tasks",
        [],
    )

    if not isinstance(tasks, list):

        return {
            "stage": "tasks",
            "status": "failed",
            "error": "Task Agent did not return a task list.",
        }

    return {
        "stage": "tasks",
        "tasks": tasks,
        "status": "in_progress",
    }

# =========================================================
# STAGE: SPRINT PLAN
# =========================================================

def generate_sprint(
    state: GenerationState,
) -> Dict[str, Any]:

    project = state["project"]

    tasks = state.get(
        "tasks",
        [],
    )

    prd = state.get(
        "prd",
        {},
    )

    if not tasks:

        return {
            "stage": "sprint",
            "status": "failed",
            "error": "Cannot generate sprint plan because tasks are missing.",
        }

    try:

        result = sprint_agent.invoke(
            {
                "project": project,
                "prd": prd,
                "tasks": tasks,
                "revision_count": 0,
                "status": "in_progress",
            }
        )

    except Exception as exc:

        return {
            "stage": "sprint",
            "status": "failed",
            "error": f"Sprint Agent failed: {exc}",
        }

    if result.get("status") == "failed":

        return {
            "stage": "sprint",
            "status": "failed",
            "error": result.get(
                "error",
                "Sprint Agent failed.",
            ),
        }

    sprint_plan = result.get(
        "sprint_plan"
    )

    if not sprint_plan:

        return {
            "stage": "sprint",
            "status": "failed",
            "error": "Sprint Agent did not return a sprint plan.",
        }

    return {
        "stage": "done",
        "sprint_plan": sprint_plan,
        "status": "complete",
        "error": None,
    }

# =========================================================
# ROUTING — stop the pipeline early if any stage failed
# =========================================================

def route_after_stage(state: GenerationState) -> str:

    if state.get("status") == "failed":
        return "failed"

    return "continue"

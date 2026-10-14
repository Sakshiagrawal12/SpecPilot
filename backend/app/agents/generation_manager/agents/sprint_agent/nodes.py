from typing import Any, Dict

from .state import SprintState

from .agents.priority_agent import (
    priority_agent,
)

from .agents.capacity_agent import (
    capacity_agent,
)

from .agents.dependency_agent import (
    dependency_agent,
)

from .agents.sprint_review_agent import (
    sprint_review_agent,
)


def analyze_priority(
    state: SprintState,
) -> Dict[str, Any]:

    try:

        result = priority_agent.prioritize(
            tasks=state["tasks"],
        )

        return {
            "prioritized_tasks": result,
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "status": "failed",
            "error": f"Priority analysis failed: {exc}",
        }


def analyze_capacity(
    state: SprintState,
) -> Dict[str, Any]:

    try:

        result = capacity_agent.plan_capacity(
            tasks=state["prioritized_tasks"],
            project=state["project"],
        )

        return {
            "capacity_plan": result,
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "status": "failed",
            "error": f"Capacity planning failed: {exc}",
        }


def analyze_dependencies(
    state: SprintState,
) -> Dict[str, Any]:

    try:

        result = dependency_agent.analyze(
            tasks=state["prioritized_tasks"],
        )

        return {
            "dependency_plan": result,
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "status": "failed",
            "error": f"Dependency analysis failed: {exc}",
        }


def build_sprint_plan(
    state: SprintState,
) -> Dict[str, Any]:

    capacity_plan = state.get(
        "capacity_plan",
        {},
    )

    # Safe retrieval with fallback
    dependency_plan = state.get("dependency_plan") or {}

    if not dependency_plan:
        # If dependency plan wasn't produced by the preceding node, handle gracefully
        dependency_plan = {
            "status": "warning",
            "message": "No dependency plan provided; proceeding with default task sequencing.",
            "dependencies": []
        }

    return {
        "sprint_plan": {
            "sprints": capacity_plan.get(
                "sprints",
                [],
            ),
            "capacity_assumptions": capacity_plan.get(
                "capacity_assumptions",
                [],
            ),
            "dependencies": dependency_plan.get(
                "dependencies",
                [],
            ),
            "independent_tasks": dependency_plan.get(
                "independent_tasks",
                [],
            ),
        },
        "status": "in_progress",
        "error": None,
    }


def review_sprint_plan(
    state: SprintState,
) -> Dict[str, Any]:

    try:

        result = sprint_review_agent.review(
            tasks=state["tasks"],
            prioritized_tasks=state["prioritized_tasks"],
            capacity_plan=state["capacity_plan"],
            dependency_plan=state["dependency_plan"],
        )

        return {
            "review": result,
            "review_status": result["status"],
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "status": "failed",
            "error": f"Sprint review failed: {exc}",
        }


MAX_REVISIONS = 2


def route_after_review(
    state: SprintState,
) -> str:

    if state.get("status") == "failed":
        return "failed"

    if state.get("review_status") == "PASS":
        return "approved"

    revision_count = state.get(
        "revision_count",
        0,
    )

    if revision_count >= MAX_REVISIONS:
        return "failed"

    return "revise"


def prepare_revision(
    state: SprintState,
) -> Dict[str, Any]:

    return {
        "revision_count": state.get(
            "revision_count",
            0,
        ) + 1,
        "status": "in_progress",
    }
from typing import Any, Dict

from app.agents.orchestrator.state import OrchestratorState
from app.agents.requirement_manager.runner import (
    process_requirement_message,
)


def run_requirement_manager(
    state: OrchestratorState,
) -> Dict[str, Any]:

    result = process_requirement_message(
        user_message=state.get("user_message", ""),
        requirements=state.get("requirements", {}),
        project_id=state.get("project_id"),
        project_name=state.get("project_name"),
    )

    next_action = result.get(
        "next_action",
        "wait_for_user",
    )

    return {
        "requirements": result.get(
            "requirements",
            {},
        ),

        # These two were previously dropped entirely — nothing wrote
        # them into OrchestratorState, so every caller reading them
        # got whatever default it fell back to (None / []).
        "current_field": result.get(
            "current_field",
        ),

        "missing_fields": result.get(
            "missing_fields",
            [],
        ),

        "requirements_status": result.get(
            "completeness_status",
            "INCOMPLETE",
        ),

        "requirements_score": result.get(
            "completeness_score",
            0.0,
        ),

        "agent_response": result.get(
            "agent_response",
            "",
        ),

        "next_action": next_action,

        "active_manager": (
            "generation_manager"
            if next_action == "generate_prd"
            else "requirement_manager"
        ),

        "workflow_status": (
            "READY"
            if next_action == "generate_prd"
            else "RUNNING"
        ),
    }


def route_after_requirement_manager(
    state: OrchestratorState,
) -> str:

    if state.get("next_action") == "generate_prd":
        return "complete"

    return "continue"

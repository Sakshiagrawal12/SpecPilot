from typing import Dict, Any

from app.agents.orchestrator.graph import (
    orchestrator_graph,
)


def process_session_turn(
    user_message: str,
    requirements: Dict[str, Any],
    project_id: int | None = None,
    project_name: str | None = None,
) -> Dict[str, Any]:

    state = {
        "user_message": user_message,
        "requirements": requirements,
        "active_manager": "requirement_manager",
        "workflow_status": "RUNNING",
    }

    if project_id is not None:
        state["project_id"] = project_id

    if project_name:
        state["project_name"] = project_name

    result = orchestrator_graph.invoke(state)

    return result
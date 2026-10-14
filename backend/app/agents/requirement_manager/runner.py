from typing import Dict, Any

from app.agents.requirement_manager.graph import (
    requirement_manager_graph,
)


def process_requirement_message(
    user_message: str,
    requirements: Dict[str, Any],
    project_id: int | None = None,
    project_name: str | None = None,
) -> Dict[str, Any]:

    state = {
        "user_message": user_message,
        "requirements": requirements,
        "messages": [],
    }

    if project_id is not None:
        state["project_id"] = project_id

    if project_name:
        state["project_name"] = project_name

    result = requirement_manager_graph.invoke(state)

    return result
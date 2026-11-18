from typing import Dict, Any, Optional

from app.agents.requirement_manager.graph import (
    requirement_manager_graph,
)


def process_requirement_message(
    user_message: str,
    requirements: Dict[str, Any],
    project_id: int | None = None,
    project_name: str | None = None,
    pending_confirmation: bool = False,
    pending_generated_field: Optional[str] = None,
    pending_generated_value: Optional[str] = None,
) -> Dict[str, Any]:

    state = {
        "user_message": user_message,
        "requirements": requirements,
        "messages": [],

        # Pending generated-suggestion state
        "pending_confirmation": pending_confirmation,
        "pending_generated_field": pending_generated_field,
        "pending_generated_value": pending_generated_value,
    }

    if project_id is not None:
        state["project_id"] = project_id

    if project_name:
        state["project_name"] = project_name

    result = requirement_manager_graph.invoke(state)

    return result
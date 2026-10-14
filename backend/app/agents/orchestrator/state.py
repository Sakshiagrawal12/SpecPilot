from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class OrchestratorState(TypedDict, total=False):

    # Session
    project_id: int
    thread_id: str
    project_name: str

    # Current user input
    user_message: str

    # Current manager
    active_manager: str

    # Overall workflow
    workflow_status: str
    next_action: str

    # Requirement Manager output
    requirements: Dict[str, Any]
    requirements_status: str
    requirements_score: float

    # These two were missing — Requirement Manager's own graph always
    # produces them (RequirementState has both), but with no field
    # declared here to carry them, every caller reading
    # result["current_field"] / result["missing_fields"] from the
    # orchestrator's output got nothing back.
    current_field: Optional[str]
    missing_fields: List[str]

    # Manager response
    agent_response: str

    # Future managers
    generated_artifacts: Dict[str, Any]
    verification_results: Dict[str, Any]

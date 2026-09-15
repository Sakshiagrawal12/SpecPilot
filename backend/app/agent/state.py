from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


# =========================================================
# REQUIREMENT FIELD
# =========================================================

class RequirementField(TypedDict, total=False):

    value: Optional[Any]

    status: str

    confidence: float


# =========================================================
# PROJECT REQUIREMENTS
# =========================================================

class ProjectRequirements(TypedDict, total=False):

    project_name: RequirementField

    business_objective: RequirementField

    problem_statement: RequirementField

    target_users: RequirementField

    expected_features: RequirementField

    technology_preferences: RequirementField

    timeline: RequirementField

    additional_instructions: RequirementField


# =========================================================
# AGENT STATE
# =========================================================

class AgentState(TypedDict, total=False):

    field_attempts: Dict[str, int]

    needs_clarification: bool

    # -----------------------------------------------------
    # PROJECT
    # -----------------------------------------------------

    project_id: int

    project_name: str

    # -----------------------------------------------------
    # CONVERSATION
    # -----------------------------------------------------

    conversation_id: int

    messages: List[Dict[str, str]]

    # -----------------------------------------------------
    # LATEST USER MESSAGE
    # -----------------------------------------------------

    user_message: str

    # -----------------------------------------------------
    # CURRENT INTERVIEW FIELD
    # -----------------------------------------------------

    current_field: str

    # -----------------------------------------------------
    # STRUCTURED REQUIREMENTS
    # -----------------------------------------------------

    requirements: ProjectRequirements

    # -----------------------------------------------------
    # EVALUATION
    # -----------------------------------------------------

    missing_fields: List[str]

    completeness_status: str

    completeness_score: float

    # -----------------------------------------------------
    # AGENT RESPONSE
    # -----------------------------------------------------

    agent_response: str

    next_action: str
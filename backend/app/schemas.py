from typing import Optional

from pydantic import BaseModel, ConfigDict


# =========================================================
# USER / AUTH
# =========================================================

class SignupRequest(BaseModel):

    name: str

    email: str

    password: str


class LoginRequest(BaseModel):

    email: str

    password: str


# =========================================================
# PROJECT CREATE
# =========================================================

class ProjectCreate(BaseModel):

    project_name: str

    category: Optional[str] = None

    business_objective: Optional[str] = None

    target_users: Optional[str] = None

    problem_statement: Optional[str] = None

    expected_features: Optional[str] = None

    technology_preferences: Optional[str] = None

    timeline: Optional[str] = None

    additional_instructions: Optional[str] = None


# =========================================================
# PROJECT UPDATE
# =========================================================

class ProjectUpdate(BaseModel):

    project_name: Optional[str] = None

    category: Optional[str] = None

    business_objective: Optional[str] = None

    target_users: Optional[str] = None

    problem_statement: Optional[str] = None

    expected_features: Optional[str] = None

    technology_preferences: Optional[str] = None

    timeline: Optional[str] = None

    additional_instructions: Optional[str] = None


# =========================================================
# AI DESCRIPTION RESPONSE
# =========================================================

class DescriptionResponse(BaseModel):

    overview: str = ""

    problem_statement: str = ""

    proposed_solution: str = ""

    target_audience: str = ""

    business_value: str = ""

    major_features: str = ""

    expected_outcome: str = ""


# =========================================================
# PRD RESPONSE
# =========================================================

class PRDResponse(BaseModel):

    product_overview: str = ""

    problem_statement: str = ""

    goals_and_objectives: str = ""

    target_users: str = ""

    functional_requirements: str = ""

    user_workflows: str = ""

    business_rules: str = ""

    non_functional_requirements: str = ""

    assumptions_and_dependencies: str = ""

    acceptance_criteria: str = ""


# =========================================================
# TASK CREATE
# =========================================================

class TaskCreate(BaseModel):

    task_title: str

    description: Optional[str] = None

    task_type: Optional[str] = None

    module: Optional[str] = None

    priority: Optional[str] = None

    acceptance_criteria: Optional[str] = None

    owner_role: Optional[str] = None

    dependencies: Optional[str] = None

    estimated_complexity: Optional[str] = None

    status: Optional[str] = "Todo"

    source: Optional[str] = "manual"


# =========================================================
# TASK UPDATE
# =========================================================

class TaskUpdate(BaseModel):

    task_title: Optional[str] = None

    description: Optional[str] = None

    task_type: Optional[str] = None

    module: Optional[str] = None

    priority: Optional[str] = None

    acceptance_criteria: Optional[str] = None

    owner_role: Optional[str] = None

    dependencies: Optional[str] = None

    estimated_complexity: Optional[str] = None

    status: Optional[str] = None

    source: Optional[str] = None


# =========================================================
# TASK RESPONSE
# =========================================================

class TaskResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    project_id: int

    task_title: str

    description: Optional[str] = None

    task_type: Optional[str] = None

    module: Optional[str] = None

    priority: Optional[str] = None

    acceptance_criteria: Optional[str] = None

    owner_role: Optional[str] = None

    dependencies: Optional[str] = None

    estimated_complexity: Optional[str] = None

    status: str

    source: str


# =========================================================
# PROJECT RESPONSE
# =========================================================

class ProjectResponse(ProjectCreate):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    user_id: int

    # -----------------------------------------------------
    # AI DESCRIPTION
    # -----------------------------------------------------

    overview: Optional[str] = None

    ai_problem_statement: Optional[str] = None

    proposed_solution: Optional[str] = None

    target_audience: Optional[str] = None

    business_value: Optional[str] = None

    major_features: Optional[str] = None

    expected_outcome: Optional[str] = None

    # -----------------------------------------------------
    # AI PRD
    # -----------------------------------------------------

    product_overview: Optional[str] = None

    prd_problem_statement: Optional[str] = None

    goals_and_objectives: Optional[str] = None

    prd_target_users: Optional[str] = None

    functional_requirements: Optional[str] = None

    user_workflows: Optional[str] = None

    business_rules: Optional[str] = None

    non_functional_requirements: Optional[str] = None

    assumptions_and_dependencies: Optional[str] = None

    acceptance_criteria: Optional[str] = None

    # -----------------------------------------------------
    # SPRINT
    # -----------------------------------------------------

    sprint_plan: Optional[str] = None


# =========================================================
# FEEDBACK
# =========================================================

class FeedbackCreate(BaseModel):

    project_id: int

    rating: Optional[int] = None

    feedback: Optional[str] = None


class FeedbackResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True
    )

    id: int

    project_id: int

    rating: Optional[int] = None

    feedback: Optional[str] = None
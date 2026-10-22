"""
Exposes Generation Manager as one endpoint instead of the four separate
generate-description / generate-prd / generate-tasks / generate-sprint
calls in app/routers/ai.py.

Those four still work independently if you need to re-run just one stage.
This endpoint runs the complete generation pipeline once the Requirement
Manager signals that requirements are complete.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Project, Task, ProjectRequirement
from app.agents.generation_manager.runner import run_generation
from app.services.prd_format import to_readable

router = APIRouter(
    prefix="/generation",
    tags=["generation"]
)


# ============================================================
# HELPERS
# ============================================================

def to_text(value) -> str:
    """Structured values are saved as readable plain text."""
    return to_readable(value)


def get_project_or_404(
    project_id: int,
    db: Session
) -> Project:

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found."
        )

    return project


# ============================================================
# FULL GENERATION PIPELINE
# ============================================================

@router.post("/run/{project_id}")
def run_generation_pipeline(
    project_id: int,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # Get project
    # --------------------------------------------------------

    project = get_project_or_404(
        project_id,
        db
    )

    # --------------------------------------------------------
    # Get requirements
    # --------------------------------------------------------

    requirement_record = (
        db.query(ProjectRequirement)
        .filter(
            ProjectRequirement.project_id == project_id
        )
        .first()
    )

    if (
        not requirement_record
        or requirement_record.completeness_status != "COMPLETE"
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "Requirements are incomplete - "
                "finish the requirement interview "
                "before generating."
            )
        )

    # --------------------------------------------------------
    # Run Generation Manager
    # --------------------------------------------------------

    result = run_generation(
        project=project,
        requirements=(
            requirement_record.requirements or {}
        )
    )

    if result.get("status") == "failed":

        raise HTTPException(
            status_code=500,
            detail=result.get(
                "error",
                "Generation failed."
            )
        )

    # ========================================================
    # SAVE DESCRIPTION
    # ========================================================

    description = result.get("description") or {}

    project.overview = to_text(description.get("overview"))
    project.ai_problem_statement = to_text(description.get("problem_statement"))
    project.proposed_solution = to_text(description.get("proposed_solution"))
    project.target_audience = to_text(description.get("target_audience"))
    project.business_value = to_text(description.get("business_value"))
    project.major_features = to_text(description.get("major_features"))
    project.expected_outcome = to_text(description.get("expected_outcome"))

    # ========================================================
    # SAVE PRD
    # ========================================================

    prd = result.get("prd") or {}

    project.product_overview = to_text(prd.get("product_overview"))
    project.prd_problem_statement = to_text(prd.get("problem_statement"))
    project.goals_and_objectives = to_text(prd.get("goals_and_objectives"))
    project.prd_target_users = to_text(prd.get("target_users"))
    project.functional_requirements = to_text(prd.get("functional_requirements"))
    project.user_workflows = to_text(prd.get("user_workflows"))
    project.business_rules = to_text(prd.get("business_rules"))
    project.non_functional_requirements = to_text(prd.get("non_functional_requirements"))
    project.assumptions_and_dependencies = to_text(prd.get("assumptions_and_dependencies"))
    project.acceptance_criteria = to_text(prd.get("acceptance_criteria"))

    # ========================================================
    # SAVE PROJECT CHANGES
    # ========================================================

    try:

        db.commit()
        db.refresh(project)

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save generated "
                f"PRD/description: {exc}"
            )
        )

    # ========================================================
    # DELETE OLD AI TASKS
    # ========================================================

    existing_ai_tasks = (
        db.query(Task)
        .filter(
            Task.project_id == project_id,
            Task.source == "ai"
        )
        .all()
    )

    for task in existing_ai_tasks:
        db.delete(task)

    db.flush()

    # ========================================================
    # SAVE NEW AI TASKS
    # ========================================================

    created_tasks = []

    for index, task_data in enumerate(
        result.get("tasks") or [],
        start=1
    ):

        # ----------------------------------------------------
        # Dependencies
        # ----------------------------------------------------

        dependencies = task_data.get(
            "dependencies",
            []
        )

        if not isinstance(
            dependencies,
            str
        ):
            dependencies = json.dumps(
                dependencies,
                ensure_ascii=False
            )

        # ----------------------------------------------------
        # Create Task
        # ----------------------------------------------------

        task = Task(
            project_id=project_id,

            task_title=task_data.get(
                "task_title",
                f"Task {index}"
            ),

            description=to_text(
                task_data.get("description")
            ),

            task_type=task_data.get(
                "task_type",
                ""
            ),

            module=task_data.get(
                "module",
                ""
            ),

            priority=task_data.get(
                "priority",
                "Medium"
            ),

            acceptance_criteria=to_text(
                task_data.get("acceptance_criteria")
            ),

            owner_role=task_data.get(
                "owner_role",
                ""
            ),

            dependencies=dependencies,

            estimated_complexity=task_data.get(
                "estimated_complexity",
                ""
            ),

            status="Todo",

            source="ai",
        )

        db.add(task)

        created_tasks.append(task)

    # ========================================================
    # SAVE SPRINT PLAN
    # ========================================================

    sprint_plan = result.get(
        "sprint_plan"
    )

    if isinstance(
        sprint_plan,
        (dict, list)
    ):

        project.sprint_plan = json.dumps(
            sprint_plan,
            ensure_ascii=False,
            indent=2
        )

    else:

        project.sprint_plan = str(
            sprint_plan
        )

    # --------------------------------------------------------
    # Commit tasks + sprint plan
    # --------------------------------------------------------

    try:

        db.commit()

        for task in created_tasks:
            db.refresh(task)

        db.refresh(project)

    except Exception as exc:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to save generated "
                f"tasks/sprint plan: {exc}"
            )
        )

    # ========================================================
    # RESPONSE
    # ========================================================

    return {
        "status": "success",
        "project_id": project.id,
        "description": description,
        "prd": prd,
        "tasks_created": len(created_tasks),
        "sprint_plan": project.sprint_plan,
    }
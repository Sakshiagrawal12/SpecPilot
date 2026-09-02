from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import json

from app.database import get_db
from app.models import Project, Task

from app.ai.description import description_generator
from app.ai.prd import prd_generator
from app.ai.task_generator import task_generator
from app.ai.sprint_generator import sprint_generator


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


# =========================================================
# HELPER
# =========================================================

def get_project_or_404(
    project_id: int,
    db: Session
):

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


# =========================================================
# GENERATE DESCRIPTION
# =========================================================
#
# POST /ai/generate-description/{project_id}
#
# This generates ONLY the project description.
#
# It does NOT generate:
# - PRD
# - Tasks
# - Sprint Plan
#
# =========================================================

@router.post(
    "/generate-description/{project_id}"
)
def generate_description(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = get_project_or_404(
        project_id,
        db
    )

    try:

        print(
            "================================="
        )
        print(
            "GENERATING AI DESCRIPTION"
        )
        print(
            "Project ID:",
            project_id
        )
        print(
            "================================="
        )

        # -------------------------------------------------
        # Generate description
        # -------------------------------------------------

        response = (
            description_generator.generate(
                project
            )
        )

        # -------------------------------------------------
        # Save AI description
        # -------------------------------------------------

        project.overview = (
            response.get(
                "overview",
                ""
            )
        )

        project.ai_problem_statement = (
            response.get(
                "problem_statement",
                ""
            )
        )

        project.proposed_solution = (
            response.get(
                "proposed_solution",
                ""
            )
        )

        project.target_audience = (
            response.get(
                "target_audience",
                ""
            )
        )

        project.business_value = (
            response.get(
                "business_value",
                ""
            )
        )

        project.major_features = (
            response.get(
                "major_features",
                ""
            )
        )

        project.expected_outcome = (
            response.get(
                "expected_outcome",
                ""
            )
        )

        db.commit()

        db.refresh(project)

        print(
            "AI DESCRIPTION SAVED"
        )

        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return {
            "message": "AI project description generated successfully.",

            "project_id": project.id,

            "description": {
                "overview": (
                    project.overview or ""
                ),

                "problem_statement": (
                    project.ai_problem_statement or ""
                ),

                "proposed_solution": (
                    project.proposed_solution or ""
                ),

                "target_audience": (
                    project.target_audience or ""
                ),

                "business_value": (
                    project.business_value or ""
                ),

                "major_features": (
                    project.major_features or ""
                ),

                "expected_outcome": (
                    project.expected_outcome or ""
                )
            }
        }

    except HTTPException:

        raise

    except Exception as e:

        db.rollback()

        print(
            "DESCRIPTION GENERATION ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate project description: "
                f"{str(e)}"
            )
        )


# =========================================================
# GENERATE PRD
# =========================================================
#
# POST /ai/generate-prd/{project_id}
#
# This generates ONLY the PRD.
#
# Description should preferably already exist.
#
# =========================================================

@router.post(
    "/generate-prd/{project_id}"
)
def generate_prd(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = get_project_or_404(
        project_id,
        db
    )

    try:

        print(
            "================================="
        )
        print(
            "GENERATING AI PRD"
        )
        print(
            "Project ID:",
            project_id
        )
        print(
            "================================="
        )

        # -------------------------------------------------
        # Generate PRD
        # -------------------------------------------------

        response = (
            prd_generator.generate_prd(
                project
            )
        )

        # -------------------------------------------------
        # Save PRD
        # -------------------------------------------------

        project.product_overview = (
            response.get(
                "product_overview",
                ""
            )
        )

        project.prd_problem_statement = (
            response.get(
                "problem_statement",
                ""
            )
        )

        project.goals_and_objectives = (
            response.get(
                "goals_and_objectives",
                ""
            )
        )

        project.prd_target_users = (
            response.get(
                "target_users",
                ""
            )
        )

        project.functional_requirements = (
            response.get(
                "functional_requirements",
                ""
            )
        )

        project.user_workflows = (
            response.get(
                "user_workflows",
                ""
            )
        )

        project.business_rules = (
            response.get(
                "business_rules",
                ""
            )
        )

        project.non_functional_requirements = (
            response.get(
                "non_functional_requirements",
                ""
            )
        )

        project.assumptions_and_dependencies = (
            response.get(
                "assumptions_and_dependencies",
                ""
            )
        )

        project.acceptance_criteria = (
            response.get(
                "acceptance_criteria",
                ""
            )
        )

        db.commit()

        db.refresh(project)

        print(
            "AI PRD SAVED"
        )

        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return {
            "message": "PRD generated successfully.",

            "project_id": project.id,

            "prd": {
                "product_overview": (
                    project.product_overview or ""
                ),

                "problem_statement": (
                    project.prd_problem_statement or ""
                ),

                "goals_and_objectives": (
                    project.goals_and_objectives or ""
                ),

                "target_users": (
                    project.prd_target_users or ""
                ),

                "functional_requirements": (
                    project.functional_requirements or ""
                ),

                "user_workflows": (
                    project.user_workflows or ""
                ),

                "business_rules": (
                    project.business_rules or ""
                ),

                "non_functional_requirements": (
                    project.non_functional_requirements or ""
                ),

                "assumptions_and_dependencies": (
                    project.assumptions_and_dependencies or ""
                ),

                "acceptance_criteria": (
                    project.acceptance_criteria or ""
                )
            }
        }

    except HTTPException:

        raise

    except Exception as e:

        db.rollback()

        print(
            "PRD GENERATION ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate PRD: "
                f"{str(e)}"
            )
        )


# =========================================================
# GENERATE TASKS
# =========================================================
#
# POST /ai/generate-tasks/{project_id}
#
# This generates ONLY tasks.
#
# Existing AI tasks for this project are replaced.
#
# =========================================================

@router.post(
    "/generate-tasks/{project_id}"
)
def generate_tasks(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = get_project_or_404(
        project_id,
        db
    )

    try:

        print(
            "================================="
        )
        print(
            "GENERATING AI TASKS"
        )
        print(
            "Project ID:",
            project_id
        )
        print(
            "================================="
        )

        # -------------------------------------------------
        # Generate tasks
        # -------------------------------------------------

        response = (
            task_generator.generate_tasks(
                project
            )
        )

        # -------------------------------------------------
        # Validate response
        # -------------------------------------------------

        if not isinstance(
            response,
            list
        ):

            raise RuntimeError(
                "Task generator did not return a list."
            )

        # -------------------------------------------------
        # Delete existing AI generated tasks
        #
        # We do NOT delete manual tasks.
        # -------------------------------------------------

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

        # -------------------------------------------------
        # Create new tasks
        # -------------------------------------------------

        created_tasks = []

        for index, task_data in enumerate(
            response,
            start=1
        ):

            if not isinstance(
                task_data,
                dict
            ):

                raise RuntimeError(
                    f"Invalid task at index {index}."
                )

            task = Task(

                project_id=project_id,

                task_title=(
                    task_data.get(
                        "task_title",
                        f"Task {index}"
                    )
                ),

                description=(
                    task_data.get(
                        "description",
                        ""
                    )
                ),

                task_type=(
                    task_data.get(
                        "task_type",
                        ""
                    )
                ),

                module=(
                    task_data.get(
                        "module",
                        ""
                    )
                ),

                priority=(
                    task_data.get(
                        "priority",
                        "Medium"
                    )
                ),

                acceptance_criteria=(
                    task_data.get(
                        "acceptance_criteria",
                        ""
                    )
                ),

                owner_role=(
                    task_data.get(
                        "owner_role",
                        ""
                    )
                ),

                dependencies=(
                    task_data.get(
                        "dependencies",
                        ""
                    )
                ),

                estimated_complexity=(
                    task_data.get(
                        "estimated_complexity",
                        ""
                    )
                ),

                status="Todo",

                source="ai"
            )

            db.add(task)

            created_tasks.append(task)

        db.commit()

        # -------------------------------------------------
        # Refresh tasks
        # -------------------------------------------------

        for task in created_tasks:

            db.refresh(task)

        print(
            "AI TASKS SAVED:",
            len(created_tasks)
        )

        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return {
            "message": "Tasks generated successfully.",

            "project_id": project.id,

            "tasks": [
                {
                    "id": task.id,

                    "task_title": (
                        task.task_title or ""
                    ),

                    "description": (
                        task.description or ""
                    ),

                    "task_type": (
                        task.task_type or ""
                    ),

                    "module": (
                        task.module or ""
                    ),

                    "priority": (
                        task.priority or ""
                    ),

                    "acceptance_criteria": (
                        task.acceptance_criteria or ""
                    ),

                    "owner_role": (
                        task.owner_role or ""
                    ),

                    "dependencies": (
                        task.dependencies or ""
                    ),

                    "estimated_complexity": (
                        task.estimated_complexity or ""
                    ),

                    "status": (
                        task.status or "Todo"
                    ),

                    "source": (
                        task.source or "ai"
                    )
                }

                for task in created_tasks
            ]
        }

    except HTTPException:

        raise

    except Exception as e:

        db.rollback()

        print(
            "TASK GENERATION ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate tasks: "
                f"{str(e)}"
            )
        )


# =========================================================
# GENERATE SPRINT PLAN
# =========================================================
#
# POST /ai/generate-sprint/{project_id}
#
# This generates ONLY the sprint plan.
#
# It uses the tasks already stored in the database.
#
# =========================================================

@router.post(
    "/generate-sprint/{project_id}"
)
def generate_sprint(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = get_project_or_404(
        project_id,
        db
    )

    try:

        print(
            "================================="
        )
        print(
            "GENERATING AI SPRINT PLAN"
        )
        print(
            "Project ID:",
            project_id
        )
        print(
            "================================="
        )

        # -------------------------------------------------
        # Load project tasks
        # -------------------------------------------------

        tasks = (
            db.query(Task)
            .filter(
                Task.project_id == project_id
            )
            .order_by(Task.id)
            .all()
        )

        # -------------------------------------------------
        # Sprint cannot be generated without tasks
        # -------------------------------------------------

        if not tasks:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Generate tasks before generating "
                    "the sprint plan."
                )
            )

        # -------------------------------------------------
        # Convert database tasks to generator input
        # -------------------------------------------------

        task_data = []

        for task in tasks:

            task_data.append({

                "id": task.id,

                "task_title": (
                    task.task_title or ""
                ),

                "description": (
                    task.description or ""
                ),

                "task_type": (
                    task.task_type or ""
                ),

                "module": (
                    task.module or ""
                ),

                "priority": (
                    task.priority or ""
                ),

                "acceptance_criteria": (
                    task.acceptance_criteria or ""
                ),

                "owner_role": (
                    task.owner_role or ""
                ),

                "dependencies": (
                    task.dependencies or ""
                ),

                "estimated_complexity": (
                    task.estimated_complexity or ""
                ),

                "status": (
                    task.status or "Todo"
                )
            })

        # -------------------------------------------------
        # Generate sprint plan
        # -------------------------------------------------

        response = (
            sprint_generator.generate_sprint_plan(
                project,
                task_data
            )
        )

        # -------------------------------------------------
        # Store sprint plan
        #
        # If the generator returns a dictionary/list,
        # convert it to JSON before saving.
        # -------------------------------------------------

        if isinstance(
            response,
            (dict, list)
        ):

            project.sprint_plan = json.dumps(
                response,
                ensure_ascii=False,
                indent=2
            )

        else:

            project.sprint_plan = str(
                response
            )

        db.commit()

        db.refresh(project)

        print(
            "SPRINT PLAN SAVED"
        )

        # -------------------------------------------------
        # Response
        # -------------------------------------------------

        return {
            "message": (
                "Sprint plan generated successfully."
            ),

            "project_id": project.id,

            "sprint_plan": (
                project.sprint_plan or ""
            )
        }

    except HTTPException:

        raise

    except Exception as e:

        db.rollback()

        print(
            "SPRINT GENERATION ERROR:",
            str(e)
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to generate sprint plan: "
                f"{str(e)}"
            )
        )


# =========================================================
# GET GENERATED AI CONTENT
# =========================================================
#
# GET /ai/generated/{project_id}
#
# Used by project-details.js when the page loads.
#
# =========================================================

@router.get(
    "/generated/{project_id}"
)
def get_generated_content(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = get_project_or_404(
        project_id,
        db
    )

    # -----------------------------------------------------
    # Load tasks
    # -----------------------------------------------------

    tasks = (
        db.query(Task)
        .filter(
            Task.project_id == project_id
        )
        .order_by(Task.id)
        .all()
    )

    # -----------------------------------------------------
    # Return all saved AI content
    # -----------------------------------------------------

    return {

        "project_id": project.id,

        # =================================================
        # AI DESCRIPTION
        # =================================================

        "description": {

            "overview": (
                project.overview or ""
            ),

            "problem_statement": (
                project.ai_problem_statement or ""
            ),

            "proposed_solution": (
                project.proposed_solution or ""
            ),

            "target_audience": (
                project.target_audience or ""
            ),

            "business_value": (
                project.business_value or ""
            ),

            "major_features": (
                project.major_features or ""
            ),

            "expected_outcome": (
                project.expected_outcome or ""
            )
        },

        # =================================================
        # AI PRD
        # =================================================

        "prd": {

            "product_overview": (
                project.product_overview or ""
            ),

            "problem_statement": (
                project.prd_problem_statement or ""
            ),

            "goals_and_objectives": (
                project.goals_and_objectives or ""
            ),

            "target_users": (
                project.prd_target_users or ""
            ),

            "functional_requirements": (
                project.functional_requirements or ""
            ),

            "user_workflows": (
                project.user_workflows or ""
            ),

            "business_rules": (
                project.business_rules or ""
            ),

            "non_functional_requirements": (
                project.non_functional_requirements or ""
            ),

            "assumptions_and_dependencies": (
                project.assumptions_and_dependencies or ""
            ),

            "acceptance_criteria": (
                project.acceptance_criteria or ""
            )
        },

        # =================================================
        # TASKS
        # =================================================

        "tasks": [

            {
                "id": task.id,

                "task_title": (
                    task.task_title or ""
                ),

                "description": (
                    task.description or ""
                ),

                "task_type": (
                    task.task_type or ""
                ),

                "module": (
                    task.module or ""
                ),

                "priority": (
                    task.priority or ""
                ),

                "acceptance_criteria": (
                    task.acceptance_criteria or ""
                ),

                "owner_role": (
                    task.owner_role or ""
                ),

                "dependencies": (
                    task.dependencies or ""
                ),

                "estimated_complexity": (
                    task.estimated_complexity or ""
                ),

                "status": (
                    task.status or "Todo"
                ),

                "source": (
                    task.source or "manual"
                )
            }

            for task in tasks
        ],

        # =================================================
        # SPRINT PLAN
        # =================================================

        "sprint_plan": (
            project.sprint_plan or ""
        )
    }
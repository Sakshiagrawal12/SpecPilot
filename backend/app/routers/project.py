import re
from urllib.parse import quote

from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)
from pydantic import BaseModel
from typing import Optional

from fastapi.responses import StreamingResponse

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Project,
    User,
    Conversation,
    ProjectRequirement,
    Task
)

from app.schemas import ProjectCreate

from app.auth import get_current_user

from app.services.prd_export import (
    generate_prd_pdf,
    generate_prd_docx
)


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

# =========================================================
# EDIT PROJECT FIELD
# =========================================================

class ProjectFieldUpdate(BaseModel):
    field: str
    value: str


# =========================================================
# EDIT TASK
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
# =========================================================
# SAFE FILENAME
# =========================================================

def safe_filename(name: str) -> str:

    name = name or "project"

    # Replace common fancy punctuation
    name = (
        name
        .replace("—", "-")
        .replace("–", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    # Strip non-ASCII characters
    name = name.encode(
        "ascii",
        "ignore"
    ).decode("ascii")

    # Collapse whitespace
    name = re.sub(
        r"\s+",
        " ",
        name
    ).strip()

    return name or "project"


# =========================================================
# CREATE PROJECT
# =========================================================

@router.post("/")
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    project_name = project_data.project_name.strip()

    if not project_name:

        raise HTTPException(
            status_code=400,
            detail="Project name cannot be empty."
        )

    # -----------------------------------------------------
    # CREATE PROJECT
    # -----------------------------------------------------

    project = Project(
        user_id=current_user.id,
        project_name=project_name
    )

    db.add(project)

    db.flush()

    # -----------------------------------------------------
    # CREATE EMPTY REQUIREMENTS RECORD
    # -----------------------------------------------------

    requirement_record = ProjectRequirement(

        project_id=project.id,

        requirements={

            "category": {
                "value": None,
                "confidence": 0.0,
                "status": "missing"
            },

            "business_objective": {
                "value": None,
                "confidence": 0.0,
                "status": "missing"
            },

            "target_users": {
                "value": None,
                "confidence": 0.0,
                "status": "missing"
            },

            "problem_statement": {
                "value": None,
                "confidence": 0.0,
                "status": "missing"
            },

            "expected_features": {
                "value": None,
                "confidence": 0.0,
                "status": "missing"
            },

            "technology_preferences": {
                "value": None,
                "confidence": 0.0,
                "status": "missing"
            },

            "timeline": {
                "value": None,
                "confidence": 0.0,
                "status": "missing"
            },

            "additional_instructions": {
                "value": None,
                "confidence": 0.0,
                "status": "missing"
            }
        },

        completeness_status="INCOMPLETE",

        completeness_score=0
    )

    db.add(requirement_record)

    # -----------------------------------------------------
    # CREATE CONVERSATION
    # -----------------------------------------------------

    conversation = Conversation(
        project_id=project.id,
        status="active"
    )

    db.add(conversation)

    db.commit()

    db.refresh(conversation)

    return {

        "message": "Project created successfully",

        "project_id": project.id,

        "conversation_id": conversation.id,

        "project_name": project.project_name

    }


# =========================================================
# GET MY PROJECTS
# =========================================================

@router.get("/")
def get_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    projects = (

        db.query(Project)

        .filter(
            Project.user_id == current_user.id
        )

        .all()
    )

    return projects


# =========================================================
# GET SINGLE PROJECT
# =========================================================

@router.get("/{project_id}")
def get_project(
    project_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    project = (

        db.query(Project)

        .filter(

            Project.id == project_id,

            Project.user_id == current_user.id

        )

        .first()
    )

    if project is None:

        raise HTTPException(

            status_code=404,

            detail="Project not found"
        )

    return project


# =========================================================
# DELETE PROJECT
# =========================================================

@router.delete("/{project_id}")
def delete_project(
    project_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # IMPORTANT:
    # Only allow the logged-in user to delete THEIR project.
    # -----------------------------------------------------

    project = (

        db.query(Project)

        .filter(

            Project.id == project_id,

            Project.user_id == current_user.id

        )

        .first()
    )

    if project is None:

        raise HTTPException(

            status_code=404,

            detail="Project not found"
        )

    project_name = project.project_name

    # -----------------------------------------------------
    # DELETE PROJECT
    #
    # SQLAlchemy relationships in models.py already contain:
    #
    # cascade="all, delete-orphan"
    #
    # Therefore this will also delete:
    #
    # ProjectRequirement
    # Tasks
    # Conversations
    # Messages
    # -----------------------------------------------------

    try:
        db.delete(project)
        db.commit()

        return {
            "message": "Project deleted successfully",
            "project_id": project_id,
            "project_name": project_name
        }

    except Exception as e:
        db.rollback()

        print("DELETE PROJECT ERROR:", str(e))

        raise HTTPException(
            status_code=500,
            detail="Failed to delete project"
        )


# =========================================================
# DOWNLOAD PRD
# =========================================================

@router.get("/{project_id}/download-prd")
def download_prd(
    project_id: int,

    format: str = "pdf",

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # FIND PROJECT
    # -----------------------------------------------------

    project = (

        db.query(Project)

        .filter(

            Project.id == project_id,

            Project.user_id == current_user.id

        )

        .first()
    )

    if project is None:

        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # -----------------------------------------------------
    # CHECK PRD
    # -----------------------------------------------------

    if not project.product_overview:

        raise HTTPException(
            status_code=400,
            detail="PRD has not been generated yet."
        )

    # -----------------------------------------------------
    # NORMALIZE FORMAT
    # -----------------------------------------------------

    format = format.lower().strip()

    # -----------------------------------------------------
    # DOCX
    # -----------------------------------------------------

    if format == "docx":

        buffer = generate_prd_docx(project)

        media_type = (
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        )

        raw_filename = (
            f"{project.project_name}-PRD.docx"
        )

    # -----------------------------------------------------
    # PDF
    # -----------------------------------------------------

    elif format == "pdf":

        buffer = generate_prd_pdf(project)

        media_type = "application/pdf"

        raw_filename = (
            f"{project.project_name}-PRD.pdf"
        )

    # -----------------------------------------------------
    # INVALID FORMAT
    # -----------------------------------------------------

    else:

        raise HTTPException(
            status_code=400,
            detail="Unsupported format. Use 'pdf' or 'docx'."
        )

    # -----------------------------------------------------
    # SAFE FILENAME
    # -----------------------------------------------------

    ascii_filename = safe_filename(
        raw_filename
    )

    return StreamingResponse(

        buffer,

        media_type=media_type,

        headers={
            "Content-Disposition": (
                f'attachment; filename="{ascii_filename}"; '
                f"filename*=UTF-8''{quote(raw_filename)}"
            )
        }
    )

# =========================================================
# UPDATE PROJECT FIELD
# =========================================================

@router.put("/{project_id}/field")
def update_project_field(
    project_id: int,
    data: ProjectFieldUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    # Only these fields can be edited from Project Details.
    allowed_fields = {
    "project_name",  # Allow renaming a project

    # Keep all your existing fields below
    "overview",
    "ai_problem_statement",
    "proposed_solution",
    "target_audience",
    "business_value",
    "major_features",
    "expected_outcome",

    "product_overview",
    "prd_problem_statement",
    "goals_and_objectives",
    "prd_target_users",
    "functional_requirements",
    "user_workflows",
    "business_rules",
    "non_functional_requirements",
    "assumptions_and_dependencies",
    "acceptance_criteria",
    "sprint_plan"
    }
    if data.field == "project_name":
        data.value = data.value.strip()

        if not data.value:
            raise HTTPException(
                status_code=400,
                detail="Project name cannot be empty."
            )

        if len(data.value) > 255:
            raise HTTPException(
                status_code=400,
                detail="Project name cannot exceed 255 characters."
            )

    setattr(
        project,
        data.field,
        data.value
    )

    db.commit()
    db.refresh(project)

    return {
        "message": "Project field updated successfully",
        "project_id": project_id,
        "field": data.field,
        "value": getattr(project, data.field)
    }

# =========================================================
# UPDATE TASK
# =========================================================

@router.put("/{project_id}/tasks/{task_id}")
def update_task(
    project_id: int,
    task_id: int,
    data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = (
        db.query(Project)
        .filter(
            Project.id == project_id,
            Project.user_id == current_user.id
        )
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.project_id == project_id
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    update_data = data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return {
        "message": "Task updated successfully",
        "task": {
            "id": task.id,
            "project_id": task.project_id,
            "task_title": task.task_title,
            "description": task.description,
            "task_type": task.task_type,
            "module": task.module,
            "priority": task.priority,
            "acceptance_criteria": task.acceptance_criteria,
            "owner_role": task.owner_role,
            "dependencies": task.dependencies,
            "estimated_complexity": task.estimated_complexity,
            "status": task.status,
            "source": task.source
        }
    }
from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from fastapi.responses import StreamingResponse

from app.services.prd_export import (
    generate_prd_pdf,
    generate_prd_docx
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Project,
    User,
    Conversation,
    ProjectRequirement
)

from app.schemas import ProjectCreate

from app.auth import get_current_user


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)

import re
from urllib.parse import quote

def safe_filename(name: str) -> str:

    name = name or "project"

    # Replace common "fancy" punctuation with ASCII equivalents
    name = (
        name
        .replace("—", "-")
        .replace("–", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    # Strip anything else that isn't ASCII
    name = name.encode("ascii", "ignore").decode("ascii")

    # Collapse whitespace, keep it filesystem-friendly
    name = re.sub(r"\s+", " ", name).strip()

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

        project_name=project_name,

         )

    db.add(project)

    db.flush()

    # -----------------------------------------------------
    # CREATE EMPTY REQUIREMENTS RECORD
    #
    # Agent will update this during conversation.
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

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

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
# DOWNLOAD PRD
# =========================================================

@router.get("/{project_id}/download-prd")
def download_prd(
    project_id: int,

    format: str = "pdf",

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

    if not project.product_overview:

        raise HTTPException(
            status_code=400,
            detail="PRD has not been generated yet."
        )

        if format == "docx":

            buffer = generate_prd_docx(project)

            media_type = (
            "application/vnd.openxmlformats-officedocument"
            ".wordprocessingml.document"
        )

            raw_filename = f"{project.project_name}-PRD.docx"

    else:

        buffer = generate_prd_pdf(project)

        media_type = "application/pdf"

        raw_filename = f"{project.project_name}-PRD.pdf"

    ascii_filename = safe_filename(raw_filename)

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
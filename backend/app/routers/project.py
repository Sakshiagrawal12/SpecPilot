from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Project,
    User
)

from app.schemas import ProjectCreate

from app.auth import get_current_user


router = APIRouter(
    prefix="/projects",
    tags=["Projects"]
)


# =========================================================
# CREATE PROJECT
# =========================================================

@router.post("/")
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    project = Project(
        user_id=current_user.id,

        project_name=project_data.project_name,
        category=project_data.category,
        business_objective=project_data.business_objective,
        target_users=project_data.target_users,
        problem_statement=project_data.problem_statement,
        expected_features=project_data.expected_features,
        technology_preferences=project_data.technology_preferences,
        timeline=project_data.timeline,
        additional_instructions=project_data.additional_instructions
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return {
        "message": "Project created successfully",
        "project_id": project.id
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
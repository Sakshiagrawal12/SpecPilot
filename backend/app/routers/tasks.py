
from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.models import (
    Project,
    Task
)

from app.schemas import (
    TaskCreate,
    TaskUpdate,
    TaskResponse
)


router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)


# =========================================================
# CREATE TASK
# =========================================================

@router.post(
    "/project/{project_id}",
    response_model=TaskResponse
)
def create_task(
    project_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db)
):

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:

        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    task = Task(
        project_id=project_id,

        task_title=task_data.task_title,

        description=task_data.description,

        task_type=task_data.task_type,

        module=task_data.module,

        priority=task_data.priority,

        acceptance_criteria=
            task_data.acceptance_criteria,

        owner_role=
            task_data.owner_role,

        dependencies=
            task_data.dependencies,

        estimated_complexity=
            task_data.estimated_complexity,

        status=task_data.status,

        source=task_data.source
    )

    db.add(task)

    db.commit()

    db.refresh(task)

    return task


# =========================================================
# GET PROJECT TASKS
# =========================================================

@router.get(
    "/project/{project_id}",
    response_model=list[TaskResponse]
)
def get_project_tasks(
    project_id: int,
    db: Session = Depends(get_db)
):

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:

        raise HTTPException(
            status_code=404,
            detail="Project not found"
        )

    tasks = (
        db.query(Task)
        .filter(Task.project_id == project_id)
        .order_by(Task.id.desc())
        .all()
    )

    return tasks


# =========================================================
# GET SINGLE TASK
# =========================================================

@router.get(
    "/{task_id}",
    response_model=TaskResponse
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db)
):

    task = (
        db.query(Task)
        .filter(Task.id == task_id)
        .first()
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    return task


# =========================================================
# UPDATE TASK
# =========================================================

@router.put(
    "/{task_id}",
    response_model=TaskResponse
)
def update_task(
    task_id: int,
    task_data: TaskUpdate,
    db: Session = Depends(get_db)
):

    task = (
        db.query(Task)
        .filter(Task.id == task_id)
        .first()
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    update_data = task_data.model_dump(
        exclude_unset=True
    )

    for field, value in update_data.items():

        setattr(
            task,
            field,
            value
        )

    db.commit()

    db.refresh(task)

    return task


# =========================================================
# DELETE TASK
# =========================================================

@router.delete(
    "/{task_id}"
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):

    task = (
        db.query(Task)
        .filter(Task.id == task_id)
        .first()
    )

    if task is None:

        raise HTTPException(
            status_code=404,
            detail="Task not found"
        )

    db.delete(task)

    db.commit()

    return {
        "message": "Task deleted successfully"
    }

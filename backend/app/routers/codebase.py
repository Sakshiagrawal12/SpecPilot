import os
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from typing import Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Project, User
from app.services.code_extraction import (
    MAX_UPLOAD_BYTES,
    ExtractionError,
    extract_zip,
)
from app.services.code_facts import extract_facts
from app.services.github_fetch import (
    GithubError,
    download_repo_zip,
    parse_github_url,
    validate_token,
)


router = APIRouter(
    prefix="/codebase",
    tags=["Codebase"]
)


class GithubRequest(BaseModel):
    url: str
    token: Optional[str] = None     # personal access token, only for private repositories


# =========================================================
# HELPERS
# =========================================================

def _get_own_project(db: Session, project_id: int, user: User) -> Project:
    project = (
        db.query(Project)
        .filter(Project.id == project_id, Project.user_id == user.id)
        .first()
    )
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _inventory(zip_path: str, tmp: str) -> dict:
    """Safe extraction, then static facts. Must run before the temp folder is deleted."""
    src_dir = os.path.join(tmp, "src")
    try:
        inventory = extract_zip(zip_path, src_dir)
    except ExtractionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    inventory["facts"] = extract_facts(src_dir, inventory)
    return inventory


# =========================================================
# UPLOAD ZIP  ->  SAFE EXTRACTION  ->  FILE INVENTORY
# (nothing is stored yet; the source is deleted as soon as
#  the inventory has been built)
# =========================================================

@router.post("/upload/{project_id}")
def upload_codebase(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_own_project(db, project_id, user)

    if not (file.filename or "").lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Please upload a .zip file.")

    with tempfile.TemporaryDirectory(prefix="specpilot_code_") as tmp:
        zip_path = os.path.join(tmp, "upload.zip")

        size = 0
        with open(zip_path, "wb") as out:
            while True:
                chunk = file.file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"ZIP is too large (limit {MAX_UPLOAD_BYTES // (1024 * 1024)} MB).",
                    )
                out.write(chunk)

        inventory = _inventory(zip_path, tmp)

    return {
        "project_id": project_id,
        "source": {"type": "zip", "filename": file.filename},
        "zip_bytes": size,
        **inventory,
    }


# =========================================================
# PUBLIC GITHUB LINK  ->  DOWNLOAD  ->  SAME INVENTORY
# =========================================================

@router.post("/github/{project_id}")
def analyze_github(
    project_id: int,
    body: GithubRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    _get_own_project(db, project_id, user)

    try:
        owner, repo, ref = parse_github_url(body.url)
        token = validate_token(body.token)
    except GithubError as e:
        raise HTTPException(status_code=e.status, detail=str(e))

    with tempfile.TemporaryDirectory(prefix="specpilot_code_") as tmp:
        zip_path = os.path.join(tmp, "repo.zip")

        try:
            size = download_repo_zip(
                owner, repo, ref, zip_path, MAX_UPLOAD_BYTES, token=token
            )
        except GithubError as e:
            raise HTTPException(status_code=e.status, detail=str(e))

        inventory = _inventory(zip_path, tmp)

    return {
        "project_id": project_id,
        "source": {
            "type": "github", "owner": owner, "repo": repo,
            "ref": ref or "default branch", "private": bool(token),
        },
        "zip_bytes": size,
        **inventory,
    }
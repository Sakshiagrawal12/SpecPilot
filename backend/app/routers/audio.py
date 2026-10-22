import os

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import get_current_user
from app.models import User, Transcript
from app.routers.agent import (
    get_project_or_404,
    get_or_create_conversation,
    apply_text_to_requirements,
)
from app.agents.audio_manager.runner import process_audio

router = APIRouter(prefix="/audio", tags=["Audio"])

ALLOWED_EXT = {".mp3", ".wav", ".m4a", ".webm"}
MAX_BYTES = 25 * 1024 * 1024  # confirm against Groq's current limit


class TranscriptUpdate(BaseModel):
    edited_text: str
    approve: bool = False


class SubmitRequest(BaseModel):
    thread_id: str


def _get_transcript(db, project_id, tid, user):
    t = (
        db.query(Transcript)
        .filter(
            Transcript.id == tid,
            Transcript.project_id == project_id,
            Transcript.user_id == user.id,
        )
        .first()
    )
    if t is None:
        raise HTTPException(404, "Transcript not found")
    return t


def _out(t):
    return {
        "id": t.id,
        "status": t.status,
        "raw_text": t.raw_text,
        "edited_text": t.edited_text,
        "error_message": t.error_message,
    }


# Plain `def` (not async): the Whisper call blocks, and FastAPI runs
# plain functions in a threadpool so other requests keep working.
@router.post("/transcribe/{project_id}")
def transcribe(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db, current_user)

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "Unsupported audio type")

    audio = file.file.read()
    if not audio:
        raise HTTPException(400, "Empty file")
    if len(audio) > MAX_BYTES:
        raise HTTPException(413, "File too large")

    t = Transcript(
        project_id=project.id,
        user_id=current_user.id,
        audio_filename=file.filename,
        status="transcribing",
    )
    db.add(t)
    db.commit()
    db.refresh(t)

    try:
        result = process_audio(project.id, audio, file.filename)
    except Exception as e:
        t.status = "failed"
        t.error_message = f"Processing failed: {e}"
        db.commit()
        return _out(t)

    if result.get("error"):
        t.status = "failed"
        t.error_message = result["error"]
    else:
        t.raw_text = result["raw_text"]
        t.edited_text = result["clean_text"]
        t.status = "needs_review"

    db.commit()
    return _out(t)


@router.get("/transcripts/{project_id}/{tid}")
def get_transcript(
    project_id: int,
    tid: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_or_404(project_id, db, current_user)
    return _out(_get_transcript(db, project_id, tid, current_user))


@router.put("/transcripts/{project_id}/{tid}")
def save_transcript(
    project_id: int,
    tid: int,
    body: TranscriptUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_project_or_404(project_id, db, current_user)
    t = _get_transcript(db, project_id, tid, current_user)

    if t.status in ("transcribing", "failed", "submitted"):
        raise HTTPException(409, f"Cannot edit a transcript that is {t.status}")

    if body.approve and not body.edited_text.strip():
        raise HTTPException(400, "Transcript is empty")

    t.edited_text = body.edited_text
    t.status = "approved" if body.approve else "needs_review"
    db.commit()
    return _out(t)


@router.post("/transcripts/{project_id}/{tid}/submit")
def submit_transcript(
    project_id: int,
    tid: int,
    body: SubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = get_project_or_404(project_id, db, current_user)
    t = _get_transcript(db, project_id, tid, current_user)

    if t.status != "approved":
        raise HTTPException(409, "Transcript must be approved first")

    if project.product_overview and project.product_overview.strip():
        raise HTTPException(
            409,
            "A PRD has already been generated for this project. "
            "Adding new requirements would make it out of date.",
        )

    conversation = get_or_create_conversation(project.id, db)

    result = apply_text_to_requirements(
        project=project,
        conversation=conversation,
        document_text=t.edited_text,
        user_note=f"[Voice requirements]\n{t.edited_text}",
        thread_id=body.thread_id,
        db=db,
    )

    t.status = "submitted"
    db.commit()
    return result
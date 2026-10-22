
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.database import engine
from app.routers import codebase
from app.models import Base
from app.routers import audio
from app.routers import project
from app.routers import ai
from app.routers import tasks
from app.routers import auth
from app.routers.agent import router as agent_router
from app.routers.project import router as projects_router
from app.routers.generation import router as generation_router
from pathlib import Path
from fastapi.responses import FileResponse


# =========================================================
# DATABASE & DIRECTORIES
# =========================================================

Base.metadata.create_all(
    bind=engine
)
origins = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
]


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="SpecPilot API",
    description="AI-Powered Project Management Assistant",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# STATIC FILES (UPLOADS)
# =========================================================


# =========================================================
# ROUTERS
# =========================================================

app.include_router(
    project.router
)

app.include_router(
    ai.router
)

app.include_router(
    tasks.router
)

app.include_router(
    generation_router
)

app.include_router(
    auth.router
)

app.include_router(agent_router)

app.include_router(projects_router)

app.include_router(audio.router)
app.include_router(codebase.router)

# =========================================================
# HOME
# =========================================================

@app.get("/")
def home():
    return {
        "message": "SpecPilot Backend Running"
    }



@app.get("/audio-test", include_in_schema=False)
def audio_test_page():
    return FileResponse(Path(__file__).parent / "audio_test.html")

@app.get("/codebase-test", include_in_schema=False)
def codebase_test_page():
    return FileResponse(Path(__file__).parent / "codebase_test.html")
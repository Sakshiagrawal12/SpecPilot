"""
Entry point for running the full generation pipeline for a project.
Takes the same (project, requirements) shape app/routers/ai.py's
individual endpoints already use — this just runs all of them in
sequence with shared error handling instead of four separate try/except
blocks across four separate endpoints.
"""

from typing import Any, Dict
from app.agents.generation_manager.graph import generation_manager

def run_generation(project: Any, requirements: Dict[str, Any]) -> Dict[str, Any]:
    
    # Initialize state with empty/default defaults for all pipeline stages
    initial_state = {
        "project": project,
        "requirements": requirements,
        "stage": "description",
        "status": "in_progress",
        "description": {},
        "prd": {},
        "tasks": [],
        "dependency_plan": {},  # Ensures dependency_plan key exists from start
        "sprint_plan": {},
        "error": None
    }

    try:
        result = generation_manager.invoke(initial_state)
        return result
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }
        
def to_text(value) -> str:
    """Text columns can't store lists/dicts. Keep strings as-is, JSON-encode the rest."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False)

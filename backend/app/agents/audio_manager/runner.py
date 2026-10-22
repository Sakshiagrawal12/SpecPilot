from typing import Dict, Any

from app.agents.audio_manager.graph import audio_graph


def process_audio(
    project_id: int,
    audio_bytes: bytes,
    filename: str,
) -> Dict[str, Any]:
    """Audio -> raw_text + clean_text (or error)."""

    return audio_graph.invoke({
        "project_id": project_id,
        "audio_bytes": audio_bytes,
        "filename": filename,
    })
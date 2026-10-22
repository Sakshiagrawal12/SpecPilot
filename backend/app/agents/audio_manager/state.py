from typing import TypedDict, Optional

class AudioState(TypedDict, total=False):
    project_id: int
    audio_bytes: bytes
    filename: str
    raw_text: str
    clean_text: str
    error: Optional[str]
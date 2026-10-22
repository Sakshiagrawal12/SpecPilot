import os
from functools import lru_cache

from groq import Groq


@lru_cache(maxsize=1)
def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")
    return Groq(api_key=api_key)


def transcribe_audio(audio_bytes: bytes, filename: str) -> str:
    result = _get_client().audio.transcriptions.create(
        file=(filename, audio_bytes),
        model="whisper-large-v3-turbo",  # confirm in Groq docs
        response_format="text",
        temperature=0,
        prompt="FastAPI, PRD, SpecPilot, LangGraph, SQLite, API, sprint",
    )
    return result if isinstance(result, str) else result.text
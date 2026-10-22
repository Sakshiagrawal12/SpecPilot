from app.agents.audio_manager.state import AudioState
from app.services.transcription import transcribe_audio


def transcribe_node(state: AudioState) -> AudioState:
    try:
        text = transcribe_audio(state["audio_bytes"], state["filename"])

        if not text or not text.strip():
            return {"error": "No speech detected in the recording."}

        return {"raw_text": text.strip()}

    except Exception as e:
        return {"error": f"Transcription failed: {e}"}
from langchain_groq import ChatGroq

from app.agents.audio_manager.state import AudioState

# Use the same model/config you use in your other agents.
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

CLEANUP_PROMPT = """You clean up a speech transcript of someone describing a software project.

Rules:
- Fix punctuation, remove filler words (um, uh, like), and fix obvious mis-hearings of technical terms.
- Do NOT add, remove, merge or infer any requirement or feature.
- Keep the speaker's meaning and order.
- Output only the cleaned text, nothing else.

Transcript:
{text}"""


def cleanup_node(state: AudioState) -> AudioState:
    if state.get("error"):
        return {}

    try:
        reply = llm.invoke(CLEANUP_PROMPT.format(text=state["raw_text"]))
        cleaned = (reply.content or "").strip()
        return {"clean_text": cleaned or state["raw_text"]}

    except Exception as e:
        print("CLEANUP ERROR:", e)
        return {"clean_text": state["raw_text"]}
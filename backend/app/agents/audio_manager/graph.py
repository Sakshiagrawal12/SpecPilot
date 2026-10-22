from langgraph.graph import StateGraph, END

from app.agents.audio_manager.state import AudioState
from app.agents.audio_manager.nodes.transcribe_node import transcribe_node
from app.agents.audio_manager.nodes.cleanup_node import cleanup_node

builder = StateGraph(AudioState)

builder.add_node("transcribe", transcribe_node)
builder.add_node("cleanup", cleanup_node)

builder.set_entry_point("transcribe")
builder.add_edge("transcribe", "cleanup")
builder.add_edge("cleanup", END)

audio_graph = builder.compile()
from fastapi import APIRouter
from pydantic import BaseModel

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from agent.agent_graph import app


router = APIRouter(
    prefix="/agent",
    tags=["Agent"]
)


# ==========================================
# Request Models
# ==========================================

class AgentChatRequest(BaseModel):

    project_id: int
    message: str
    thread_id: str


class AgentApprovalRequest(BaseModel):

    thread_id: str
    approval: str


# ==========================================
# CHAT
# ==========================================

@router.post("/chat")
def chat_with_agent(
    request: AgentChatRequest
):

    config = {
        "configurable": {
            "thread_id": request.thread_id
        }
    }

    result = app.invoke(
        {
            "messages": [
                HumanMessage(
                    content=request.message
                )
            ],
            "project_id": request.project_id,
            "retry_count": 0,
            "human_approved": False
        },
        config
    )

    # Agent paused for approval
    if "__interrupt__" in result:

        interrupt_data = (
            result["__interrupt__"][0].value
        )

        return {
            "status": "approval_required",
            "message": interrupt_data["message"],
            "tool": interrupt_data["tool"],
            "arguments": interrupt_data["arguments"],
            "thread_id": request.thread_id
        }

    # Normal response
    return {
        "status": "completed",
        "response": result["messages"][-1].content,
        "thread_id": request.thread_id
    }


# ==========================================
# APPROVAL
# ==========================================

@router.post("/approve")
def approve_agent_action(
    request: AgentApprovalRequest
):

    config = {
        "configurable": {
            "thread_id": request.thread_id
        }
    }

    result = app.invoke(
        Command(
            resume=request.approval
        ),
        config
    )

    # Another interrupt occurred
    if "__interrupt__" in result:

        interrupt_data = (
            result["__interrupt__"][0].value
        )

        return {
            "status": "approval_required",
            "message": interrupt_data["message"],
            "tool": interrupt_data["tool"],
            "arguments": interrupt_data["arguments"],
            "thread_id": request.thread_id
        }

    return {
        "status": "completed",
        "response": result["messages"][-1].content,
        "thread_id": request.thread_id
    }
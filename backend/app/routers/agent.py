from fastapi import (
    APIRouter,
    Depends,
    HTTPException
)

from pydantic import BaseModel

from sqlalchemy.orm import Session

from langchain_core.messages import HumanMessage
from langgraph.types import Command

from app.database import get_db

from app.models import (
    Project,
    Conversation,
    Message,
    ProjectRequirement,
    User
)
import copy 
from app.auth import get_current_user

from app.agent.graph import agent

from app.schemas import AgentChatRequest

router = APIRouter(
    prefix="/agent",
    tags=["Agent"]
)


# =========================================================
# REQUEST MODELS
# =========================================================



class AgentStartRequest(BaseModel):

    project_id: int

    thread_id: str


class AgentApprovalRequest(BaseModel):

    thread_id: str

    approval: str


# =========================================================
# EMPTY REQUIREMENTS
# =========================================================

def create_empty_requirements():

    return {
        "project_name": {
            "value": None,
            "confidence": 0.0,
            "status": "MISSING"
        },

        "business_objective": {
            "value": None,
            "confidence": 0.0,
            "status": "missing"
        },

        "target_users": {
            "value": None,
            "confidence": 0.0,
            "status": "missing"
        },

        "problem_statement": {
            "value": None,
            "confidence": 0.0,
            "status": "missing"
        },

        "expected_features": {
            "value": None,
            "confidence": 0.0,
            "status": "missing"
        },

        "technology_preferences": {
            "value": None,
            "confidence": 0.0,
            "status": "missing"
        },

        "timeline": {
            "value": None,
            "confidence": 0.0,
            "status": "missing"
        },

        "additional_instructions": {
            "value": None,
            "confidence": 0.0,
            "status": "missing"
        }
    }


# =========================================================
# GET PROJECT
# =========================================================

def get_project_or_404(
    project_id: int,
    db: Session,
    current_user: User
):

    project = (

        db.query(Project)

        .filter(

            Project.id == project_id,

            Project.user_id == current_user.id

        )

        .first()
    )

    if project is None:

        raise HTTPException(

            status_code=404,

            detail="Project not found"
        )

    return project


# =========================================================
# GET OR CREATE REQUIREMENTS
# =========================================================
def get_or_create_requirements(
    project_id: int,
    db: Session
):

    requirement_record = (

        db.query(ProjectRequirement)

        .filter(
            ProjectRequirement.project_id == project_id
        )

        .first()
    )

    if requirement_record is None:

        requirement_record = ProjectRequirement(

            project_id=project_id,

            requirements=create_empty_requirements(),

            completeness_status="INCOMPLETE",

            completeness_score=0
        )

        db.add(requirement_record)

        db.commit()

        db.refresh(requirement_record)

    requirements = requirement_record.requirements

    if not requirements:

        requirements = create_empty_requirements()

    # IMPORTANT:
    # Never give the SQLAlchemy JSON object directly
    # to LangGraph.
    requirements = copy.deepcopy(requirements)

    return requirement_record, requirements


# =========================================================
# GET OR CREATE CONVERSATION
# =========================================================

def get_or_create_conversation(
    project_id: int,
    db: Session
):

    conversation = (

        db.query(Conversation)

        .filter(

            Conversation.project_id == project_id,

            Conversation.status == "active"

        )

        .order_by(
            Conversation.created_at.desc()
        )

        .first()
    )

    if conversation:

        return conversation

    conversation = Conversation(

        project_id=project_id,

        status="active"
    )

    db.add(conversation)

    db.commit()

    db.refresh(conversation)

    return conversation

@router.get("/history/{project_id}")
def get_agent_history(
    project_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # VERIFY PROJECT
    # -----------------------------------------------------

    project = get_project_or_404(
        project_id,
        db,
        current_user
    )

    # -----------------------------------------------------
    # GET ACTIVE CONVERSATION
    # -----------------------------------------------------

    conversation = (
    db.query(Conversation)
    .filter(
        Conversation.project_id == project.id
    )
    .order_by(
        Conversation.created_at.desc()
    )
    .first()
    )

    # -----------------------------------------------------
    # NO CONVERSATION YET
    # -----------------------------------------------------

    if conversation is None:

        return {
            "status": "empty",
            "conversation_id": None,
            "messages": []
        }

    # -----------------------------------------------------
    # GET MESSAGES
    # -----------------------------------------------------

    messages = (
        db.query(Message)
        .filter(
            Message.conversation_id == conversation.id
        )
        .order_by(
            Message.created_at.asc()
        )
        .all()
    )

    # -----------------------------------------------------
    # FORMAT
    # -----------------------------------------------------

    history = []

    for message in messages:

        history.append({

            "role":
                message.role,

            "content":
                message.content,

            "created_at":
                message.created_at.isoformat()
                if message.created_at
                else None
        })

    # -----------------------------------------------------
    # REQUIREMENTS
    # -----------------------------------------------------

    requirement_record, requirements = (
        get_or_create_requirements(
            project.id,
            db
        )
    )

    current_field = find_next_missing_field(
        requirements
    )

    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "status":
            "success",

        "conversation_id":
            conversation.id,

        "project_id":
            project.id,

        "project_name":
            project.project_name,

        "messages":
            history,

        "requirements":
            requirements,

        "current_field":
            current_field
    }
# =========================================================
# START AGENT INTERVIEW
# =========================================================

@router.post("/start")
def start_agent(
    request: AgentStartRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    # =====================================================
    # VERIFY PROJECT
    # =====================================================

    project = get_project_or_404(
        request.project_id,
        db,
        current_user
    )

    # =====================================================
    # REQUIREMENTS
    # =====================================================

    requirement_record, requirements = (
        get_or_create_requirements(
            project.id,
            db
        )
    )

    # =====================================================
    # MAKE SURE PROJECT NAME IS STORED
    # =====================================================

    if "project_name" not in requirements:

        requirements["project_name"] = {
            "value": None,
            "confidence": 0.0,
            "status": "MISSING"
        }

    requirements["project_name"]["value"] = (
        project.project_name
    )

    requirements["project_name"]["confidence"] = 1.0

    requirements["project_name"]["status"] = "PROVIDED"

    # =====================================================
    # CONVERSATION
    # =====================================================

    conversation = get_or_create_conversation(
        project.id,
        db
    )

    # =====================================================
    # LANGGRAPH CONFIG
    # =====================================================

    config = {

        "configurable": {

            "thread_id":
                request.thread_id

        }

    }

    # =====================================================
    # START GRAPH
    # =====================================================
    #
    # IMPORTANT:
    #
    # user_message is empty because this is NOT a user
    # answer.
    #
    # The project name has already been supplied directly
    # from the database.
    #
    # =====================================================

    try:

        result = agent.invoke(

            {

                "messages": [],

                "project_id":
                    project.id,

                "project_name":
                    project.project_name,

                "user_message":
                    "",

                "retry_count":
                    0,

                "human_approved":
                    False,

                "requirements":
                    requirements

            },

            config
        )

    except Exception as e:

        print(
            "AGENT START ERROR:",
            str(e)
        )

        raise HTTPException(

            status_code=500,

            detail=f"Agent start failed: {str(e)}"
        )
    print("\n========================================")
    print("START REQUIREMENTS BEFORE GRAPH")
    print(requirements)
    print("========================================")
        # =====================================================
    # INTERRUPT
    # =====================================================

    if "__interrupt__" in result:

        interrupt_data = (
            result["__interrupt__"][0].value
        )

        agent_response = interrupt_data.get(

            "message",

            "Let's start gathering your requirements."
        )

    else:

        # =================================================
        # AGENT RESPONSE
        # =================================================

        agent_response = result.get(
            "agent_response"
        )

        if not agent_response:

            messages = result.get(
                "messages",
                []
            )

            if messages:

                agent_response = (
                    messages[-1].content
                )

            else:

                agent_response = (
                    "What is the main goal or objective of this project?"
                )

    # =====================================================
    # UPDATED REQUIREMENTS
    # =====================================================

    updated_requirements = result.get(

        "requirements",

        requirements
    )

    if updated_requirements is None:

        updated_requirements = requirements

    # =====================================================
    # COMPLETENESS
    # =====================================================

    completeness_status = result.get(

        "completeness_status",

        "INCOMPLETE"
    )

    completeness_score = result.get(

        "completeness_score",

        0
    )

    missing_fields = result.get(

        "missing_fields",

        []
    )

    current_field = result.get(
        "current_field",
        "business_objective"
    )

    # =====================================================
    # SAVE AGENT MESSAGE
    # =====================================================

    agent_message = Message(

        conversation_id=
            conversation.id,

        role="agent",

        content=(
            f"Hi! I got your project name: "
            f"\"{project.project_name}\".\n\n"
            f"Great! Let's build the project requirements "
            f"step by step.\n\n"
            f"{agent_response}"
        )
    )

    db.add(
        agent_message
    )

    # =====================================================
    # UPDATE REQUIREMENTS
    # =====================================================

    requirement_record.requirements = (
        updated_requirements
    )

    requirement_record.completeness_status = (
        completeness_status
    )

    requirement_record.completeness_score = (
        completeness_score
    )

    db.commit()

    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        "status":
            "started",

        "project_id":
            project.id,

        "project_name":
            project.project_name,

        "conversation_id":
            conversation.id,

        "message":
            (
                f"Hi! I got your project name: "
                f"\"{project.project_name}\".\n\n"
                f"Great! Let's build the project requirements "
                f"step by step.\n\n"
                f"{agent_response}"
            ),

        "response":
            (
                f"Hi! I got your project name: "
                f"\"{project.project_name}\".\n\n"
                f"Great! Let's build the project requirements "
                f"step by step.\n\n"
                f"{agent_response}"
            ),

        "requirements":
            updated_requirements,

        "completeness_status":
            completeness_status,

        "completeness_score":
            completeness_score,

        "missing_fields":
            missing_fields,

        "current_field":
            current_field,

        "thread_id":
            request.thread_id
    }

# =========================================================
# SYNC REQUIREMENTS -> PROJECT COLUMNS
# =========================================================

PROJECT_FIELD_MAP = {
    "category": "category",
    "business_objective": "business_objective",
    "target_users": "target_users",
    "problem_statement": "problem_statement",
    "expected_features": "expected_features",
    "technology_preferences": "technology_preferences",
    "timeline": "timeline",
    "additional_instructions": "additional_instructions",
}


def sync_requirements_to_project(project, requirements):

    for req_key, project_attr in PROJECT_FIELD_MAP.items():

        field_data = requirements.get(req_key, {})

        value = field_data.get("value")

        if value is None:
            continue

        if isinstance(value, list):

            value = ", ".join(
                str(item) for item in value
            )

        elif not isinstance(value, str):

            value = str(value)

        setattr(project, project_attr, value)
INTERVIEW_FIELDS = [
    "category",
    "business_objective",
    "target_users",
    "problem_statement",
    "expected_features",
    "technology_preferences",
    "timeline",
    "additional_instructions"
]


def find_next_missing_field(requirements):

    for field in INTERVIEW_FIELDS:

        field_data = requirements.get(
            field,
            {}
        )

        value = field_data.get("value")

        if value is None:
            return field

        if isinstance(value, str) and not value.strip():
            return field

    return None

# =========================================================
# CHAT
# =========================================================

@router.post("/chat")
def chat_with_agent(
    request: AgentChatRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    # -----------------------------------------------------
    # VALIDATE
    # -----------------------------------------------------

    if (
        not request.initialize
        and not request.message.strip()
    ):

        raise HTTPException(

            status_code=400,

            detail="Message cannot be empty."
        )


    # -----------------------------------------------------
    # PROJECT
    # -----------------------------------------------------

    project = get_project_or_404(

        request.project_id,

        db,

        current_user
    )


    # -----------------------------------------------------
    # CONVERSATION
    # -----------------------------------------------------

    conversation = get_or_create_conversation(

        project.id,

        db
    )


    # -----------------------------------------------------
    # SAVE USER MESSAGE
    # -----------------------------------------------------

    if not request.initialize:

        user_message = Message(

            conversation_id=conversation.id,

            role="user",

            content=request.message

        )

        db.add(user_message)

        db.commit()


    # -----------------------------------------------------
    # REQUIREMENTS
    # -----------------------------------------------------

    requirement_record, requirements = (
        get_or_create_requirements(

            project.id,

            db

        )
    )
    current_field = find_next_missing_field(
    requirements
    )
    print("\n========================================")
    print("REQUIREMENTS FROM DATABASE")
    print("========================================")
    print(requirements)
    print("========================================\n")

    # -----------------------------------------------------
    # LANGGRAPH CONFIG
    # -----------------------------------------------------

    config = {

        "configurable": {

            "thread_id":
                request.thread_id

        }

    }


    # -----------------------------------------------------
    # RUN AGENT
    # -----------------------------------------------------

    try:

        if request.initialize:

            agent_input = {

                "messages": [],

                "project_id":
                    project.id,

                "project_name":
                    project.project_name,

                "user_message":
                    "",

                "retry_count":
                    0,

                "human_approved":
                    False,

                "requirements":
                    requirements

            }

        else:

            agent_input = {

                "messages": [

                    HumanMessage(
                        content=request.message
                    )

                ],

                "project_id":
                    project.id,

                "project_name":
                    project.project_name,

                "user_message":
                    request.message,

                "current_field":
                    current_field,

                "retry_count":
                    0,

                "human_approved":
                    False,

                "requirements":
                    copy.deepcopy(requirements)

            }


        print("\n========================================")
        print("AGENT INPUT")
        print("========================================")
        print("INITIALIZE:", request.initialize)
        print("MESSAGE:", repr(request.message))
        print("PROJECT ID:", project.id)
        print("PROJECT NAME:", project.project_name)
        print("THREAD ID:", request.thread_id)
        print("========================================\n")


        result = agent.invoke(

            agent_input,

            config

        )


        print("\n========================================")
        print("AGENT RESULT")
        print("========================================")

        print(
            "AGENT RESPONSE:",
            result.get("agent_response")
        )

        print(
            "CURRENT FIELD:",
            result.get("current_field")
        )

        print(
            "MISSING FIELDS:",
            result.get("missing_fields")
        )

        print(
            "COMPLETENESS:",
            result.get("completeness_status")
        )

        print(
            "MESSAGES:",
            result.get("messages")
        )

        print("========================================\n")


    except Exception as e:

        print(
            "AGENT ERROR:",
            str(e)
        )

        raise HTTPException(

            status_code=500,

            detail=f"Agent processing failed: {str(e)}"

        )


    # -----------------------------------------------------
    # APPROVAL
    # -----------------------------------------------------

    if "__interrupt__" in result:

        interrupt_data = (
            result["__interrupt__"][0].value
        )

        return {

            "status":
                "approval_required",

            "message":
                interrupt_data.get(
                    "message",
                    "Approval required."
                ),

            "tool":
                interrupt_data.get(
                    "tool"
                ),

            "arguments":
                interrupt_data.get(
                    "arguments"
                ),

            "thread_id":
                request.thread_id,

            "conversation_id":
                conversation.id

        }


    # -----------------------------------------------------
    # AGENT RESPONSE
    # -----------------------------------------------------

    agent_response = result.get(
        "agent_response",
        ""
    )


    if not agent_response:

        agent_response = (
            "I was unable to generate a response."
        )


    print(
        "FINAL AGENT RESPONSE:",
        agent_response
    )


    # -----------------------------------------------------
    # UPDATED REQUIREMENTS
    # -----------------------------------------------------

    updated_requirements = result.get(

        "requirements",

        requirements

    )


    if updated_requirements is None:

        updated_requirements = requirements


    # -----------------------------------------------------
    # COMPLETENESS
    # -----------------------------------------------------

    completeness_status = result.get(

        "completeness_status",

        "INCOMPLETE"

    )


    completeness_score = result.get(

        "completeness_score",

        0

    )


    missing_fields = result.get(

        "missing_fields",

        []

    )


    unclear_fields = result.get(

        "unclear_fields",

        []

    )


    contradictory_fields = result.get(

        "contradictory_fields",

        []

    )


    next_action = result.get(

        "next_action",

        ""

    )


    current_field = result.get(

        "current_field",

        "business_objective"

    )


    # -----------------------------------------------------
    # UPDATE REQUIREMENTS
    # -----------------------------------------------------

    requirement_record.requirements = (
        updated_requirements
    )

    requirement_record.completeness_status = (
        completeness_status
    )

    requirement_record.completeness_score = (
        completeness_score
    )


    # -----------------------------------------------------
    # SAVE AGENT MESSAGE
    # -----------------------------------------------------

    agent_message = Message(

        conversation_id=conversation.id,

        role="agent",

        content=agent_response

    )

    db.add(agent_message)


    # -----------------------------------------------------
    # CONVERSATION STATUS
    # -----------------------------------------------------

    if completeness_status.upper() == "COMPLETE":

        conversation.status = "completed"
        sync_requirements_to_project(
            project,
            updated_requirements
        )

        db.add(project)


    db.commit()


    # -----------------------------------------------------
    # RESPONSE
    # -----------------------------------------------------

    return {

        "status":
            "completed",

        "conversation_id":
            conversation.id,

        "message":
            agent_response,

        "response":
            agent_response,

        "requirements":
            updated_requirements,

        "completeness_status":
            completeness_status,

        "completeness_score":
            completeness_score,

        "missing_fields":
            missing_fields,

        "unclear_fields":
            unclear_fields,

        "contradictory_fields":
            contradictory_fields,

        "next_action":
            next_action,

        "thread_id":
            request.thread_id,

        "current_field":
            current_field,

        "project_id":
            project.id,

        "project_name":
            project.project_name

    }

# =========================================================
# APPROVAL
# =========================================================

@router.post("/approve")
def approve_agent_action(
    request: AgentApprovalRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    config = {

        "configurable": {

            "thread_id": request.thread_id

        }

    }

    try:

        result = agent.invoke(

            Command(
                resume=request.approval
            ),

            config
        )

    except Exception as e:

        print(
            "AGENT APPROVAL ERROR:",
            str(e)
        )

        raise HTTPException(

            status_code=500,

            detail=f"Agent approval failed: {str(e)}"
        )

    if "__interrupt__" in result:

        interrupt_data = (
            result["__interrupt__"][0].value
        )

        return {

            "status": "approval_required",

            "message": interrupt_data.get(

                "message",

                "Approval required."
            ),

            "tool": interrupt_data.get(
                "tool"
            ),

            "arguments": interrupt_data.get(
                "arguments"
            ),

            "thread_id": request.thread_id
        }

    messages = result.get(

        "messages",

        []
    )

    if messages:

        agent_response = messages[-1].content

    else:

        agent_response = "Action completed."

    return {

        "status": "completed",

        "response": agent_response,

        "message": agent_response,

        "thread_id": request.thread_id
    }
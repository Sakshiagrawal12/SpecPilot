from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    File,
    Form
)
from typing import Dict,Optional
import traceback
from pydantic import BaseModel
 
from sqlalchemy.orm import Session
 
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
from app.agents.requirement_manager.agents.document_agent import (
    extract_text_from_file,
    extract_requirements_from_document,
)
from app.agents.generation_manager.diagram_agent import diagram_agent
# =========================================================
# ORCHESTRATOR (replaces the old app.agent.graph import)
# =========================================================
 
from app.agents.orchestrator.graph import orchestrator
 
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
class UpdateRequirementRequest(BaseModel):
    field: str
    value: str
 
# =========================================================
# RUN ONE TURN THROUGH THE ORCHESTRATOR
# =========================================================
#
# Replaces the old direct `agent.invoke(state, config)` calls.
# Requirement Manager handles the interview; once it signals
# completion the orchestrator hands off with next_action ==
# "generate_prd". Generation Manager itself runs separately (via
# /generation/run/{project_id}), since it needs the real DB Project
# row, which the orchestrator deliberately doesn't touch.
#
# thread_id becomes the orchestrator's session_id — a label only,
# nothing currently persists against it inside the orchestrator, since
# this stays stateless per call the same way the old graph.invoke()
# calls were: the caller (this router) already owns persistence via
# ProjectRequirement.
# =========================================================
 
def run_orchestrator_turn(
    thread_id: str,
    project_id: int,
    project_name: str,
    user_message: str,
    requirements: dict,
    current_field: str = None,
    pending_confirmation: bool = False,
    pending_generated_field: str = None,
    pending_generated_value: str = None,
) -> dict:

    orchestrator_state = {
        "thread_id": thread_id,
        "project_id": project_id,
        "project_name": project_name,
        "user_message": user_message,
        "requirements": requirements,
        "current_field": current_field,
        "pending_confirmation": pending_confirmation,
        "pending_generated_field": pending_generated_field,
        "pending_generated_value": pending_generated_value,
    }

    result = orchestrator.invoke(orchestrator_state)

    return {
        "agent_response": result.get("agent_response", ""),
        "next_action": result.get("next_action", "wait_for_user"),
        "active_manager": result.get("active_manager"),
        "requirements": result.get("requirements", requirements),
        "current_field": result.get("current_field"),
        "completeness_status": result.get("requirements_status", "INCOMPLETE"),
        "completeness_score": result.get("requirements_score", 0),
        "missing_fields": result.get("missing_fields", []),
        
        # PERMANENT FIX: Pass pending flags back to caller
        "pending_confirmation": result.get("pending_confirmation", False),
        "pending_generated_field": result.get("pending_generated_field", ""),
        "pending_generated_value": result.get("pending_generated_value", ""),
        "messages": [],
    }
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
    # to the orchestrator.
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
 
        # -------------------------------------------------
        # Even with no conversation row, the project may
        # already have a generated PRD (edge case — e.g. the
        # conversation was cleared after generation). Check
        # here too so the frontend can still redirect instead
        # of starting a brand-new interview over a completed
        # project.
        # -------------------------------------------------
 
        prd_generated = (
            project.product_overview is not None
            and project.product_overview.strip() != ""
        )
 
        return {
            "status": "empty",
            "conversation_id": None,
            "messages": [],
            "prd_generated": prd_generated
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
 
    next_action = (
        "generate_prd"
        if requirement_record.completeness_status == "COMPLETE"
        and current_field is None
        else "continue_interview"
    )
 
    # -----------------------------------------------------
    # PRD ALREADY GENERATED?
    # -----------------------------------------------------
    #
    # product_overview is always the first key PRDGenerator
    # validates before returning, so it's non-empty if and
    # only if /generation/run/{project_id} has already saved
    # a PRD onto this project row.
    # -----------------------------------------------------
 
    prd_generated = (
        project.product_overview is not None
        and project.product_overview.strip() != ""
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
            current_field,
        
        "completeness_status": requirement_record.completeness_status,
        "completeness_score": requirement_record.completeness_score,
        "next_action": next_action,
        "prd_generated": prd_generated
    }
 
class WorkflowDiagramRequest(BaseModel):
    workflow_text: str
 
 
@router.post("/convert-workflow-diagram")
def convert_workflow_diagram(
    request: WorkflowDiagramRequest
):
    if not request.workflow_text or not request.workflow_text.strip():
        raise HTTPException(
            status_code=400,
            detail="Workflow text cannot be empty."
        )
 
    try:
 
        mermaid_code = diagram_agent.generate_diagram(
            request.workflow_text
        )
 
        return {
            "status": "success",
            "mermaid_code": mermaid_code
        }
 
    except Exception as e:
 
        raise HTTPException(
            status_code=500,
            detail=f"Diagram generation failed: {str(e)}"
        )
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
    # START — via orchestrator
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
 
        result = run_orchestrator_turn(
        thread_id=request.thread_id,
        project_id=project.id,
        project_name=project.project_name,

        # /start is always an initialization call
        user_message="",

        requirements=requirements,

        current_field=None,

        pending_confirmation=False,
        pending_generated_field=None,
        pending_generated_value=None,
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
    # AGENT RESPONSE
    # =====================================================
 
    agent_response = result.get(
        "agent_response"
    )
 
    if not agent_response:
 
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
    print("\n========================================")
    print("UPDATED REQUIREMENTS FROM AGENT")
    print("========================================")
    print(updated_requirements)
    print("========================================\n")
 
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
    print("\n========================================")
    print("REQUIREMENTS ASSIGNED TO DB RECORD")
    print("========================================")
    print(requirement_record.requirements)
    print("========================================\n")
 
    requirement_record.completeness_status = (
        completeness_status
    )
 
    requirement_record.completeness_score = (
        completeness_score
    )
 
    db.commit()
    print("\n========================================")
    print("REQUIREMENTS AFTER DB COMMIT")
    print("========================================")
    print(requirement_record.requirements)
    print("========================================\n")
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
            request.thread_id,

        "pending_confirmation": result.get("pending_confirmation", False),
        "pending_generated_field": result.get("pending_generated_field", ""),
        "pending_generated_value": result.get("pending_generated_value", "")
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
    # RUN AGENT — via orchestrator
    # -----------------------------------------------------
 
    try:
 
        print("\n========================================")
        print("AGENT INPUT")
        print("========================================")
        print("INITIALIZE:", request.initialize)
        print("MESSAGE:", repr(request.message))
        print("PROJECT ID:", project.id)
        print("PROJECT NAME:", project.project_name)
        print("THREAD ID:", request.thread_id)
        print("========================================\n")
 
        result = run_orchestrator_turn(
 
            thread_id=request.thread_id,
 
            project_id=project.id,
 
            project_name=project.project_name,
 
            user_message="" if request.initialize else request.message,
 
            requirements=(
                requirements if request.initialize
                else copy.deepcopy(requirements)
            ),
 
            current_field=(
                None if request.initialize else current_field
            ),
 
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
 
        print("========================================\n")
 
 
    except Exception as e:
 
        print(
            "AGENT ERROR:",
            str(e)
        )
        print("FULL TRACEBACK:")
        traceback.print_exc()
        raise HTTPException(
 
            status_code=500,
 
            detail=f"Agent processing failed: {str(e)}"
 
        )
 
 
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

    if completeness_status.upper() == "COMPLETE":
        conversation.status = "completed"

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
#
# NOTE: nothing in this graph ever interrupts (no human-approval
# step exists inside Requirement Manager or Generation Manager), so
# there is never anything to actually resume here. This endpoint is
# kept only so the frontend doesn't get a 404 if it calls it; it
# always falls back to "Action completed."
# =========================================================
 
@router.post("/approve")
def approve_agent_action(
    request: AgentApprovalRequest,
 
    db: Session = Depends(get_db),
 
    current_user: User = Depends(get_current_user)
):
 
    return {
 
        "status": "completed",
 
        "response": "Action completed.",
 
        "message": "Action completed.",
 
        "thread_id": request.thread_id
    }
@router.put("/agent/update-requirement/{project_id}")
def update_project_requirement(
    project_id: int,
    request: UpdateRequirementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    project = get_project_or_404(project_id, db, current_user)
    requirement_record, requirements = get_or_create_requirements(project.id, db)

    field_key = request.field
    new_value = request.value.strip()

    if field_key not in requirements or not isinstance(requirements[field_key], dict):
        requirements[field_key] = {}

    requirements[field_key]["value"] = new_value if new_value else None
    requirements[field_key]["status"] = "PROVIDED" if new_value else "MISSING"

    requirement_record.requirements = copy.deepcopy(requirements)
    sync_requirements_to_project(project, requirements)

    db.add(requirement_record)
    db.add(project)
    db.commit()

    return {"status": "success", "requirements": requirements}
# =========================================================
# UPLOAD DOCUMENT
# =========================================================
 
@router.post("/upload-document/{project_id}")
async def upload_document(
    project_id: int,
 
    thread_id: str = Form(...),
 
    file: UploadFile = File(...),
 
    db: Session = Depends(get_db),
 
    current_user: User = Depends(get_current_user)
):
 
    project = get_project_or_404(project_id, db, current_user)
 
    conversation = get_or_create_conversation(project.id, db)
 
    # -----------------------------------------------------
    # READ + EXTRACT TEXT
    # -----------------------------------------------------
 
    file_bytes = await file.read()
 
    try:
 
        document_text = extract_text_from_file(file.filename, file_bytes)
 
    except ValueError as e:
 
        raise HTTPException(status_code=400, detail=str(e))
 
    if not document_text.strip():
 
        raise HTTPException(
            status_code=400,
            detail="No readable text found in the uploaded document."
        )
 
    # -----------------------------------------------------
    # SAVE USER MESSAGE (attachment note)
    # -----------------------------------------------------
 
    upload_message = Message(
 
        conversation_id=conversation.id,
 
        role="user",
 
        content=f"[Uploaded document: {file.filename}]"
    )
 
    db.add(upload_message)
 
    db.commit()
 
    # -----------------------------------------------------
    # REQUIREMENTS — merge document fields
    # -----------------------------------------------------
 
    requirement_record, requirements = get_or_create_requirements(project.id, db)
 
    try:
 
        doc_result = extract_requirements_from_document(
            document_text=document_text,
            existing_requirements=requirements
        )
 
    except Exception as e:
 
        print("DOCUMENT EXTRACTION ERROR:", str(e))
        traceback.print_exc()
 
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {str(e)}"
        )
 
    updated_requirements = doc_result["requirements"]
    filled_fields = doc_result["filled_fields"]
 
    # -----------------------------------------------------
    # ASK NEXT QUESTION — reuse the orchestrator the same
    # way /start does (empty user_message just advances the
    # interview to whatever field is still missing).
    # -----------------------------------------------------
 
    try:
 
        next_turn = run_orchestrator_turn(
 
            thread_id=thread_id,
 
            project_id=project.id,
 
            project_name=project.project_name,
 
            user_message="",
 
            requirements=updated_requirements,
        )
 
    except Exception as e:
 
        print("ORCHESTRATOR ERROR AFTER UPLOAD:", str(e))
        traceback.print_exc()
 
        raise HTTPException(
            status_code=500,
            detail=f"Failed to continue interview after upload: {str(e)}"
        )
 
    updated_requirements = next_turn.get("requirements", updated_requirements)
 
    completeness_status = next_turn.get("completeness_status", "INCOMPLETE")
    completeness_score = next_turn.get("completeness_score", 0)
    missing_fields = next_turn.get("missing_fields", [])
    current_field = next_turn.get("current_field")
 
    # -----------------------------------------------------
    # BUILD RESPONSE MESSAGE
    # -----------------------------------------------------
 
    if filled_fields:
 
        readable_fields = ", ".join(f.replace("_", " ") for f in filled_fields)
 
        summary = f"I found information for: {readable_fields} in your document."
 
    else:
 
        summary = "I couldn't confidently extract any project details from that document."
 
    next_question = next_turn.get("agent_response", "")
 
    agent_response = f"{summary}\n\n{next_question}".strip()
 

    # -----------------------------------------------------
    # SAVE + PERSIST
    # -----------------------------------------------------
 
    agent_message = Message(
 
        conversation_id=conversation.id,
 
        role="agent",
 
        content=agent_response
    )
 
    db.add(agent_message)
 
    requirement_record.requirements = updated_requirements
    requirement_record.completeness_status = completeness_status
    requirement_record.completeness_score = completeness_score
 
    if completeness_status.upper() == "COMPLETE":
 
        conversation.status = "completed"
        sync_requirements_to_project(project, updated_requirements)
        db.add(project)
 
    db.commit()
 
    return {
 
        "status": "completed",
 
        "message": agent_response,
 
        "response": agent_response,
 
        "filled_fields": filled_fields,
 
        "requirements": updated_requirements,
 
        "completeness_status": completeness_status,
 
        "completeness_score": completeness_score,
 
        "missing_fields": missing_fields,
 
        "next_action": next_turn.get("next_action", ""),
 
        "current_field": current_field,
 
        "thread_id": thread_id,
 
        "project_id": project.id
    }
# =========================================================
# EDIT REQUIREMENT DETAILS  (paste into app/routers/agent.py)
# =========================================================
#
# 1. Add to the imports at the top of agent.py:
#
#        from typing import Dict, Optional
#
# 2. Paste everything below at the END of agent.py (after
#    upload_document). It reuses helpers already defined there:
#    get_project_or_404, get_or_create_requirements,
#    sync_requirements_to_project, PROJECT_FIELD_MAP,
#    INTERVIEW_FIELDS, plus Conversation / Message models.
#
# Why this exists: the agent reads its state from the
# ProjectRequirement row, not from the Project columns. Editing only
# the Project columns would leave the interview using stale values.
# =========================================================

MAX_FIELD_CHARS = 2000


class RequirementsUpdateRequest(BaseModel):

    fields: Dict[str, Optional[str]]


def _flatten_value(field_data) -> str:
    """Return a requirement field as plain text, whatever shape it is stored in."""

    value = (
        field_data.get("value")
        if isinstance(field_data, dict)
        else field_data
    )

    if value is None:
        return ""

    if isinstance(value, list):
        return ", ".join(str(item) for item in value)

    return str(value)


def _prd_exists(project) -> bool:

    return bool(
        project.product_overview
        and project.product_overview.strip()
    )


# ---------------------------------------------------------
# GET: current values for the modal
# ---------------------------------------------------------

@router.get("/requirements/{project_id}")
def get_requirement_details(
    project_id: int,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    project = get_project_or_404(
        project_id,
        db,
        current_user
    )

    record, requirements = get_or_create_requirements(
        project.id,
        db
    )

    return {

        "project_id":
            project.id,

        "project_name":
            project.project_name,

        "fields": {
            field: _flatten_value(requirements.get(field))
            for field in INTERVIEW_FIELDS
        },

        "completeness_status":
            record.completeness_status,

        "prd_generated":
            _prd_exists(project)
    }


# ---------------------------------------------------------
# PATCH: apply manual edits
# ---------------------------------------------------------

@router.patch("/requirements/{project_id}")
def update_requirement_details(
    project_id: int,

    request: RequirementsUpdateRequest,

    db: Session = Depends(get_db),

    current_user: User = Depends(get_current_user)
):

    project = get_project_or_404(
        project_id,
        db,
        current_user
    )

    record, requirements = get_or_create_requirements(
        project.id,
        db
    )

    # -----------------------------------------------------
    # APPLY CHANGED FIELDS
    # -----------------------------------------------------

    changed = []

    for field, raw_value in request.fields.items():

        if field not in INTERVIEW_FIELDS:
            continue

        new_value = (raw_value or "").strip()

        if len(new_value) > MAX_FIELD_CHARS:

            raise HTTPException(
                status_code=400,
                detail=(
                    f"{field.replace('_', ' ').title()} is too long "
                    f"(maximum {MAX_FIELD_CHARS} characters)."
                )
            )

        old_value = _flatten_value(
            requirements.get(field)
        ).strip()

        if new_value == old_value:
            continue

        if new_value:

            requirements[field] = {
                "value": new_value,
                "confidence": 1.0,
                "status": "PROVIDED",
                "source": "user_edit"
            }

        else:

            requirements[field] = {
                "value": None,
                "confidence": 0.0,
                "status": "missing"
            }

            # sync_requirements_to_project() skips empty values,
            # so clear the project column here.
            setattr(
                project,
                PROJECT_FIELD_MAP[field],
                None
            )

        changed.append(field)

    if not changed:

        return {
            "status": "unchanged",
            "changed_fields": [],
            "completeness_status": record.completeness_status,
            "prd_generated": _prd_exists(project)
        }

    # -----------------------------------------------------
    # RECOMPUTE COMPLETENESS
    # -----------------------------------------------------

    missing = [
        field for field in INTERVIEW_FIELDS
        if not _flatten_value(requirements.get(field)).strip()
    ]

    complete = not missing

    filled = len(INTERVIEW_FIELDS) - len(missing)

    # -----------------------------------------------------
    # KEEP THE INTERVIEW ENGINE'S OWN STATE CONSISTENT
    # (only present when the dialogue engine is in use)
    # -----------------------------------------------------

    agent_state = requirements.get("_agent_state")

    if isinstance(agent_state, dict):

        agent_state["pending"] = None
        agent_state["accept_raw"] = None
        agent_state["phase"] = "done" if complete else "interview"

    # -----------------------------------------------------
    # PERSIST
    # -----------------------------------------------------

    record.requirements = requirements

    record.completeness_status = (
        "COMPLETE" if complete else "INCOMPLETE"
    )

    record.completeness_score = int(
        round(100 * filled / len(INTERVIEW_FIELDS))
    )

    sync_requirements_to_project(
        project,
        requirements
    )

    db.add(project)

    # -----------------------------------------------------
    # CONVERSATION: reopen it if something is missing again,
    # and leave a note so the chat history matches reality
    # -----------------------------------------------------

    conversation = (
        db.query(Conversation)
        .filter(Conversation.project_id == project.id)
        .order_by(Conversation.created_at.desc())
        .first()
    )

    if conversation:

        conversation.status = (
            "completed" if complete else "active"
        )

        readable = ", ".join(
            field.replace("_", " ") for field in changed
        )

        note = f"Project details updated: {readable}."

        if complete:
            note += " All requirements are complete."
        else:
            note += (
                " Some requirements are still missing, "
                "so we can continue the interview."
            )

        db.add(
            Message(
                conversation_id=conversation.id,
                role="agent",
                content=note
            )
        )

    db.commit()

    return {

        "status": "updated",

        "changed_fields": changed,

        "completeness_status":
            record.completeness_status,

        "completeness_score":
            record.completeness_score,

        "missing_fields": missing,

        "prd_generated":
            _prd_exists(project)
    }
 

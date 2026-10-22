from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    ForeignKey,
    DateTime,
    JSON,
)
from sqlalchemy.orm import relationship

from app.database import Base


# =========================================================
# USER
# =========================================================

class User(Base):

    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        index=True,
        nullable=False
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    # -----------------------------------------------------
    # RELATIONSHIP
    # -----------------------------------------------------

    projects = relationship(
        "Project",
        back_populates="user",
        cascade="all, delete-orphan"
    )


# =========================================================
# PROJECT
# =========================================================

class Project(Base):

    __tablename__ = "projects"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # -----------------------------------------------------
    # USER
    # -----------------------------------------------------

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # =====================================================
    # ORIGINAL PROJECT INFORMATION
    #
    # These fields are entered by the user/agent.
    # They are NOT AI-generated fields.
    # =====================================================

    project_name = Column(
        String(255),
        nullable=False
    )

    category = Column(
        String(100),
        nullable=True
    )

    business_objective = Column(
        Text,
        nullable=True
    )

    target_users = Column(
        Text,
        nullable=True
    )

    problem_statement = Column(
        Text,
        nullable=True
    )

    expected_features = Column(
        Text,
        nullable=True
    )

    technology_preferences = Column(
        Text,
        nullable=True
    )

    timeline = Column(
        String(255),
        nullable=True
    )

    additional_instructions = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # AI GENERATED DESCRIPTION
    # =====================================================

    overview = Column(
        Text,
        nullable=True
    )

    ai_problem_statement = Column(
        Text,
        nullable=True
    )

    proposed_solution = Column(
        Text,
        nullable=True
    )

    target_audience = Column(
        Text,
        nullable=True
    )

    business_value = Column(
        Text,
        nullable=True
    )

    major_features = Column(
        Text,
        nullable=True
    )

    expected_outcome = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # AI GENERATED PRD
    # =====================================================

    product_overview = Column(
        Text,
        nullable=True
    )

    prd_problem_statement = Column(
        Text,
        nullable=True
    )

    goals_and_objectives = Column(
        Text,
        nullable=True
    )

    prd_target_users = Column(
        Text,
        nullable=True
    )

    functional_requirements = Column(
        Text,
        nullable=True
    )

    user_workflows = Column(
        Text,
        nullable=True
    )

    business_rules = Column(
        Text,
        nullable=True
    )

    non_functional_requirements = Column(
        Text,
        nullable=True
    )

    assumptions_and_dependencies = Column(
        Text,
        nullable=True
    )

    acceptance_criteria = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # AI GENERATED SPRINT PLAN
    # =====================================================

    sprint_plan = Column(
        Text,
        nullable=True
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    user = relationship(
        "User",
        back_populates="projects"
    )

    tasks = relationship(
        "Task",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    conversations = relationship(
        "Conversation",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    requirements = relationship(
        "ProjectRequirement",
        back_populates="project",
        uselist=False,
        cascade="all, delete-orphan"
    )
    transcripts = relationship(
        "Transcript",
        back_populates="project",
        cascade="all, delete-orphan"
    )

# =========================================================
# CONVERSATION
# =========================================================

class Conversation(Base):

    __tablename__ = "conversations"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True
    )

    status = Column(
        String(50),
        default="active",
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # RELATIONSHIPS
    # =====================================================

    project = relationship(
        "Project",
        back_populates="conversations"
    )

    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    


# =========================================================
# MESSAGE
# =========================================================

class Message(Base):

    __tablename__ = "messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    conversation_id = Column(
        Integer,
        ForeignKey("conversations.id"),
        nullable=False,
        index=True
    )

    role = Column(
        String(50),
        nullable=False
    )

    content = Column(
        Text,
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # RELATIONSHIP
    # =====================================================

    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )


# =========================================================
# PROJECT REQUIREMENTS
# =========================================================

class ProjectRequirement(Base):

    __tablename__ = "project_requirements"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        unique=True,
        index=True
    )

    # =====================================================
    # STRUCTURED REQUIREMENT STATE
    #
    # Example:
    #
    # {
    #     "business_objective": {
    #         "value": "...",
    #         "confidence": 0.95,
    #         "status": "complete"
    #     }
    # }
    # =====================================================

    requirements = Column(
        JSON,
        nullable=False,
        default=dict
    )

    # =====================================================
    # COMPLETENESS
    # =====================================================

    completeness_status = Column(
        String(50),
        default="incomplete",
        nullable=False
    )

    completeness_score = Column(
        Integer,
        default=0,
        nullable=False
    )

    # =====================================================
    # TIMESTAMPS
    # =====================================================

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # =====================================================
    # RELATIONSHIP
    # =====================================================

    project = relationship(
        "Project",
        back_populates="requirements"
    )


# =========================================================
# TASK
# =========================================================

class Task(Base):

    __tablename__ = "tasks"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )
    task_number = Column(
        Integer,
        nullable=True
    )
    # =====================================================
    # PROJECT
    # =====================================================

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False
    )

    # =====================================================
    # TASK INFORMATION
    # =====================================================

    task_title = Column(
        String(255),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    task_type = Column(
        String(100),
        nullable=True
    )

    module = Column(
        String(150),
        nullable=True
    )

    priority = Column(
        String(50),
        nullable=True
    )

    acceptance_criteria = Column(
        Text,
        nullable=True
    )

    owner_role = Column(
        String(150),
        nullable=True
    )

    dependencies = Column(
        Text,
        nullable=True
    )

    estimated_complexity = Column(
        String(100),
        nullable=True
    )

    # =====================================================
    # TASK STATUS
    # =====================================================

    status = Column(
        String(50),
        default="Todo",
        nullable=False
    )

    # =====================================================
    # TASK SOURCE
    # =====================================================

    source = Column(
        String(50),
        default="manual",
        nullable=False
    )

    # =====================================================
    # RELATIONSHIP
    # =====================================================

    project = relationship(
        "Project",
        back_populates="tasks"
    )

class Transcript(Base):

    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    audio_filename = Column(String(255))

    raw_text = Column(Text)

    edited_text = Column(Text)

    # transcribing | needs_review | approved | submitted | failed
    status = Column(String(50), default="transcribing", nullable=False)

    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    project = relationship(
        "Project",
        back_populates="transcripts"
    )
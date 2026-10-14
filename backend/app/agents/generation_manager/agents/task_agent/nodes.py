from typing import Any, Dict

from .state import TaskState

from .agents.task_analysis_agent import task_analysis_agent
from .agents.task_generation_agent import task_generation_agent
from .agents.task_critic_agent import task_critic_agent


MAX_REVISIONS = 2


# ============================================================
# TASK ANALYSIS
# ============================================================

def analyze_tasks(state: TaskState) -> Dict[str, Any]:

    try:
        project = state.get("project")
        prd = state.get("prd") or {}

        result = task_analysis_agent.analyze(
            project=project,
            prd=prd,
        )

        return {
            "task_analysis": result,
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "task_analysis": {},
            "status": "failed",
            "error": f"Task analysis failed: {exc}",
        }


# ============================================================
# TASK GENERATION
# ============================================================

def generate_tasks(state: TaskState) -> Dict[str, Any]:

    try:
        project = state.get("project")
        prd = state.get("prd") or {}
        task_analysis = state.get("task_analysis") or {}

        # IMPORTANT:
        # TaskGenerationAgent.generate() requires:
        #
        # project
        # prd
        # task_analysis

        generated_list = task_generation_agent.generate(
            project=project,
            prd=prd,
            task_analysis=task_analysis,
        )

        return {
            "tasks": generated_list,
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "tasks": [],
            "status": "failed",
            "error": f"Task generation failed: {exc}",
        }


# ============================================================
# TASK CRITIQUE
# ============================================================

def critique_tasks(state: TaskState) -> Dict[str, Any]:

    # --------------------------------------------------------
    # Check whether an upstream node failed
    # --------------------------------------------------------

    if state.get("status") == "failed":

        return {
            "critique_status": "failed",
            "critique_feedback": state.get("error")
            or "Task generation failed prior to critique.",
            "error": state.get("error")
            or "Task generation failed prior to critique.",
            "tasks": state.get("tasks") or [],
        }

    # --------------------------------------------------------
    # Get generated tasks
    # --------------------------------------------------------

    tasks = state.get("tasks") or []
    prd = state.get("prd") or {}

    if not tasks:

        return {
            "critique_status": "failed",
            "critique_feedback": "No tasks were generated to critique.",
            "error": "No tasks were generated to critique.",
            "tasks": [],
        }

    # --------------------------------------------------------
    # Run Task Critic Agent
    # --------------------------------------------------------

    try:

        critique_result = task_critic_agent.review(
            prd=prd,
            tasks=tasks,
        )

        status = str(
            critique_result.get("status", "FAIL")
        ).upper()

        issues = critique_result.get("issues", [])
        suggestions = critique_result.get("suggestions", [])

        # ----------------------------------------------------
        # Normalize critic status
        # ----------------------------------------------------

        if status == "PASS":

            critique_status = "approved"

        elif status == "FAIL":

            critique_status = "revise"

        else:

            critique_status = "failed"

        # ----------------------------------------------------
        # Build feedback for revision
        # ----------------------------------------------------

        feedback = {
            "issues": issues,
            "suggestions": suggestions,
        }

        return {
            "critique_status": critique_status,
            "critique_feedback": feedback,
            "tasks": tasks,
            "error": None,
        }

    except Exception as exc:

        return {
            "critique_status": "failed",
            "critique_feedback": f"Critique step crashed: {exc}",
            "error": f"Critique step crashed: {exc}",
            "tasks": tasks,
        }


# ============================================================
# ROUTE AFTER CRITIQUE
# ============================================================

def route_after_critique(state: TaskState) -> str:

    # --------------------------------------------------------
    # If any pipeline step failed
    # --------------------------------------------------------

    if state.get("status") == "failed":

        return "failed"

    if state.get("critique_status") == "failed":

        return "failed"

    # --------------------------------------------------------
    # Approved
    # --------------------------------------------------------

    if state.get("critique_status") == "approved":

        return "approved"

    # --------------------------------------------------------
    # Revision limit
    # --------------------------------------------------------

    revision_count = state.get("revision_count", 0)

    if revision_count >= MAX_REVISIONS:

        return "failed"

    # --------------------------------------------------------
    # Otherwise revise
    # --------------------------------------------------------

    return "revise"


# ============================================================
# PREPARE REVISION
# ============================================================

def prepare_revision(state: TaskState) -> Dict[str, Any]:

    return {
        "revision_count": state.get("revision_count", 0) + 1,
        "status": "in_progress",
        "error": None,
    }
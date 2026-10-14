from typing import Any, Dict

from .state import PRDState

from .agents.product_understanding_agent import (
    product_understanding_agent,
)

from .agents.requirements_agent import (
    requirements_agent,
)

from .agents.user_workflow_agent import (
    user_workflow_agent,
)

from .agents.prd_assembly_agent import (
    prd_assembly_agent,
)

from .agents.prd_critic_agent import (
    prd_critic_agent,
)


# ============================================================
# PRODUCT UNDERSTANDING
# ============================================================

def understand_product(
    state: PRDState,
) -> Dict[str, Any]:

    try:

        result = product_understanding_agent.generate(
            project=state["project"],
            requirements=state["requirements"],
        )

        return {
            "product_understanding": result,
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "status": "failed",
            "error": str(exc),
        }


# ============================================================
# REQUIREMENT ANALYSIS
# ============================================================

def analyze_requirements(
    state: PRDState,
) -> Dict[str, Any]:

    try:

        result = requirements_agent.generate(
            requirements=state["requirements"],
        )

        return {
            "requirement_analysis": result,
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "status": "failed",
            "error": str(exc),
        }


# ============================================================
# WORKFLOW ANALYSIS
# ============================================================

def analyze_workflow(
    state: PRDState,
) -> Dict[str, Any]:

    try:

        result = user_workflow_agent.generate(
            requirements=state["requirements"],
            product_understanding=state[
                "product_understanding"
            ],
        )

        workflows = result.get(
            "workflows",
            [],
        )

        return {
            "user_workflows": workflows,
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "status": "failed",
            "error": str(exc),
        }


# ============================================================
# PRD ASSEMBLY
# ============================================================

def assemble_prd(
    state: PRDState,
) -> Dict[str, Any]:

    try:

        critique = state.get(
            "critique"
        )

        result = prd_assembly_agent.generate(

            project=state["project"],

            requirements=state[
                "requirements"
            ],

            product_understanding=state[
                "product_understanding"
            ],

            requirement_analysis=state[
                "requirement_analysis"
            ],

            user_workflows=state.get(
                "user_workflows",
                [],
            ),

            critique=critique,
        )

        return {
            "prd": result,
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "status": "failed",
            "error": str(exc),
        }


# ============================================================
# PRD CRITIQUE
# ============================================================

def critique_prd(
    state: PRDState,
) -> Dict[str, Any]:

    try:

        result = prd_critic_agent.review(

            requirements=state[
                "requirements"
            ],

            requirement_analysis=state[
                "requirement_analysis"
            ],

            user_workflows=state.get(
                "user_workflows",
                [],
            ),

            prd=state.get("prd"),
        )

        return {
            "critique": result,
            "critique_status": result["status"],
            "status": "in_progress",
            "error": None,
        }

    except Exception as exc:

        return {
            "status": "failed",
            "error": str(exc),
        }


# ============================================================
# REVISION CONTROL
# ============================================================

MAX_REVISIONS = 2


def route_after_critique(
    state: PRDState,
) -> str:

    if state.get("status") == "failed":
        return "failed"

    critique_status = state.get(
        "critique_status",
        "FAIL",
    )

    # Critic approved the PRD
    if critique_status == "PASS":
        return "approved"

    revision_count = state.get(
        "revision_count",
        0,
    )

    # Do not mark a failed PRD as approved.
    if revision_count >= MAX_REVISIONS:
        return "failed"

    return "revise"


# ============================================================
# PREPARE REVISION
# ============================================================

def prepare_revision(
    state: PRDState,
) -> Dict[str, Any]:

    return {
        "revision_count": (
            state.get(
                "revision_count",
                0,
            ) + 1
        ),
        "status": "in_progress",
        "error": None,
    }
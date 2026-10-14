from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class GenerationState(TypedDict, total=False):

    # =========================================================
    # INPUT
    # =========================================================

    project: Any
    requirements: Dict[str, Any]

    # =========================================================
    # CURRENT PIPELINE STAGE
    # =========================================================

    stage: str
    # description
    # prd
    # tasks
    # sprint
    # done

    # =========================================================
    # GENERATED OUTPUTS
    # =========================================================

    description: Optional[Dict[str, Any]]

    prd: Optional[Dict[str, Any]]

    tasks: Optional[List[Dict[str, Any]]]

    sprint_plan: Optional[Any]

    # =========================================================
    # DIAGRAM
    # =========================================================

    workflow: Optional[str]

    diagram: Optional[str]

    # =========================================================
    # PIPELINE STATUS
    # =========================================================

    status: str
    # in_progress
    # complete
    # failed

    error: Optional[str]
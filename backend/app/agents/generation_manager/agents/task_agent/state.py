from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class TaskState(TypedDict, total=False):

    # =====================================================
    # INPUT
    # =====================================================

    project: Any
    requirements: Dict[str, Any]
    prd: Dict[str, Any]

    # =====================================================
    # ANALYSIS
    # =====================================================

    task_analysis: Dict[str, Any]

    # =====================================================
    # GENERATED TASKS
    # =====================================================

    tasks: List[Dict[str, Any]]

    # =====================================================
    # CRITIC
    # =====================================================

    critique_status: Optional[str]
    critique_feedback: Optional[Any]

    # =====================================================
    # CONTROL
    # =====================================================

    revision_count: int
    status: str
    error: Optional[str]
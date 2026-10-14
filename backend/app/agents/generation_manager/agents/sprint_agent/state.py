from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict


class SprintState(TypedDict, total=False):

    # =====================================================
    # INPUT
    # =====================================================

    project: Any

    prd: Dict[str, Any]

    tasks: List[Dict[str, Any]]

    # =====================================================
    # PRIORITY ANALYSIS
    # =====================================================

    prioritized_tasks: List[Dict[str, Any]]

    # =====================================================
    # CAPACITY ANALYSIS
    # =====================================================

    capacity_plan: Dict[str, Any]

    # =====================================================
    # DEPENDENCY ANALYSIS
    # =====================================================

    dependency_plan: Dict[str, Any]

    # =====================================================
    # FINAL SPRINT PLAN
    # =====================================================

    sprint_plan: Any

    # =====================================================
    # REVIEW
    # =====================================================

    review: Dict[str, Any]

    review_status: str

    # =====================================================
    # CONTROL
    # =====================================================

    revision_count: int

    status: str

    error: Optional[str]
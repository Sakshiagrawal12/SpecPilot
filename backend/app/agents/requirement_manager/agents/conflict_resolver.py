# app/agents/requirement_manager/agents/conflict_resolver.py

from typing import Any, Dict

from app.ai.llm import llm
from ..utils import _extract_json


class ConflictResolver:
    """
    Detects and resolves conflicts between an existing requirement
    and a newly extracted value.
    """

    def detect_conflict(
        self,
        field_name: str,
        existing_value: Any,
        new_value: Any,
    ) -> Dict[str, Any]:

        if existing_value is None:
            return {
                "has_conflict": False,
                "reason": "",
            }

        if new_value is None:
            return {
                "has_conflict": False,
                "reason": "",
            }

        prompt = f"""
You are a conflict detection component in a software
requirement-gathering system.

FIELD:
{field_name}

EXISTING REQUIREMENT:
{existing_value}

NEW USER INFORMATION:
{new_value}

Determine whether the new information clearly contradicts
the existing requirement.

Do NOT treat additional information as a conflict.

Return JSON only:

{{
    "has_conflict": true,
    "reason": "short explanation"
}}

or

{{
    "has_conflict": false,
    "reason": ""
}}
"""

        response = llm.generate(prompt)

        result = _extract_json(response)

        return {
            "has_conflict": bool(
                result.get("has_conflict", False)
            ),
            "reason": result.get("reason", ""),
        }

    def resolve_conflict(
        self,
        field_name: str,
        existing_value: Any,
        new_value: Any,
    ) -> Dict[str, Any]:

        prompt = f"""
You are resolving a conflict in a software project
requirement.

FIELD:
{field_name}

EXISTING VALUE:
{existing_value}

NEW VALUE:
{new_value}

Determine the safest interpretation.

Rules:
1. Do not invent information.
2. Do not silently combine contradictory values.
3. If the new value clearly represents a correction,
   prefer the new value.
4. If the situation is ambiguous, request clarification.

Return JSON only:

{{
    "action": "replace" | "keep" | "clarify",
    "resolved_value": "...",
    "reason": "short explanation"
}}
"""

        response = llm.generate(prompt)

        result = _extract_json(response)

        return {
            "action": result.get("action", "clarify"),
            "resolved_value": result.get("resolved_value"),
            "reason": result.get("reason", ""),
        }
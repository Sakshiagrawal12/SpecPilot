# app/agents/requirement_manager/agents/question_planner.py

from typing import Any, Dict, List
from app.ai.llm import llm
from ..utils import _extract_json


class RequirementQuestionPlanner:
    def generate_question(
        self,
        field_name: str,
        requirements: Dict[str, Any],
        document_summary: str = "",
        document_filled_fields=None,
        evaluation_context: str = "",
        recent_messages: str = "",  # <--- Added Chat Memory parameter
    ) -> Dict[str, Any]:

        if document_filled_fields is None:
            document_filled_fields = []

        field_data = requirements.get(field_name, {})
        existing_value = field_data.get("value")
        source = field_data.get("source")

        prompt = f"""
You are the Requirement Question Planner for SpecPilot.

Your job is to generate the next response or question for the project requirement gathering process.

=========================================================
CURRENT FIELD: {field_name}
EXISTING FIELD VALUE: {existing_value} (Source: {source})
=========================================================
UPLOADED DOCUMENT CONTEXT:
{document_summary or "No document uploaded."}
=========================================================
RECENT CONVERSATION HISTORY:
{recent_messages or "No recent messages."}
=========================================================

RULES FOR MEMORY & CONTINUITY:
1. Always reference previously agreed details (e.g., category, target audience) when formulating questions or examples.
2. If the user asks about something mentioned earlier in the conversation, explicitly answer their question using the RECENT CONVERSATION HISTORY before asking for the missing field.
3. Do NOT ask for information that has already been provided or confirmed in the chat history.
4. Keep the question project-specific and natural. Never output hardcoded static examples like 'small restaurant owners' unless relevant.

Return JSON only:
{{
    "question": "your contextual response or question",
    "reason": "explanation of what detail is missing or being answered"
}}
"""
        response = llm.generate(prompt)
        result = _extract_json(response)

        return {
            "question": (result.get("question") or "").strip(),
            "reason": (result.get("reason") or "").strip(),
        }
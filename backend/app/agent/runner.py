from typing import Dict, Any

from app.agent.graph import agent


# =========================================================
# REQUIREMENT INITIALIZATION
# =========================================================

def create_empty_requirements() -> Dict[str, Dict[str, Any]]:
    return {
        "project_name": {
            "value": None,
            "status": "MISSING"
        },
        "business_objective": {
            "value": None,
            "status": "MISSING"
        },
        "target_users": {
            "value": None,
            "status": "MISSING"
        },
        "problem_statement": {
            "value": None,
            "status": "MISSING"
        },
        "expected_features": {
            "value": None,
            "status": "MISSING"
        },
        "technology_preferences": {
            "value": None,
            "status": "MISSING"
        },
        "timeline": {
            "value": None,
            "status": "MISSING"
        },
        "additional_instructions": {
            "value": None,
            "status": "MISSING"
        }
    }


# =========================================================
# CREATE INITIAL AGENT STATE
# =========================================================

def create_initial_state(user_message: str) -> Dict[str, Any]:
    return {
        "user_message": user_message,
        "requirements": create_empty_requirements(),
        "messages": [],
        "missing_fields": [],
        "unclear_fields": [],
        "contradictory_fields": [],
        "completeness_status": "INCOMPLETE",
        "completeness_score": 0,
        "agent_response": "",
        "next_action": "wait_for_user"
    }


# =========================================================
# PROCESS USER MESSAGE
# =========================================================

def process_message(
    user_message: str,
    requirements: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:

    state = {
        "user_message": user_message,
        "requirements": requirements,
        "messages": []
    }

    result = agent.invoke(state)

    return result
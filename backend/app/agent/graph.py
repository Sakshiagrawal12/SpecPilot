from langgraph.graph import StateGraph, START, END

from app.agent.state import AgentState

from app.agent.nodes import (
    extract_requirements,
    evaluate_requirements,
    generate_question,
    requirements_complete,
    _find_next_missing_field
)


def clarification_decision(state: AgentState) -> str:

    if state.get("needs_clarification"):
        return "clarify"

    return "continue"


def ask_clarification(state: AgentState):

    # agent_response was already set by extract_requirements
    return {
        "agent_response": state.get(
            "agent_response",
            "Could you provide a bit more detail?"
        ),
        "next_action": "wait_for_user"
    }
def requirement_decision(state: AgentState) -> str:

    requirements = state.get(
        "requirements",
        {}
    )

    # -----------------------------------------------------
    # IMPORTANT
    # -----------------------------------------------------
    # The conversational interview must continue until
    # ALL INTERVIEW_FIELDS have been collected.
    #
    # Do NOT use evaluator's missing_fields here because
    # evaluator only checks fields marked as required in
    # FIELD_REQUIREMENTS.
    # -----------------------------------------------------

    next_field = _find_next_missing_field(
        requirements
    )

    print("\n==========================================")
    print("GRAPH REQUIREMENT DECISION")
    print("==========================================")
    print("NEXT INTERVIEW FIELD:", next_field)
    print("==========================================\n")

    if next_field:

        return "ask_question"

    return "complete"
def build_agent():

    graph = StateGraph(AgentState)

    graph.add_node("extract_requirements", extract_requirements)
    graph.add_node("evaluate_requirements", evaluate_requirements)
    graph.add_node("ask_question", generate_question)
    graph.add_node("requirements_complete", requirements_complete)
    graph.add_node("ask_clarification", ask_clarification)

    graph.add_edge(START, "extract_requirements")

    graph.add_conditional_edges(

        "extract_requirements",

        clarification_decision,

        {
            "clarify": "ask_clarification",
            "continue": "evaluate_requirements"
        }
    )

    graph.add_conditional_edges(

        "evaluate_requirements",

        requirement_decision,

        {
            "ask_question": "ask_question",
            "complete": "requirements_complete"
        }
    )

    graph.add_edge("ask_clarification", END)
    graph.add_edge("ask_question", END)
    graph.add_edge("requirements_complete", END)

    return graph.compile()


agent = build_agent()
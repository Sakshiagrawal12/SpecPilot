from langgraph.graph import StateGraph, START, END

from app.agents.requirement_manager.state import RequirementState

from app.agents.requirement_manager.agents.conversation_agent import handle_user_question_or_suggestion
from app.agents.requirement_manager.nodes import (
    # -------------------------------------------------
    # NORMAL CONVERSATION
    # -------------------------------------------------
    classify_and_route,
    route_after_classification,

    handle_correction,
    handle_question,

    generate_for_me,
    handle_skip,
    accept_generated_value,
    reject_generated_value,

    extract_and_score,
    route_after_extraction,

    respond_off_track,
    respond_blank,
    respond_clarify,

    accept_and_store,

    # -------------------------------------------------
    # EVALUATION
    # -------------------------------------------------
    evaluate_requirements,
    requirement_decision,

    generate_question,
    requirements_complete,

    # -------------------------------------------------
    # DOCUMENT
    # -------------------------------------------------
    process_uploaded_document,
)


# =====================================================
# INITIAL ROUTER
# =====================================================

def route_initial_state(state: RequirementState):

    uploaded_filename = getattr(
        state,
        "uploaded_filename",
        None,
    )

    uploaded_file_bytes = getattr(
        state,
        "uploaded_file_bytes",
        None,
    )

    document_processed = getattr(
        state,
        "document_processed",
        False,
    )

    # -------------------------------------------------
    # DOCUMENT EXISTS BUT HAS NOT BEEN PROCESSED
    # -------------------------------------------------

    if (
        uploaded_filename
        and uploaded_file_bytes
        and not document_processed
    ):
        return "process_document"

    # -------------------------------------------------
    # NORMAL CHAT FLOW
    # -------------------------------------------------

    return "classify"


# =====================================================
# BUILD GRAPH
# =====================================================

def build_agent():

    graph = StateGraph(RequirementState)

    # =================================================
    # NODES
    # =================================================

    # -------------------------------------------------
    # INITIAL DOCUMENT PROCESSING
    # -------------------------------------------------

    graph.add_node(
        "process_document",
        process_uploaded_document,
    )

    # -------------------------------------------------
    # NORMAL CONVERSATION
    # -------------------------------------------------

    graph.add_node(
        "classify_and_route",
        classify_and_route,
    )

    graph.add_node(
        "handle_correction",
        handle_correction,
    )

    graph.add_node(
        "handle_question",
        handle_user_question_or_suggestion,  # Integrated full context question/suggestion handler
    )

    graph.add_node(
        "generate_for_me",
        generate_for_me,
    )

    graph.add_node(
        "handle_skip",
        handle_skip,
    )

    graph.add_node(
        "accept_generated_value",
        accept_generated_value,
    )

    graph.add_node(
        "reject_generated_value",
        reject_generated_value,
    )

    graph.add_node(
        "extract_and_score",
        extract_and_score,
    )

    # -------------------------------------------------
    # RESPONSE NODES
    # -------------------------------------------------

    graph.add_node(
        "respond_off_track",
        respond_off_track,
    )

    graph.add_node(
        "respond_blank",
        respond_blank,
    )

    graph.add_node(
        "respond_clarify",
        respond_clarify,
    )

    graph.add_node(
        "accept_and_store",
        accept_and_store,
    )

    # -------------------------------------------------
    # EVALUATION
    # -------------------------------------------------

    graph.add_node(
        "evaluate_requirements",
        evaluate_requirements,
    )

    graph.add_node(
        "ask_question",
        generate_question,
    )

    graph.add_node(
        "requirements_complete",
        requirements_complete,
    )

    # =================================================
    # START
    # =================================================

    graph.add_conditional_edges(
        START,
        route_initial_state,
        {
            "process_document": "process_document",
            "classify": "classify_and_route",
        },
    )

    # =================================================
    # DOCUMENT FLOW
    # =================================================

    graph.add_edge(
        "process_document",
        "evaluate_requirements",
    )

    # =================================================
    # CLASSIFICATION ROUTING
    # =================================================

    graph.add_conditional_edges(
        "classify_and_route",
        route_after_classification,
        {
            "confirmation": "accept_generated_value",
            "accept_proposal": "accept_generated_value",
            "rejection": "reject_generated_value",
            "reject_proposal": "reject_generated_value",
            "correction": "handle_correction",
            "question": "handle_question",
            "generate_for_me": "generate_for_me",
            "skip": "handle_skip",
            "extract": "extract_and_score",
        },
    )

    # =================================================
    # DIRECT RESPONSE NODES
    # =================================================

    graph.add_edge(
        "handle_correction",
        END,
    )

    graph.add_edge(
        "handle_question",
        "evaluate_requirements",
    )

    graph.add_edge(
        "generate_for_me",
        END,
    )

    graph.add_edge(
        "handle_skip",
        END,
    )

    graph.add_edge(
        "accept_generated_value",
        "evaluate_requirements",
    )

    graph.add_edge(
        "reject_generated_value",
        END,
    )

    # =================================================
    # EXTRACTION ROUTING
    # =================================================

    graph.add_conditional_edges(
        "extract_and_score",
        route_after_extraction,
        {
            "off_track": "respond_off_track",

            "blank": "respond_blank",

            "blank_capped": "accept_and_store",

            "low_conf": "respond_clarify",

            "low_conf_capped": "accept_and_store",

            "accepted": "accept_and_store",

            "evaluate": "evaluate_requirements",
        },
    )

    # =================================================
    # EXTRACTION RESPONSE NODES
    # =================================================

    graph.add_edge(
        "respond_off_track",
        END,
    )

    graph.add_edge(
        "respond_blank",
        END,
    )

    graph.add_edge(
        "respond_clarify",
        END,
    )

    # =================================================
    # ACCEPT NORMAL USER ANSWER
    # =================================================

    graph.add_edge(
        "accept_and_store",
        "evaluate_requirements",
    )

    # =================================================
    # EVALUATION
    # =================================================

    graph.add_conditional_edges(
        "evaluate_requirements",
        requirement_decision,
        {
            "ask_question": "ask_question",
            "complete": "requirements_complete",
        },
    )

    # =================================================
    # FINAL NODES
    # =================================================

    graph.add_edge(
        "ask_question",
        END,
    )

    graph.add_edge(
        "requirements_complete",
        END,
    )

    # =================================================
    # COMPILE
    # =================================================

    return graph.compile()


# =====================================================
# GRAPH INSTANCE
# =====================================================

requirement_manager_graph = build_agent()
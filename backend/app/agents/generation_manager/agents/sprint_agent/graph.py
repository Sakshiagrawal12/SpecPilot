from langgraph.graph import StateGraph, START, END

from .state import SprintState

from .nodes import (
    analyze_priority,
    analyze_capacity,
    analyze_dependencies,
    build_sprint_plan,
    review_sprint_plan,
    prepare_revision,
    route_after_review,
)


def build_sprint_agent():

    graph = StateGraph(SprintState)

    # =====================================================
    # NODES
    # =====================================================

    graph.add_node(
        "analyze_priority",
        analyze_priority,
    )

    graph.add_node(
        "analyze_capacity",
        analyze_capacity,
    )

    graph.add_node(
        "analyze_dependencies",
        analyze_dependencies,
    )

    graph.add_node(
        "build_sprint_plan",
        build_sprint_plan,
    )

    graph.add_node(
        "review_sprint_plan",
        review_sprint_plan,
    )

    graph.add_node(
        "prepare_revision",
        prepare_revision,
    )

    # =====================================================
    # INITIAL FLOW
    # =====================================================

    graph.add_edge(
        START,
        "analyze_priority",
    )

    graph.add_edge(
        "analyze_priority",
        "analyze_capacity",
    )

    graph.add_edge(
        "analyze_capacity",
        "analyze_dependencies",
    )

    graph.add_edge(
        "analyze_dependencies",
        "build_sprint_plan",
    )

    graph.add_edge(
        "build_sprint_plan",
        "review_sprint_plan",
    )

    # =====================================================
    # REVIEW ROUTING
    # =====================================================

    graph.add_conditional_edges(
        "review_sprint_plan",
        route_after_review,
        {
            "approved": END,
            "revise": "prepare_revision",
            "failed": END,
        },
    )

    # =====================================================
    # REVISION
    # =====================================================

    graph.add_edge(
        "prepare_revision",
        "analyze_priority",
    )

    return graph.compile()


sprint_agent = build_sprint_agent()
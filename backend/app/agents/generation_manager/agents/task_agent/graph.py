from langgraph.graph import StateGraph, START, END

from .state import TaskState

from .nodes import (
    analyze_tasks,
    generate_tasks,
    critique_tasks,
    prepare_revision,
    route_after_critique,
)


def build_task_agent():

    graph = StateGraph(TaskState)

    # =====================================================
    # NODES
    # =====================================================

    graph.add_node(
        "analyze_tasks",
        analyze_tasks,
    )

    graph.add_node(
        "generate_tasks",
        generate_tasks,
    )

    graph.add_node(
        "critique_tasks",
        critique_tasks,
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
        "analyze_tasks",
    )

    graph.add_edge(
        "analyze_tasks",
        "generate_tasks",
    )

    graph.add_edge(
        "generate_tasks",
        "critique_tasks",
    )

    # =====================================================
    # CRITIC ROUTING
    # =====================================================

    graph.add_conditional_edges(
        "critique_tasks",
        route_after_critique,
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
        "generate_tasks",
    )

    return graph.compile()


task_agent = build_task_agent()
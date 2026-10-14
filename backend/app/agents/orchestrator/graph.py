from langgraph.graph import StateGraph, START, END

from app.agents.orchestrator.state import OrchestratorState

from app.agents.orchestrator.nodes import (
    run_requirement_manager,
    route_after_requirement_manager,
)


def build_orchestrator():

    graph = StateGraph(OrchestratorState)

    graph.add_node(
        "requirement_manager",
        run_requirement_manager,
    )

    graph.add_edge(
        START,
        "requirement_manager",
    )

    graph.add_conditional_edges(
        "requirement_manager",
        route_after_requirement_manager,
        {
            "continue": END,
            "complete": END,
        },
    )

    return graph.compile()


orchestrator = build_orchestrator()
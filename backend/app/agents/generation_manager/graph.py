from langgraph.graph import StateGraph, START, END

from app.agents.generation_manager.state import GenerationState
from app.agents.generation_manager.nodes import (
    generate_description,
    generate_prd,
    generate_tasks,
    generate_sprint,
    route_after_stage,
)


def build_generation_manager():

    graph = StateGraph(GenerationState)

    graph.add_node("generate_description", generate_description)
    graph.add_node("generate_prd", generate_prd)
    graph.add_node("generate_tasks", generate_tasks)
    graph.add_node("generate_sprint", generate_sprint)

    graph.add_edge(START, "generate_description")

    # Each stage checks its own status before continuing — a failure
    # at any point stops the pipeline instead of generating a PRD from
    # a broken description, or a sprint plan from broken tasks.
    graph.add_conditional_edges(
        "generate_description",
        route_after_stage,
        {"continue": "generate_prd", "failed": END},
    )

    graph.add_conditional_edges(
        "generate_prd",
        route_after_stage,
        {"continue": "generate_tasks", "failed": END},
    )

    graph.add_conditional_edges(
        "generate_tasks",
        route_after_stage,
        {"continue": "generate_sprint", "failed": END},
    )

    graph.add_edge("generate_sprint", END)

    return graph.compile()


generation_manager = build_generation_manager()

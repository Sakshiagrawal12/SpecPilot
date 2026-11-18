from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from .state import PRDState

from .nodes import (
    understand_product,
    analyze_requirements,
    analyze_workflow,
    assemble_prd,
    critique_prd,
    prepare_revision,
    route_after_critique,
)

def route_after_assembly(state: PRDState) -> str:
    if state.get("status") == "failed":
        return "failed"

    prd = state.get("prd")

    if not isinstance(prd, dict) or not prd:
        return "failed"

    return "continue"

def build_prd_agent():

    graph = StateGraph(PRDState)

    # --------------------------------------------------------
    # Nodes
    # --------------------------------------------------------

    graph.add_node(
        "understand_product",
        understand_product,
    )

    graph.add_node(
        "analyze_requirements",
        analyze_requirements,
    )

    graph.add_node(
        "analyze_workflow",
        analyze_workflow,
    )

    graph.add_node(
        "assemble_prd",
        assemble_prd,
    )

    graph.add_node(
        "critique_prd",
        critique_prd,
    )

    graph.add_node(
        "prepare_revision",
        prepare_revision,
    )

    # --------------------------------------------------------
    # Initial flow
    # --------------------------------------------------------

    graph.add_edge(
        START,
        "understand_product",
    )

    graph.add_edge(
        "understand_product",
        "analyze_requirements",
    )

    graph.add_edge(
        "analyze_requirements",
        "analyze_workflow",
    )

    graph.add_edge(
        "analyze_workflow",
        "assemble_prd",
    )

    graph.add_conditional_edges(
    "assemble_prd",
    route_after_assembly,
    {
        "continue": "critique_prd",
        "failed": END,
    },
    )

    # --------------------------------------------------------
    # Critic routing
    # --------------------------------------------------------

    graph.add_conditional_edges(
        "critique_prd",
        route_after_critique,
        {
            "approved": END,
            "revise": "prepare_revision",
            "failed": END,
        },
    )

    # --------------------------------------------------------
    # Revision loop
    # --------------------------------------------------------

    graph.add_edge(
        "prepare_revision",
        "assemble_prd",
    )

    return graph.compile()


prd_agent = build_prd_agent()
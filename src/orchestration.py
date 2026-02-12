"""
LangGraph orkestrasyonu: Analyst → Researcher | Coder | General
Mevcut ajanlar (analyst, researcher, coder) ve client dışarıdan verilir; sadece akış burada tanımlanır.
"""
from typing import TypedDict, Literal
from langgraph.graph import StateGraph, END


class AgentState(TypedDict):
    query: str
    decision: dict
    response: str


def build_graph(analyst, researcher, coder, client):
    """
    Grafiği oluşturur ve derler. main.py'den çağrılır.
    """
    async def analyst_node(state: AgentState) -> dict:
        decision = await analyst.analyze(state["query"])
        return {"decision": decision}

    async def researcher_node(state: AgentState) -> dict:
        response = await researcher.research(state["query"])
        return {"response": response}

    async def coder_node(state: AgentState) -> dict:
        response = await coder.solve(state["query"])
        return {"response": response}

    async def general_node(state: AgentState) -> dict:
        response = await client.ask(state["query"], task_type="general")
        return {"response": response}

    def route_after_analyst(state: AgentState) -> Literal["researcher", "coder", "general"]:
        decision = state.get("decision") or {}
        task_type = decision.get("task_type", "general")
        if not isinstance(task_type, str):
            return "general"
        t = task_type.lower()
        if t in ("web_search", "rag") or "search" in t or "research" in t:
            return "researcher"
        if t in ("coding", "code", "calculate") or "code" in t:
            return "coder"
        return "general"

    workflow = StateGraph(AgentState)
    workflow.add_node("analyst", analyst_node)
    workflow.add_node("researcher", researcher_node)
    workflow.add_node("coder", coder_node)
    workflow.add_node("general", general_node)

    workflow.set_entry_point("analyst")
    workflow.add_conditional_edges(
        "analyst",
        route_after_analyst,
        path_map={
            "researcher": "researcher",
            "coder": "coder",
            "general": "general",
        },
    )
    workflow.add_edge("researcher", END)
    workflow.add_edge("coder", END)
    workflow.add_edge("general", END)

    return workflow.compile()

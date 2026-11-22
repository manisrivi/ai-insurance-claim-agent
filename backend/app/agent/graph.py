# graph.py: connects the desks (nodes) with edges, and saves progress in Postgres
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from app.agent.nodes import (
    decide_node,
    document_node,
    finalize_node,
    fraud_node,
    mark_for_officer_node,
    officer_node,
    policy_node,
    route_after_decide,
)
from app.agent.state import ClaimState
from app.config import settings


def build_graph(checkpointer=None):
    graph = StateGraph(ClaimState)

    # Desks
    graph.add_node("document", document_node)
    graph.add_node("policy", policy_node)
    graph.add_node("fraud", fraud_node)
    graph.add_node("decide", decide_node)
    graph.add_node("mark_for_officer", mark_for_officer_node)
    graph.add_node("officer", officer_node)
    graph.add_node("finalize", finalize_node)

    # Paths
    graph.add_edge(START, "document")
    graph.add_edge("document", "policy")
    graph.add_edge("policy", "fraud")
    graph.add_edge("fraud", "decide")
    graph.add_conditional_edges("decide", route_after_decide, ["mark_for_officer", "finalize"])
    graph.add_edge("mark_for_officer", "officer")
    graph.add_edge("officer", "finalize")
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=checkpointer)


# Separate small pool for the checkpointer.
# prepare_threshold=0 = no prepared statements (safer with the Supabase pooler)
checkpoint_pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=3,
    kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    open=False,
)


def open_checkpointer() -> PostgresSaver:
    # Connect and create LangGraph's own tables (safe to run every start)
    checkpoint_pool.open(wait=True)
    saver = PostgresSaver(checkpoint_pool)
    saver.setup()
    return saver


def close_checkpointer() -> None:
    checkpoint_pool.close()

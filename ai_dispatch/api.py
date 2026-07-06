"""
Whitelisted API methods for the AI Dispatch app.

Called from the frontend as:
    /api/method/ai_dispatch.api.chat
    /api/method/ai_dispatch.api.list_agents
    /api/method/ai_dispatch.api.ingest_document
    /api/method/ai_dispatch.api.train_router
"""

import uuid

import frappe

from ai_dispatch.rag.embeddings import embed_texts
from ai_dispatch.rag.vector_store import query_documents
from ai_dispatch.router.classifier import load_model, predict_label
from ai_dispatch.llm.generator import generate_response


def get_cached_agents():
    """
    Enabled agents, cached in-process (invalidated by AIAgent.on_update),
    since this is looked up on every single chat request.
    """
    cached = frappe.cache().get_value("ai_dispatch:agents")
    if cached:
        return cached

    agents = frappe.get_all(
        "AI Agent",
        filters={"enabled": 1},
        fields=["agent_key", "agent_label", "system_prompt", "color"],
    )
    agent_map = {a["agent_key"]: a for a in agents}
    frappe.cache().set_value("ai_dispatch:agents", agent_map)
    return agent_map


@frappe.whitelist()
def list_agents():
    agents = get_cached_agents()
    return [
        {"agent_key": key, "agent_label": a["agent_label"], "color": a.get("color")}
        for key, a in agents.items()
    ]


@frappe.whitelist()
def chat(query: str, session_id: str = None):
    if not query or not query.strip():
        frappe.throw("Query cannot be empty.")

    session_id = session_id or str(uuid.uuid4())
    agents = get_cached_agents()

    if len(agents) < 2:
        frappe.throw(
            "Need at least 2 enabled AI Agent records before chatting. "
            "Create some under AI Agent in the Desk."
        )

    try:
        model, labels = load_model()
    except FileNotFoundError as e:
        frappe.throw(str(e))

    embedding = embed_texts([query])[0]
    routing_result = predict_label(model, labels, embedding)
    predicted_key = routing_result["predicted_agent"]
    agent = agents.get(predicted_key)

    if agent is None:
        frappe.throw(
            f"Router predicted agent '{predicted_key}', but no enabled AI Agent "
            f"with that key exists. Retrain the router or check your agents."
        )

    settings = frappe.get_single("AI Dispatch Settings")
    top_k = settings.top_k or 3

    context_chunks = query_documents(predicted_key, query, top_k=top_k)
    answer = generate_response(
        system_prompt=agent["system_prompt"],
        context_chunks=context_chunks,
        user_query=query,
    )

    _log_turn(session_id, "User", None, query, None, None)
    _log_turn(
        session_id,
        "Agent",
        predicted_key,
        answer,
        routing_result["confidence_scores"],
        context_chunks,
    )

    return {
        "session_id": session_id,
        "agent": predicted_key,
        "agent_label": agent["agent_label"],
        "answer": answer,
        "retrieved_context": context_chunks,
        "routing": routing_result,
    }


def _log_turn(session_id, role, agent_key, content, confidence_scores, context_chunks):
    try:
        frappe.get_doc(
            {
                "doctype": "AI Chat Message",
                "session_id": session_id,
                "role": role,
                "agent": agent_key,
                "user": frappe.session.user,
                "content": content,
                "confidence_scores": frappe.as_json(confidence_scores) if confidence_scores else None,
                "retrieved_context": frappe.as_json(context_chunks) if context_chunks else None,
            }
        ).insert(ignore_permissions=True)
    except Exception:
        # Logging failures shouldn't break the chat response itself.
        frappe.log_error(title="AI Dispatch: failed to log chat message", message=frappe.get_traceback())


@frappe.whitelist()
def ingest_document(agent_key: str, content: str, source_label: str = None):
    frappe.only_for("System Manager")

    if not frappe.db.exists("AI Agent", agent_key):
        frappe.throw(f"No AI Agent with key '{agent_key}' exists.")

    doc = frappe.get_doc(
        {
            "doctype": "AI Agent Document",
            "agent": agent_key,
            "content": content,
            "source_label": source_label,
        }
    ).insert()

    return {"name": doc.name, "agent": agent_key}


@frappe.whitelist()
def train_router():
    frappe.only_for("System Manager")
    from ai_dispatch.router.train import train_router as _train

    result = _train()
    frappe.cache().delete_value("ai_dispatch:agents")
    return result

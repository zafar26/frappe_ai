"""
ChromaDB wrapper. Each AI Agent gets its own isolated collection, keyed
by its agent_key, so agents never retrieve each other's knowledge.

Storage lives under the current site's private files directory, so it's
backed up with the site and isolated per-site on multi-tenant benches.
"""

import os
from functools import lru_cache
from typing import List, Optional

import chromadb
import frappe

from frappe_ai.rag.embeddings import embed_texts


def _chroma_path() -> str:
    path = frappe.get_site_path("private", "files", "frappe_ai", "chroma_db")
    os.makedirs(path, exist_ok=True)
    return path


def _get_client():
    # Not cached across requests via lru_cache -- PersistentClient handles
    # its own on-disk locking, and Frappe's per-request lifecycle makes a
    # process-wide singleton risky across worker forks. Re-opening it is
    # cheap relative to the embedding/LLM calls anyway.
    return chromadb.PersistentClient(path=_chroma_path())


def get_or_create_collection(agent_key: str):
    client = _get_client()
    return client.get_or_create_collection(name=f"agent_{agent_key}")


# ---------------------------------------------------------------------------
# Optional auto-categorization metadata (zero-shot classification)
#
# Stored as extra Chroma metadata for future filtering/search -- NOT used
# for routing or retrieval today. Deliberately fail-safe: any failure here
# (model won't load, classification errors, etc.) NEVER blocks the actual
# embed/upsert -- the document always gets stored, worst case without a
# category tag. An optional metadata feature should never be able to break
# core RAG functionality.
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _get_zero_shot_classifier():
    """
    Loaded once per process and cached -- this is a ~1.6GB model
    (facebook/bart-large-mnli), so reloading it on every document save
    would be far too slow (potentially tens of seconds each time, risking
    request timeouts). Caching means only the FIRST save after a bench
    restart pays that cost; every save after that just runs inference
    against the already-loaded model.
    """
    from transformers import pipeline

    return pipeline("zero-shot-classification", model="facebook/bart-large-mnli", device=-1)


def _get_candidate_labels() -> List[str]:
    """
    Pull current agent_keys dynamically rather than hardcoding a label
    list, so this stays in sync automatically as agents are added/renamed
    -- same pattern the router already uses for its labels.
    """
    return frappe.get_all("AI Agent", filters={"enabled": 1}, pluck="name")


def _classify_content(content: str) -> dict:
    """Best-effort auto-categorization. Never raises."""
    try:
        candidate_labels = _get_candidate_labels()
        if not content or not candidate_labels:
            return {"auto_category": "unclassified", "confidence_score": 0.0}

        classifier = _get_zero_shot_classifier()
        result = classifier(content, candidate_labels=candidate_labels)
        return {
            "auto_category": result["labels"][0],
            "confidence_score": round(float(result["scores"][0]), 4),
        }
    except Exception:
        frappe.log_error(
            title="Frappe AI: auto-categorization failed",
            message=frappe.get_traceback(),
        )
        return {"auto_category": "unclassified", "confidence_score": 0.0}


def add_or_update_document(agent_key: str, doc_id: str, content: str) -> None:
    """
    Embed one AI Agent Document's content, auto-tag it with a zero-shot
    predicted category (stored as Chroma metadata for future filtering --
    not used for retrieval today), and upsert it into Chroma.
    """
    collection = get_or_create_collection(agent_key)
    embedding = embed_texts([content])[0].tolist()
    metadata = _classify_content(content)

    collection.upsert(
        ids=[doc_id],
        documents=[content],
        embeddings=[embedding],
        metadatas=[metadata],
    )


def delete_document(agent_key: str, doc_id: str) -> None:
    collection = get_or_create_collection(agent_key)
    try:
        collection.delete(ids=[doc_id])
    except Exception:
        pass  # already gone / never embedded -- not an error worth surfacing


def query_documents(agent_key: str, query: str, top_k: int = 3) -> List[str]:
    collection = get_or_create_collection(agent_key)
    if collection.count() == 0:
        return []

    query_embedding = embed_texts([query])[0].tolist()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=min(top_k, collection.count()),
    )
    return results["documents"][0] if results.get("documents") else []


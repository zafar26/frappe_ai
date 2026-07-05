"""
ChromaDB wrapper. Each AI Agent gets its own isolated collection, keyed
by its agent_key, so agents never retrieve each other's knowledge.

Storage lives under the current site's private files directory, so it's
backed up with the site and isolated per-site on multi-tenant benches.
"""

import os
from typing import List, Optional

import chromadb
import frappe

from ai_dispatch.rag.embeddings import embed_texts


def _chroma_path() -> str:
    path = frappe.get_site_path("private", "files", "ai_dispatch", "chroma_db")
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


def add_or_update_document(agent_key: str, doc_id: str, content: str) -> None:
    """Embed one AI Agent Document's content and upsert it into Chroma."""
    collection = get_or_create_collection(agent_key)
    embedding = embed_texts([content])[0].tolist()
    collection.upsert(ids=[doc_id], documents=[content], embeddings=[embedding])


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

"""
Shared embedding utility. Used by both the router classifier and the
ChromaDB retrieval pipeline, so we load one embedding model, not two.
"""

import os
from typing import List

import frappe
from sentence_transformers import SentenceTransformer

from frappe_ai.utils import ensure_hf_login

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_DIM = 768

# ✅ Module-level singleton — survives across requests in same worker
_embedder_instance: SentenceTransformer | None = None
_embedder_model_name: str | None = None


def get_embedding_model_name() -> str:
    settings = frappe.get_single("Frappe AI Settings")
    return settings.embedding_model_name or DEFAULT_EMBEDDING_MODEL


def _get_cache_dir() -> str:
    """Store model in site private files — no re-download needed."""
    path = frappe.get_site_path(
        "private", "files", "frappe_ai", "hf_cache"
    )
    os.makedirs(path, exist_ok=True)
    return path


def get_embedder() -> SentenceTransformer:
    global _embedder_instance, _embedder_model_name

    model_name = get_embedding_model_name()

    # ✅ Only load if not loaded or model name changed
    if _embedder_instance is None or _embedder_model_name != model_name:
        ensure_hf_login()
        _embedder_instance = SentenceTransformer(
            model_name,
            cache_folder=_get_cache_dir()  # ✅ local cache — no HTTP on reload
        )
        _embedder_model_name = model_name

    return _embedder_instance


def embed_texts(texts: List[str]):
    model = get_embedder()
    return model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
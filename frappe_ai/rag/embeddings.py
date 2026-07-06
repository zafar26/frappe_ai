"""
Shared embedding utility. Used by both the router classifier and the
ChromaDB retrieval pipeline, so we load one embedding model, not two.
"""

from functools import lru_cache
from typing import List

import frappe
from sentence_transformers import SentenceTransformer

from frappe_ai.utils import ensure_hf_login

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-mpnet-base-v2"
EMBEDDING_DIM = 384


def get_embedding_model_name() -> str:
    settings = frappe.get_single("Frappe AI Settings")
    return settings.embedding_model_name or DEFAULT_EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _load_embedder(model_name: str) -> SentenceTransformer:
    ensure_hf_login()
    return SentenceTransformer(model_name)


def get_embedder() -> SentenceTransformer:
    return _load_embedder(get_embedding_model_name())


def embed_texts(texts: List[str]):
    model = get_embedder()
    return model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)

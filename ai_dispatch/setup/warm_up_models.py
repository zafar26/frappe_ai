"""
Pre-downloads and caches the embedding model and local LLM so:
  1. Setup has one predictable, visible download step (with progress bars
     in the terminal) instead of silently happening mid-chat.
  2. Every request after this completes runs fully offline, on-device --
     no calls to OpenAI, Anthropic, or any other external AI API.

Run once after installing Python dependencies:
    bench --site <site> execute ai_dispatch.setup.warm_up_models.run

Models are cached in the Hugging Face cache directory (usually
~/.cache/huggingface on Linux/macOS) -- NOT re-downloaded on every site
restart, only once per machine.
"""

from ai_dispatch.rag.embeddings import get_embedder
from ai_dispatch.llm.generator import _get_pipeline


def run():
    print("Downloading/loading embedding model (sentence-transformers)...")
    get_embedder()
    print("Embedding model ready.\n")

    print("Downloading/loading local LLM (this is the bigger one, ~1GB)...")
    _get_pipeline()
    print("Local LLM ready.\n")

    print(
        "Both models are now cached locally. All future chat requests run "
        "entirely on this machine -- no external AI API calls are made."
    )

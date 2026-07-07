"""
Pre-downloads and caches the embedding model and local LLM so:
  1. Setup has one predictable, visible download step (with progress bars
     in the terminal) instead of silently happening mid-chat.
  2. Every request after this completes runs fully offline, on-device --
     no calls to OpenAI, Anthropic, or any other external AI API.

Run once after installing Python dependencies:
    bench --site <site> execute frappe_ai.setup.warm_up_models.run

Models are cached in the Hugging Face cache directory (usually
~/.cache/huggingface on Linux/macOS) -- NOT re-downloaded on every site
restart, only once per machine.
"""

import frappe

from frappe_ai.rag.embeddings import get_embedder
from frappe_ai.utils import get_hf_token


def run():
    if get_hf_token():
        print("Hugging Face token detected -- downloads will be authenticated (higher rate limits).\n")
    else:
        print(
            "No Hugging Face token set -- downloads will still work, just slower and "
            "rate-limited, with a benign 'unauthenticated requests' warning. To remove "
            "that warning, set Frappe AI Settings > Hugging Face Token, or export "
            "HF_TOKEN before running this command. Get a free token at "
            "https://huggingface.co/settings/tokens\n"
        )

    print("Downloading/loading embedding model (sentence-transformers)...")
    get_embedder()
    print("Embedding model ready.\n")

    settings = frappe.get_single("Frappe AI Settings")
    backend = settings.model_backend or "GGUF (llama.cpp)"

    if backend.startswith("GGUF"):
        print("Model Backend is set to GGUF (llama.cpp) -- fetching quantized model...")
        from frappe_ai.setup.fetch_gguf_model import run as fetch_gguf
        fetch_gguf()
    else:
        print(
            "Model Backend is set to Transformers (PyTorch) -- downloading full model "
            "(this is the bigger one, ~1GB)..."
        )
        from frappe_ai.llm.generator import _load_transformers_pipeline, DEFAULT_TRANSFORMERS_MODEL
        model_name = settings.llm_model_name or DEFAULT_TRANSFORMERS_MODEL
        _load_transformers_pipeline(model_name)
        print("Transformers model ready.")

    print(
        "\nAll models are now cached locally. All future chat requests run "
        "entirely on this machine -- no external AI API calls are made."
    )

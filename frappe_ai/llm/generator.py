"""
Local LLM generation, supporting two backends (switchable in Frappe AI
Settings > Model Backend):

  - "GGUF (llama.cpp)" (default) -- quantized model via llama-cpp-python.
    3-5x faster on CPU and uses far less RAM than the Transformers
    backend. The GGUF file is auto-downloaded (Qwen's official
    pre-quantized repo) by setup/fetch_gguf_model.py, or you can point
    at a custom .gguf file (e.g. from scripts/convert_to_gguf.py).

  - "Transformers (PyTorch)" -- the original backend, kept as a fallback
    and for A-B quality comparison. Slower on CPU.
"""

import os
from functools import lru_cache
from typing import List

import frappe

from frappe_ai.utils import ensure_hf_login

DEFAULT_TRANSFORMERS_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"

PRECISION_INSTRUCTIONS = (
    "You are answering inside a Frappe/ERPNext help assistant. Follow these rules strictly:\n"
    "1. Always answer in terms of actual Frappe/ERPNext DocTypes, fields, and navigation -- "
    "never give generic business advice that could apply to any software.\n"
    "2. Where relevant, give the exact Desk navigation path in the form "
    "'Module > DocType > New' or 'DocType list > [button/action]'.\n"
    "3. Use the precise DocType and field names from the context and system prompt "
    "(e.g. say 'Purchase Order', 'Salary Structure Assignment', 'Stock Entry (Material Transfer)' "
    "-- not vague paraphrases like 'the purchasing screen' or 'the HR section').\n"
    "4. Prefer short numbered steps over a paragraph when explaining a process.\n"
    "5. If the retrieved context directly answers the question, base your answer on it "
    "and do not add unrelated general knowledge.\n"
    "6. If the context doesn't cover the question, say so explicitly, then give your best "
    "ERPNext-specific answer -- never fall back to vague, non-ERPNext-specific filler."
)


def _get_settings():
    return frappe.get_single("Frappe AI Settings")


def _build_messages(system_prompt: str, context_chunks: List[str], user_query: str):
    context_block = (
        "\n".join(f"- {chunk}" for chunk in context_chunks)
        if context_chunks
        else "(No specific knowledge base entries were found for this query -- rely on the "
        "DocTypes named in your system prompt and general ERPNext knowledge instead.)"
    )
    return [
        {"role": "system", "content": f"{system_prompt}\n\n{PRECISION_INSTRUCTIONS}"},
        {
            "role": "user",
            "content": (
                f"Relevant knowledge base context:\n{context_block}\n\n"
                f"User question: {user_query}\n\n"
                "Answer precisely, using real Frappe/ERPNext DocType names and navigation "
                "paths as instructed. Do not give a vague or generic answer."
            ),
        },
    ]


# ---------------------------------------------------------------------------
# GGUF backend (llama.cpp) -- default, fast CPU inference
# ---------------------------------------------------------------------------

DEFAULT_GGUF_REPO = "Qwen/Qwen2.5-0.5B-Instruct-GGUF"
DEFAULT_GGUF_FILENAME = "qwen2.5-0.5b-instruct-q4_k_m.gguf"


def gguf_model_path() -> str:
    """Resolve the .gguf file path -- manual override, or the auto-downloaded default location."""
    settings = _get_settings()
    if settings.gguf_model_path:
        return settings.gguf_model_path

    filename = settings.gguf_model_filename or DEFAULT_GGUF_FILENAME
    return os.path.join(
        frappe.get_site_path("private", "files", "frappe_ai", "models"), filename
    )


@lru_cache(maxsize=1)
def _load_gguf(model_path: str, n_ctx: int, n_threads: int, chat_format: str):
    from llama_cpp import Llama

    return Llama(
        model_path=model_path,
        n_ctx=n_ctx,
        n_threads=n_threads,
        chat_format=chat_format,
        verbose=False,
    )


def _get_gguf_llm():
    settings = _get_settings()
    path = gguf_model_path()

    if not os.path.exists(path):
        frappe.throw(
            f"GGUF model not found at {path}. Run: "
            "bench --site [your-site-name] execute frappe_ai.setup.fetch_gguf_model.run"
        )

    return _load_gguf(
        path,
        settings.gguf_n_ctx or 2048,
        settings.gguf_n_threads or 4,
        settings.gguf_chat_format or "chatml",
    )


def _generate_gguf(system_prompt: str, context_chunks: List[str], user_query: str, max_new_tokens: int) -> str:
    llm = _get_gguf_llm()
    messages = _build_messages(system_prompt, context_chunks, user_query)

    result = llm.create_chat_completion(
        messages=messages,
        max_tokens=max_new_tokens,
        temperature=0.3,
        top_p=0.85,
        repeat_penalty=1.1,
    )
    return result["choices"][0]["message"]["content"].strip()


# ---------------------------------------------------------------------------
# Transformers backend (PyTorch) -- fallback / A-B comparison
# ---------------------------------------------------------------------------


@lru_cache(maxsize=1)
def _load_transformers_pipeline(model_name: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

    ensure_hf_login()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.float32, device_map="cpu"
    )
    return pipeline("text-generation", model=model, tokenizer=tokenizer)


def _generate_transformers(system_prompt: str, context_chunks: List[str], user_query: str, max_new_tokens: int) -> str:
    settings = _get_settings()
    model_name = settings.llm_model_name or DEFAULT_TRANSFORMERS_MODEL
    generator = _load_transformers_pipeline(model_name)
    messages = _build_messages(system_prompt, context_chunks, user_query)

    output = generator(
        messages,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.3,
        top_p=0.85,
        repetition_penalty=1.1,
        pad_token_id=generator.tokenizer.eos_token_id,
    )

    generated = output[0]["generated_text"]
    if isinstance(generated, list):
        return generated[-1]["content"].strip()
    return str(generated).strip()


# ---------------------------------------------------------------------------
# Public entry point -- unchanged signature, dispatches to the active backend
# ---------------------------------------------------------------------------


def generate_response(system_prompt: str, context_chunks: List[str], user_query: str) -> str:
    settings = _get_settings()
    max_new_tokens = settings.max_new_tokens or 256
    backend = settings.model_backend or "GGUF (llama.cpp)"

    if backend.startswith("GGUF"):
        return _generate_gguf(system_prompt, context_chunks, user_query, max_new_tokens)
    return _generate_transformers(system_prompt, context_chunks, user_query, max_new_tokens)

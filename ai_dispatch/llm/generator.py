"""
Local LLM generation via Hugging Face `transformers` (PyTorch backend).
Model name is configurable from AI Dispatch Settings in the Desk UI.
"""

from functools import lru_cache
from typing import List

import frappe
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"


def _get_settings():
    return frappe.get_single("AI Dispatch Settings")


@lru_cache(maxsize=1)
def _load_pipeline(model_name: str):
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.float32, device_map="cpu"
    )
    return pipeline("text-generation", model=model, tokenizer=tokenizer)


def _get_pipeline():
    settings = _get_settings()
    model_name = settings.llm_model_name or DEFAULT_MODEL
    return _load_pipeline(model_name)


def generate_response(system_prompt: str, context_chunks: List[str], user_query: str) -> str:
    settings = _get_settings()
    max_new_tokens = settings.max_new_tokens or 256

    context_block = (
        "\n".join(f"- {chunk}" for chunk in context_chunks)
        if context_chunks
        else "(No specific knowledge base entries were found for this query.)"
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Relevant knowledge base context:\n{context_block}\n\n"
                f"User question: {user_query}\n\n"
                "Answer using the context above where relevant. If the context "
                "doesn't cover it, answer helpfully using general knowledge and say so."
            ),
        },
    ]

    generator = _get_pipeline()
    output = generator(
        messages,
        max_new_tokens=max_new_tokens,
        do_sample=True,
        temperature=0.7,
        top_p=0.9,
        pad_token_id=generator.tokenizer.eos_token_id,
    )

    generated = output[0]["generated_text"]
    if isinstance(generated, list):
        return generated[-1]["content"].strip()
    return str(generated).strip()

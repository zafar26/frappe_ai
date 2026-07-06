"""
Local LLM generation via Hugging Face `transformers` (PyTorch backend).
Model name is configurable from Frappe AI Settings in the Desk UI.
"""

from functools import lru_cache
from typing import List

import frappe
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

from frappe_ai.utils import ensure_hf_login

DEFAULT_MODEL = "Qwen/Qwen2.5-0.5B-Instruct"


def _get_settings():
    return frappe.get_single("Frappe AI Settings")


@lru_cache(maxsize=1)
def _load_pipeline(model_name: str):
    ensure_hf_login()
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name, torch_dtype=torch.float32, device_map="cpu"
    )
    return pipeline("text-generation", model=model, tokenizer=tokenizer)


def _get_pipeline():
    settings = _get_settings()
    model_name = settings.llm_model_name or DEFAULT_MODEL
    return _load_pipeline(model_name)


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


def generate_response(system_prompt: str, context_chunks: List[str], user_query: str) -> str:
    settings = _get_settings()
    max_new_tokens = settings.max_new_tokens or 256

    context_block = (
        "\n".join(f"- {chunk}" for chunk in context_chunks)
        if context_chunks
        else "(No specific knowledge base entries were found for this query -- rely on the "
        "DocTypes named in your system prompt and general ERPNext knowledge instead.)"
    )

    messages = [
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

    generator = _get_pipeline()
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

"""
Uploads the locally-cached GGUF model file to your own Hugging Face
repo -- a mirror/backup, NOT a new or fine-tuned model. This app does
not train or modify the LLM's weights at all; it only downloads Qwen's
own pre-quantized GGUF and uses it as-is for RAG-grounded generation.
The uploaded repo is clearly labeled as a mirror with credit to the
original model, so it's not mistaken for original work.

Requires a Hugging Face token with WRITE access (the read-only token
used for downloads elsewhere in this app is NOT enough for uploads).
Get one at https://huggingface.co/settings/tokens -- set the role to
"Write", then either:
  - paste it into Frappe AI Settings > Hugging Face Token (same field
    used for downloads -- a Write token also works for reads), or
  - export HF_TOKEN before running this command.

Usage:
    # uploads to <your-hf-username>/qwen2.5-0.5b-instruct-gguf-mirror
    bench --site <your-site> execute frappe_ai.setup.upload_gguf_to_hf.run

    # or specify your own repo name
    bench --site <your-site> execute frappe_ai.setup.upload_gguf_to_hf.run \
        --kwargs '{"repo_id": "your-username/your-repo-name"}'
"""

import os

import frappe

from frappe_ai.llm.generator import gguf_model_path, DEFAULT_GGUF_REPO
from frappe_ai.utils import get_hf_token

MODEL_CARD_TEMPLATE = """---
license: apache-2.0
base_model: {source_repo}
tags:
  - gguf
  - llama-cpp
  - mirror
---

# {repo_name} (GGUF mirror)

**This is an unmodified mirror of [`{source_repo}`](https://huggingface.co/{source_repo}).**
No fine-tuning, training, or weight changes were made -- this repo exists
purely as a personal backup/mirror of the original quantized GGUF file.

All credit for the underlying model goes to the original authors at
[`{source_repo}`](https://huggingface.co/{source_repo}). Please refer to
their repo for the model card, license terms, and intended use.

## File

- `{filename}` -- GGUF quantized weights, unchanged from the source repo.

## Usage

```python
from llama_cpp import Llama

llm = Llama(model_path="{filename}", n_ctx=2048, n_threads=4, chat_format="chatml")
```
"""


def run(repo_id: str = None):
    from huggingface_hub import HfApi, create_repo

    token = get_hf_token()
    if not token:
        frappe.throw(
            "Uploading requires a Hugging Face token with WRITE access. "
            "Get one at https://huggingface.co/settings/tokens (role: Write), "
            "then set it in Frappe AI Settings > Hugging Face Token, or "
            "export HF_TOKEN before running this command."
        )

    settings = frappe.get_single("Frappe AI Settings")
    local_path = gguf_model_path()

    if not os.path.exists(local_path):
        frappe.throw(
            f"No GGUF file found at {local_path}. Run "
            "bench --site [your-site-name] execute frappe_ai.setup.fetch_gguf_model.run "
            "first, then retry this upload."
        )

    api = HfApi(token=token)
    filename = os.path.basename(local_path)
    source_repo = settings.gguf_model_repo or DEFAULT_GGUF_REPO

    if not repo_id:
        username = api.whoami()["name"]
        repo_id = f"{username}/qwen2.5-0.5b-instruct-gguf-mirror"

    print(f"Creating (or reusing) repo: {repo_id}")
    create_repo(repo_id, token=token, exist_ok=True, repo_type="model")

    print(f"Uploading {filename} ({os.path.getsize(local_path) / 1e6:.0f} MB)...")
    api.upload_file(
        path_or_fileobj=local_path,
        path_in_repo=filename,
        repo_id=repo_id,
        repo_type="model",
    )

    print("Uploading model card (README.md) with attribution to the original model...")
    model_card = MODEL_CARD_TEMPLATE.format(
        source_repo=source_repo,
        repo_name=repo_id.split("/")[-1],
        filename=filename,
    )
    api.upload_file(
        path_or_fileobj=model_card.encode("utf-8"),
        path_in_repo="README.md",
        repo_id=repo_id,
        repo_type="model",
    )

    print(f"\nDone. View it at: https://huggingface.co/{repo_id}")

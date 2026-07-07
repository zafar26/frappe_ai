"""
Downloads Qwen's official pre-quantized GGUF model (or whatever repo/
filename is configured in Frappe AI Settings) into this site's private
files, ready for the GGUF (llama.cpp) backend to load.

This is the recommended path for the default Qwen2.5-0.5B model --
no cmake/build-essential/llama.cpp compilation needed, just a direct
download of a file the Qwen team already built and quantized.

If you want to convert a DIFFERENT model that has no pre-made GGUF
(e.g. a custom fine-tune), use scripts/convert_to_gguf.py instead, then
set "GGUF Model Path" in Frappe AI Settings to point at the output file
-- that bypasses this download step entirely.

Run once after installing Python dependencies:
    bench --site <your-site> execute frappe_ai.setup.fetch_gguf_model.run
"""

import os
import shutil

import frappe

from frappe_ai.utils import get_hf_token
from frappe_ai.llm.generator import DEFAULT_GGUF_REPO, DEFAULT_GGUF_FILENAME


def run():
    settings = frappe.get_single("Frappe AI Settings")

    if settings.gguf_model_path:
        print(
            f"GGUF Model Path is manually set to '{settings.gguf_model_path}' -- "
            "skipping auto-download. Clear that field in Frappe AI Settings if you "
            "want this script to manage the model file instead."
        )
        return

    repo_id = settings.gguf_model_repo or DEFAULT_GGUF_REPO
    filename = settings.gguf_model_filename or DEFAULT_GGUF_FILENAME

    dest_dir = frappe.get_site_path("private", "files", "frappe_ai", "models")
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, filename)

    if os.path.exists(dest_path):
        print(f"GGUF model already present at {dest_path}, skipping download.")
        return

    from huggingface_hub import hf_hub_download

    print(f"Downloading {filename} from {repo_id} ...")
    token = get_hf_token()
    local_path = hf_hub_download(repo_id=repo_id, filename=filename, token=token)

    shutil.copy(local_path, dest_path)
    print(f"GGUF model ready at {dest_path}")
    print(
        "Model Backend in Frappe AI Settings is already set to 'GGUF (llama.cpp)' "
        "by default -- you're ready to chat."
    )

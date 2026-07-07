"""
Optional Hugging Face token handling.

Without a token, Hugging Face Hub downloads work fine but are
rate-limited and slower, and print a warning like:

    "You are sending unauthenticated requests to the HF Hub. Please
    set a HF_TOKEN to enable higher rate limits and faster downloads"

Setting a token (free, from https://huggingface.co/settings/tokens)
removes that warning and speeds up model downloads. Fully optional --
everything works without one, just slower on first download.

Token is read from, in priority order:
  1. Frappe AI Settings > Hugging Face Token (Desk UI, encrypted at rest)
  2. HF_TOKEN environment variable
"""

import os

import frappe

_login_attempted = False


def get_hf_token():
    token = None
    try:
        settings = frappe.get_single("Frappe AI Settings")
        if settings.hf_token:
            token = settings.get_password("hf_token")
    except Exception:
        token = None

    if not token:
        token = os.environ.get("HF_TOKEN")

    return token or None


def ensure_hf_login():
    """
    Log in to Hugging Face Hub once per process if a token is available,
    so all downstream `transformers`/`sentence-transformers` downloads
    use it automatically without needing to pass it into every call.
    """
    global _login_attempted
    if _login_attempted:
        return
    _login_attempted = True

    token = get_hf_token()
    if not token:
        return

    try:
        from huggingface_hub import login

        login(token=token, add_to_git_credential=False)
    except Exception:
        frappe.log_error(
            title="Frappe AI: Hugging Face login failed",
            message=frappe.get_traceback(),
        )

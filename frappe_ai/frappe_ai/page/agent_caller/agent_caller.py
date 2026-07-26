"""
Natural-language -> Frappe document creation, via a local GGUF model
fine-tuned for function calling (e.g. LFM2.5-1.2B-Nova-Function-Calling).

Both the available functions and the system prompt are configured from
the Desk, not hardcoded here:
  - Functions: `Agent Function` doctype (name, description, parameter
    schema, target DocType, and a Script written directly in the Desk).
  - System prompt: `Frappe AI Settings > Agent Caller System Prompt`
    (falls back to DEFAULT_SYSTEM_PROMPT_TEMPLATE if left blank). The
    template must contain the literal token {{FUNCTIONS}}, which gets
    replaced with the live JSON description of all enabled functions.

A function's Script runs sandboxed via frappe.utils.safe_exec -- the same
mechanism Frappe's own Server Script doctype uses. This intentionally
avoids a dotted Python import path (frappe.get_attr) as the dispatch
mechanism: that requires a matching file to exist at an exact location in
the codebase, which is a recurring source of mismatch bugs, and it means
every new function needs a code deploy. A Desk-authored script needs
neither.

Whitelisted from the Agent Caller Desk page (page/agent_caller/agent_caller.js) as:
    frappe_ai.agent_caller.plan
    frappe_ai.agent_caller.run

Two-step flow, mirroring the confirm-before-write pattern used by write
tools in Frappe Flow: `plan()` only asks the model to propose a function
call and returns it for review -- nothing is written to the database.
`run()` executes the function's script, and is only ever called after the
user has reviewed (and can edit) the proposal in the page. A script can
itself decline to create anything and instead propose a "next_action"
(e.g. "the Customer doesn't exist yet, create it first") -- see
fixtures/agent_function.json for a worked example. That next step is still
surfaced to the user for approval, not auto-run.
"""

import json
import os
import re
from functools import lru_cache

import frappe
from frappe.utils.safe_exec import get_safe_globals, safe_exec

DEFAULT_GGUF_FILENAME = "LFM2.5-1.2B-Nova-Function-Calling.Q2_K.gguf"

DEFAULT_SYSTEM_PROMPT_TEMPLATE = """You are a function-calling assistant for a Frappe/ERPNext system.

Available functions:
{{FUNCTIONS}}

Notes:
- Each item in "items" must be an object with "item_name" and "qty" (an
  integer). The user may say "quantity" or "qty" in plain English -- both
  map to the "qty" field.
- The function name goes in the "name" field, and its arguments go in the
  "arguments" field. Every required argument must be present.

When the user's request matches one of the functions above, respond with
ONLY a single JSON object, for example:
{"name": "create_sales_invoice", "arguments": {"customer": "Jane", "items": [{"item_name": "Keyboard", "qty": 3}], "due_date": "2026-08-01"}}

Do not use Python list / tool_call_start syntax. Do not include any other
text, explanation, or markdown formatting -- JSON only."""


# ---------------------------------------------------------------------------
# Functions, loaded from the "Agent Function" doctype (editable in the Desk)
# ---------------------------------------------------------------------------


def _get_functions() -> dict:
    """Enabled functions, keyed by function_name. Cached in-process,
    invalidated by AgentFunction.on_update/on_trash (see agent_function.py)."""
    cached = frappe.cache().get_value("frappe_ai:agent_functions")
    if cached:
        return cached

    rows = frappe.get_all(
        "Agent Function",
        filters={"enabled": 1},
        fields=["function_name", "description", "parameters", "target_doctype", "script"],
    )
    functions = {}
    for row in rows:
        try:
            parameters = json.loads(row["parameters"])
        except (json.JSONDecodeError, TypeError):
            # A malformed record shouldn't take down the whole agent -- skip
            # it and let the admin notice/fix it in the Desk.
            frappe.log_error(
                title="Frappe AI: bad Agent Function parameters",
                message=f"{row['function_name']}: {row['parameters']}",
            )
            continue
        functions[row["function_name"]] = {
            "description": row["description"],
            "parameters": parameters,
            "target_doctype": row["target_doctype"],
            "script": row["script"],
        }

    frappe.cache().set_value("frappe_ai:agent_functions", functions)
    return functions


# ---------------------------------------------------------------------------
# Model loading
# ---------------------------------------------------------------------------


def _settings():
    return frappe.get_single("Frappe AI Settings")


def _model_path() -> str:
    settings = _settings()
    path = getattr(settings, "agent_caller_gguf_path", None)
    if path:
        return path
    return os.path.join(
        frappe.get_site_path("private", "files", "frappe_ai", "models"),
        DEFAULT_GGUF_FILENAME,
    )


@lru_cache(maxsize=1)
def _load_llm(model_path: str, n_ctx: int):
    from llama_cpp import Llama

    # chat_format=None lets llama-cpp-python read the ChatML template
    # embedded in the GGUF's own metadata (LFM2.5 ships one), instead of
    # relying on a hand-built prompt string that the model was never
    # fine-tuned on.
    return Llama(model_path=model_path, n_ctx=n_ctx, chat_format=None, verbose=False)


def _get_llm():
    path = _model_path()
    if not os.path.exists(path):
        frappe.throw(
            f"Agent Caller GGUF model not found at {path}. Download "
            "LFM2.5-1.2B-Nova-Function-Calling (or a higher-precision quant "
            "than Q2_K if you have the RAM), and either place it at that path "
            "or set Frappe AI Settings > Agent Caller GGUF Path."
        )
    settings = _settings()
    return _load_llm(path, settings.gguf_n_ctx or 4096)


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def _system_prompt() -> str:
    settings = _settings()
    template = getattr(settings, "agent_caller_system_prompt", None) or DEFAULT_SYSTEM_PROMPT_TEMPLATE

    if "{{FUNCTIONS}}" not in template:
        frappe.throw(
            "Frappe AI Settings > Agent Caller System Prompt must contain the "
            "literal token {{FUNCTIONS}} somewhere, so the live function list "
            "can be inserted."
        )

    functions_for_prompt = {
        name: {"description": f["description"], "parameters": f["parameters"]}
        for name, f in _get_functions().items()
    }
    # A plain string replace (not .format()) on purpose: the template and the
    # functions JSON both contain literal { } characters that .format() would
    # try to interpret as format fields.
    return template.replace("{{FUNCTIONS}}", json.dumps(functions_for_prompt, indent=2))


def _extract_json(text: str) -> str:
    """Fallback for models that still wrap JSON in ```json fences or add stray text."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        return fenced.group(1)
    brace = re.search(r"\{.*\}", text, re.DOTALL)
    if brace:
        return brace.group(0)
    return text


# ---------------------------------------------------------------------------
# Whitelisted API
# ---------------------------------------------------------------------------


@frappe.whitelist()
def plan(query: str):
    """Turn a natural-language request into a proposed function call. Writes nothing."""
    if not query or not query.strip():
        frappe.throw("Please describe what you want to do.")

    functions = _get_functions()
    if not functions:
        frappe.throw(
            "No enabled Agent Function records exist yet. Add at least one "
            "under Agent Function in the Desk."
        )

    llm = _get_llm()
    output = llm.create_chat_completion(
        messages=[
            {"role": "system", "content": _system_prompt()},
            {"role": "user", "content": query},
        ],
        max_tokens=512,
        temperature=0.1,
        response_format={"type": "json_object"},
    )
    raw_text = output["choices"][0]["message"]["content"].strip()
    frappe.logger("frappe_ai.agent_caller").debug(f"raw model output: {raw_text}")

    try:
        fn_call = json.loads(_extract_json(raw_text))
        fn_name = fn_call["name"]
        args = fn_call.get("arguments", {})
    except Exception as e:
        frappe.throw(
            f"Could not parse a function call from the model's response: {e}"
            f"<br><br>Raw output:<br><code>{frappe.utils.escape_html(raw_text)}</code>"
        )

    if fn_name not in functions:
        frappe.throw(f"Model proposed an unknown or disabled function: {fn_name}")

    return {"name": fn_name, "arguments": args, "raw": raw_text}


@frappe.whitelist()
def run(name: str, arguments):
    """Run a function's Desk-authored script. Only call this after the user
    has reviewed (and can edit) the proposal in the page.

    The script is expected to set a local variable `result`, a dict with at
    least a "created" boolean. On a soft failure it may instead include a
    "next_action" (and optionally "then") describing a follow-up step for
    the user to review -- see fixtures/agent_function.json for an example
    (creating a missing Customer before retrying the original request)."""
    if isinstance(arguments, str):
        arguments = json.loads(arguments)

    functions = _get_functions()
    function = functions.get(name)
    if function is None:
        frappe.throw(f"Unknown or disabled function: {name}")

    doctype = function["target_doctype"]
    if not frappe.has_permission(doctype, "create"):
        frappe.throw(f"You don't have permission to create {doctype}.")

    _locals = {"args": arguments, "result": None}
    safe_exec(
        function["script"],
        _globals=get_safe_globals(),
        _locals=_locals,
        script_filename=f"Agent Function: {name}",
    )

    result = _locals.get("result")
    if not isinstance(result, dict):
        frappe.throw(
            f"The script for '{name}' did not set a `result` dict variable. "
            "Fix the script under Agent Function in the Desk."
        )
    return result

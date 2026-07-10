"""
A hand-rolled ReAct-style agent loop: the LLM decides, step by step,
whether to call a read-only tool and reason over the real result before
giving a final answer -- instead of always answering from static RAG
context alone.

Deliberately NOT built on a framework (LangGraph/CrewAI) so the
mechanics stay visible: Thought -> Action -> Observation -> repeat
until Final Answer, or until MAX_STEPS is hit. This is the reference
"agentic" pattern for Frappe AI -- currently wired up only for the
"accounts" agent (see tools/accounts_tools.py).

To extend this to another agent:
  1. Create tools/<agent>_tools.py with the same TOOL_REGISTRY /
     TOOL_DESCRIPTIONS shape as accounts_tools.py.
  2. Register it in TOOL_REGISTRIES_BY_AGENT below.
  3. Set enable_tools=1 on that AI Agent record.
  4. Add a run_agentic_<agent>() wrapper below (or generalize
     run_agentic_accounts into a single run_agentic(agent_key, ...)
     once more than one agent uses this -- kept agent-specific for now
     since this is a reference implementation, not yet a generalized
     framework).

Note on model size: this relies on the LLM reliably following the
ACTION: / FINAL ANSWER: text format. Small models (e.g. the default
Qwen2.5-0.5B) are noticeably less reliable at this than larger ones --
if you see it frequently skipping tool calls it should make, or
malformed ACTION lines, consider switching to a bigger GGUF (e.g.
Qwen2.5-1.5B or 3B-Instruct-GGUF) via Frappe AI Settings, at least for
testing this feature.
"""

import ast
import json
import re

from frappe_ai.llm.generator import _complete_chat, PRECISION_INSTRUCTIONS
from frappe_ai.tools.accounts_tools import (
    TOOL_REGISTRY as ACCOUNTS_TOOLS,
    TOOL_DESCRIPTIONS as ACCOUNTS_TOOL_DESCRIPTIONS,
)

TOOL_REGISTRIES_BY_AGENT = {
    "Accounts": (ACCOUNTS_TOOLS, ACCOUNTS_TOOL_DESCRIPTIONS),
}

MAX_STEPS = 4

ACTION_RE = re.compile(r"^\s*ACTION:\s*(\w+)\((.*)\)\s*$", re.DOTALL)
FINAL_ANSWER_RE = re.compile(r"^\s*FINAL ANSWER:\s*(.*)$", re.DOTALL)


def _parse_action(text: str):
    """
    Parses 'ACTION: tool_name(arg1="value", arg2=5)' safely -- uses
    ast.literal_eval (not eval) so only literal values can be passed,
    never arbitrary code execution.
    """
    match = ACTION_RE.match(text.strip())
    if not match:
        return None

    tool_name, args_str = match.groups()
    try:
        node = ast.parse(f"_({args_str})", mode="eval").body
        kwargs = {kw.arg: ast.literal_eval(kw.value) for kw in node.keywords}
        return tool_name, kwargs
    except Exception:
        return None


def _build_tool_system_prompt(base_system_prompt: str, tool_descriptions: str) -> str:
    return (
        f"{base_system_prompt}\n\n{PRECISION_INSTRUCTIONS}\n\n"
        "You also have access to tools that look up LIVE data from the ERPNext "
        "system. Use a tool whenever the question needs current, specific data "
        "(real invoice numbers, current outstanding balances, actual GL entries) "
        "rather than general knowledge.\n\n"
        f"Available tools:\n{tool_descriptions}\n\n"
        "To call a tool, respond with EXACTLY this on its own line and nothing else:\n"
        'ACTION: tool_name(arg1="value1", arg2=5)\n\n'
        "You will then be given the result as an OBSERVATION. Once you have "
        "enough information, respond with:\n"
        "FINAL ANSWER: <your answer>\n\n"
        "Only call a tool if the question truly needs live data -- if you can "
        "answer from the context already given, skip straight to FINAL ANSWER."
    )


def run_agentic_accounts(system_prompt: str, context_chunks, user_query: str, max_new_tokens: int = None) -> dict:
    """
    Runs the ReAct loop for the accounts agent. Returns a dict with the
    final answer plus a trace of tool calls made (tool name, args, and
    the observation returned), so the frontend can show what actually
    happened -- same transparency spirit as showing router confidence
    scores for the routing decision.
    """
    tool_registry, tool_descriptions = TOOL_REGISTRIES_BY_AGENT["Accounts"]

    context_block = (
        "\n".join(f"- {chunk}" for chunk in context_chunks)
        if context_chunks
        else "(No specific knowledge base entries were found for this query.)"
    )

    messages = [
        {"role": "system", "content": _build_tool_system_prompt(system_prompt, tool_descriptions)},
        {
            "role": "user",
            "content": f"Relevant knowledge base context:\n{context_block}\n\nUser question: {user_query}",
        },
    ]

    tool_trace = []

    for _step in range(MAX_STEPS):
        raw = _complete_chat(messages, max_new_tokens)

        final_match = FINAL_ANSWER_RE.match(raw.strip())
        if final_match:
            return {"answer": final_match.group(1).strip(), "tool_trace": tool_trace}

        action = _parse_action(raw)
        if action is None:
            # Model didn't follow the ACTION/FINAL ANSWER format -- treat its
            # raw output as the final answer rather than erroring or looping
            # on a format it's clearly not going to produce this turn.
            return {"answer": raw.strip(), "tool_trace": tool_trace}

        tool_name, kwargs = action
        messages.append({"role": "assistant", "content": raw.strip()})

        if tool_name not in tool_registry:
            observation = f"Error: unknown tool '{tool_name}'."
        else:
            try:
                result = tool_registry[tool_name](**kwargs)
                observation = json.dumps(result, default=str)
            except Exception as e:
                observation = f"Error calling {tool_name}: {e}"

        tool_trace.append({"tool": tool_name, "args": kwargs, "observation": observation})
        messages.append({"role": "user", "content": f"OBSERVATION: {observation}"})

    fallback_summary = "; ".join(f"{t['tool']} -> {t['observation']}" for t in tool_trace) or "no tool calls succeeded"
    return {
        "answer": (
            "I gathered some information but couldn't finish within the allowed "
            f"number of steps. Here's what I found: {fallback_summary}"
        ),
        "tool_trace": tool_trace,
    }

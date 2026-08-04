# Frappe AI — Agent Caller

A natural-language agent for Frappe/ERPNext: describe what you want in
plain English, a local GGUF model proposes a function call, you review
and approve it, and only then does it write to the database. If a step
needs something that doesn't exist yet (a Customer, an Item, ...), the
agent proposes creating that first as a follow-up step -- still reviewed
by you, unless you turn on auto-approve.

This is a standalone app containing just the Agent Caller system -- not
a chatbot/RAG app, just the function-calling agent.

## What's in it

- **Agent Function** (DocType): defines what the agent can do. Each
  record has a name, description, parameter schema, target DocType (for
  the permission check), and a **Script** -- real Python, written and
  edited directly in the Desk, run sandboxed via `frappe.utils.safe_exec`
  (the same mechanism Server Script uses). No code deploy needed to add
  a new function.
- **Agent Caller** (Page): the chat-like UI. Type a request, click Plan,
  review the proposed JSON (editable), Approve & Run. An "Auto-approve"
  checkbox runs the whole chain through to completion without asking at
  each step. An Activity panel shows live progress (via
  `frappe.publish_realtime`/socketio) while the model is thinking and
  while scripts run.
- **Frappe AI Settings** (single DocType): where the GGUF model path and
  the agent's system prompt live, both editable from the Desk.
- **30 built-in functions** (`fixtures/agent_function.json`), covering:
  - Selling: Sales Order, Sales Invoice, Quotation, Sales Return, Delivery Note
  - Buying: Purchase Order, Purchase Invoice, Purchase Receipt, Supplier Quotation, Purchase Return
  - Stock: Item, Material Request, Stock Entry, Stock Reconciliation
  - Accounts: Payment Entry, Journal Entry (these two **require real
    Chart of Accounts names** as arguments -- nothing is guessed, on purpose)
  - HR: Employee, Leave Application, Attendance
  - Manufacturing: BOM, Work Order
  - CRM (the separate **Frappe CRM** app, not ERPNext's core CRM):
    CRM Organization, CRM Lead, CRM Deal
  - Helpdesk (the separate **Frappe Helpdesk** app): HD Customer, HD Ticket
  - Shared: Customer, Supplier
  - Projects: Project, Task

Most of these assume your site has **ERPNext** installed (Customer,
Item, Sales Order, etc. are ERPNext doctypes, not core Frappe). The CRM
functions need the **Frappe CRM** app; the Helpdesk functions need the
**Frappe Helpdesk** app. If you don't have one of those installed, just
disable (or delete) the corresponding Agent Function records -- the rest
of the app works fine without them.

## Install

```bash
# from your bench directory
cp -r /path/to/extracted/frappe_ai apps/frappe_ai
bench pip install -e apps/frappe_ai
bench --site <your-site> install-app frappe_ai
bench build
bench --site <your-site> migrate
```

(If your bench doesn't pick up `pyproject.toml` automatically, `pip
install llama-cpp-python` directly into the bench's Python environment
works too.)

## Set up the model

1. Download a GGUF model fine-tuned for function calling -- e.g.
   `LFM2.5-1.2B-Nova-Function-Calling`. Q2_K is the smallest/fastest
   quant but noticeably weaker at reliably producing well-formed JSON;
   Q4_K_M is a safer choice if you have the RAM.
2. Either place it at
   `<site>/private/files/frappe_ai/models/LFM2.5-1.2B-Nova-Function-Calling.Q2_K.gguf`,
   or set **Frappe AI Settings > Agent Caller GGUF Path** to wherever you
   put it.

## Use it

- **Desk > Agent Caller** (`/app/agent-caller`): the main page.
- **Desk > Agent Function** (`/app/agent-function`): manage what the
  agent can do.
- **Desk > Frappe AI Settings**: model path, context size, system prompt.

There's no custom Workspace/sidebar shipped with this app (workspace
JSON is finicky to hand-write correctly without testing against a live
bench, and getting it wrong risks a broken Desk page) -- use the awesome
bar (search) to jump to any of the three, or build yourself a Workspace
shortcut in the Desk UI (drag-and-drop, takes a minute) if you want them
pinned in the sidebar.

## Writing your own function

Desk > Agent Function > New. The script gets one variable: `args` (the
model's proposed arguments, as a dict). It must set `result`, a dict with
at least `"created"`:

```python
customer = args.get("customer")

doc = frappe.get_doc({
    "doctype": "Delivery Note",
    "customer": customer,
    "items": [...],
})
doc.insert()
result = {"created": True, "name": doc.name, "doctype": "Delivery Note"}
```

To chain a follow-up step instead of failing outright (e.g. the Customer
doesn't exist yet):

```python
result = {
    "created": False,
    "error": "Customer does not exist.",
    "next_action": {"name": "create_customer", "arguments": {"customer_name": customer}},
    "then": {"name": "create_delivery_note", "arguments": args},  # retried after next_action succeeds
}
```

## Security note

`Agent Function.script` is a `System Manager`-only field, same trust
level as Server Script -- anyone who can edit it can run arbitrary Python
against your site. That's intentional (it's what makes functions
addable with no code deploy), so restrict access to Agent Function the
same way you'd restrict Server Script.

`Payment Entry` and `Journal Entry` deliberately refuse to run without
real account names passed in as arguments -- a plausible-looking but
wrong GL account name is how money silently ends up in the wrong ledger,
so nothing is defaulted there.

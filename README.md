# AI Dispatch — Multi-Agent RAG System for Frappe

A Frappe custom app: routes user queries to specialized agents mirroring
real ERPNext modules (Accounts, Buying, Selling, Stock, Manufacturing,
HR, Projects, Assets, Quality, CRM, Support — or any others you add)
using a neural network classifier, retrieves relevant context per agent
from an isolated ChromaDB collection, and generates grounded answers
with a locally hosted LLM. Fully manageable from the Frappe Desk UI —
add agents, knowledge base entries, and training examples without
touching code.

## What's inside

| Piece | How it's implemented |
|---|---|
| Query routing | Small PyTorch neural network (MLP) trained on `Router Training Example` records |
| Knowledge retrieval (RAG) | ChromaDB, one isolated collection per `AI Agent` |
| Answer generation | Local LLM via Hugging Face `transformers` (configurable in `AI Dispatch Settings`) |
| Agents | `AI Agent` DocType — add/edit/disable agents from the Desk, no code changes |
| Knowledge base | `AI Agent Document` DocType — auto-embeds into ChromaDB on save |
| Chat history | `AI Chat Message` DocType — every turn logged with routing confidence + retrieved context |
| Chatbot UI | Frappe www page at `/ai-dispatch`, uses your existing login session |

## Default agents (ship as fixtures, fully editable)

| Agent | Key | Covers |
|---|---|---|
| Accounts | `accounts` | Journal entries, payments, invoices, tax templates, GL reports |
| Buying | `buying` | Purchase orders, RFQs, supplier quotations, purchase receipts |
| Selling | `selling` | Sales orders, quotations, pricing rules, delivery notes |
| Stock | `stock` | Stock entries, warehouses, batch/serial tracking, reconciliation |
| Manufacturing | `manufacturing` | BOMs, work orders, job cards, production plans |
| HR | `hr` | Leave, attendance, payroll, appraisals, onboarding |
| Projects | `projects` | Tasks, timesheets, project billing, Gantt tracking |
| Assets | `assets` | Asset registration, depreciation, maintenance, disposal |
| Quality Management | `quality` | Quality inspections, non-conformance reports, procedures |
| CRM | `crm` | Leads, opportunities, pipeline, campaigns |
| Support / Tech Support | `support` | HD Tickets, SLAs, and general Frappe/ERPNext troubleshooting |

Each ships with ~25 router training examples (275 total) written in real
ERPNext terminology, and ~10 knowledge base documents describing that
module's actual workflows -- so the router and retrieval are grounded in
genuine ERPNext concepts, not generic placeholder text.

## Installation

```bash
# From your frappe-bench directory

# 1. Get the app (copy this folder into apps/, or push it to a git repo
#    and use bench get-app <repo-url>)
cp -r /path/to/ai_dispatch apps/ai_dispatch

# 2. Install Python dependencies into the bench's virtualenv
#    (these are heavy -- torch, transformers, chromadb -- expect this to
#    take a few minutes and download several hundred MB)
./env/bin/pip install -r apps/ai_dispatch/requirements.txt

# 3. Install the app on your site
bench --site <your-site> install-app ai_dispatch

# 4. Run migrations (creates the DocTypes, loads AI Agent + Router
#    Training Example fixtures automatically)
bench --site <your-site> migrate
```

## First-time setup (after install)

```bash
# 1. Warm up the models -- this is the ONE step that needs internet
#    access, and it's the local LLM setup, made explicit and visible
#    (with progress bars) instead of happening silently mid-chat.
bench --site <your-site> execute ai_dispatch.setup.warm_up_models.run

# 2. Seed sample ERPNext knowledge base documents for the 11 default
#    agents (Accounts, Buying, Selling, Stock, Manufacturing, HR,
#    Projects, Assets, Quality, CRM, Support)
bench --site <your-site> execute ai_dispatch.setup.seed_sample_data.run

# 3. Train the router classifier on the 275 ERPNext-flavored example
#    queries that ship as fixtures
bench --site <your-site> train-router
```

You should see output like:
```
Trained router on 275 examples.
Labels: ['accounts', 'assets', 'buying', 'crm', 'hr', 'manufacturing',
         'projects', 'quality', 'selling', 'stock', 'support']
Validation accuracy: 91.2%
```

## About the local LLM (important -- read this if you're not seeing one)

The app runs a genuinely **local** LLM -- `Qwen2.5-0.5B-Instruct` via
Hugging Face `transformers` (PyTorch backend, see `llm/generator.py`).
It is NOT a wrapper around OpenAI, Anthropic, or any other hosted API --
every response is generated on your own machine.

What can be confusing: the model's weights (~1GB) are **not** bundled in
this app's files -- no code repository ships gigabytes of model weights.
Instead, the model downloads once from Hugging Face automatically the
first time it's used, then is cached locally (usually under
`~/.cache/huggingface`) and reused on every request after that with zero
internet dependency. Running `warm_up_models.run` (step 1 above) makes
this download happen predictably during setup instead of surprising you
during your first chat message.

To use a different local model, change `llm_model_name` in
**AI Dispatch Settings** in the Desk to any `transformers`-compatible
causal LM, then re-run the warm-up step.

## Using it

Open **`https://<your-site>/ai-dispatch`** in your browser while logged
into your Frappe site. That's the chatbot UI — it shows the routing
confidence per agent live, and lets you expand the exact knowledge base
chunks used for each answer.

Everything else is managed from the Desk, same as any other Frappe data:

- **`AI Agent`** — add a new agent (e.g. "Billing"), give it a system
  prompt and a color, mark it enabled.
- **`Router Training Example`** — add 20-30+ example queries for your
  new agent so the router learns to recognize it, then retrain:
  `bench --site <your-site> train-router`
- **`AI Agent Document`** — add knowledge base entries for any agent.
  Saving a document automatically embeds it into that agent's ChromaDB
  collection (check the "Embedded" checkbox afterward to confirm).
- **`AI Dispatch Settings`** — change the LLM model, embedding model,
  how many chunks are retrieved (`top_k`), or max response length.
- **`AI Chat Message`** — full conversation log, filterable by session,
  user, agent, or role. Useful for reviewing routing accuracy over time.

## Adding a new agent (end-to-end example)

1. Desk → AI Agent → New: `agent_key = billing`, label "Billing", write
   a system prompt, save.
2. Desk → Router Training Example → add ~25 example billing questions,
   each linked to the `billing` agent.
3. Desk → AI Agent Document → add a handful of billing knowledge base
   entries linked to `billing`.
4. `bench --site <your-site> train-router`
5. Refresh `/ai-dispatch` — Billing now shows up as a routable agent.

## Notes on the neural network router

The router is a small feed-forward network (embedding → hidden layers
→ softmax over agent classes), not a large model — routing is a simple
classification task over a handful of categories, so a heavier
architecture isn't warranted. It's trained fresh every time you run
`train-router`, using whatever `Router Training Example` records exist
at that moment, so it always reflects your current set of agents.

## Notes on scaling this beyond a demo

- The local LLM (default: `Qwen2.5-0.5B-Instruct`) runs on CPU by
  default and is intentionally small. For production-quality answers,
  swap in a larger model with GPU inference, or point
  `llm/generator.py` at a hosted API instead.
- ChromaDB here runs in local persistent mode under the site's private
  files directory. For a multi-worker production deployment, consider
  ChromaDB's client/server mode instead.
- The router needs retraining any time agents or their training
  examples change — there's no online/incremental learning here by
  design, since retraining is fast (seconds) and keeps things simple
  and reproducible.

# AI Dispatch — Multi-Agent RAG System for Frappe

A Frappe custom app: routes user queries to specialized agents (Tech
Support, HR, Sales, or any you configure) using a neural network
classifier, retrieves relevant context per agent from an isolated
ChromaDB collection, and generates grounded answers with a locally
hosted LLM. Fully manageable from the Frappe Desk UI — add agents,
knowledge base entries, and training examples without touching code.

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
# 1. Seed sample knowledge base documents for the 3 default agents
#    (Tech Support, HR, Sales -- created automatically as AI Agent
#    fixtures during install). This step calls the embedding model,
#    so it needs internet access to Hugging Face on first run.
bench --site <your-site> execute ai_dispatch.setup.seed_sample_data.run

# 2. Train the router classifier (also needs the embedding model)
bench --site <your-site> train-router
```

You should see output like:
```
Trained router on 75 examples.
Labels: ['hr', 'sales', 'tech_support']
Validation accuracy: 93.33%
```

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

# Frappe AI — Multi-Agent RAG System for Frappe

A Frappe custom app: routes user queries to specialized agents mirroring
real ERPNext modules (Internal, Accounts, Buying, Selling, Stock,
Manufacturing, HR, Projects, CRM, Support)
using a neural network classifier, retrieves relevant context per agent
from an isolated ChromaDB collection, and generates grounded answers
with a locally hosted LLM. Fully manageable from the Frappe Desk UI —
add agents, knowledge base entries, and training examples without
touching code.

<img width="1212" height="687" alt="Screenshot 2026-07-07 at 4 36 21 PM" src="https://github.com/user-attachments/assets/fe9eee2f-2465-4767-9897-a577612c807e" />

<img width="750" height="687" alt="Screenshot 2026-07-07 at 4 35 49 PM" src="https://github.com/user-attachments/assets/d36013f5-9142-4c1d-a28c-cab6ce14e222" />

<img width="578" height="698" alt="Screenshot 2026-07-07 at 4 40 22 PM" src="https://github.com/user-attachments/assets/b44e838a-1552-4592-a441-096df5ed62e5" />

<img width="578" height="605" alt="Screenshot 2026-07-07 at 4 39 27 PM" src="https://github.com/user-attachments/assets/72ead45f-aa01-4d12-bda1-4898f17ab0ad" />

<img width="578" height="443" alt="Screenshot 2026-07-07 at 4 37 58 PM" src="https://github.com/user-attachments/assets/a997d10e-4bf5-44a9-9ab2-2d159c28fbbc" />


## What's inside

| Piece | How it's implemented |
|---|---|
| Query routing | Small PyTorch neural network (MLP) trained on `Router Training Example` records |
| Knowledge retrieval (RAG) | ChromaDB, one isolated collection per `AI Agent` |
| Answer generation | Local LLM via Hugging Face `transformers` (configurable in `Frappe AI Settings`) |
| Agents | `AI Agent` DocType — add/edit/disable agents from the Desk, no code changes |
| Knowledge base | `AI Agent Document` DocType — auto-embeds into ChromaDB on save |
| Chat history | `AI Chat Message` DocType — every turn logged with routing confidence + retrieved context |
| Chatbot UI | Frappe www page at `/frappe-ai`, uses your existing login session |

## Default agents (ship as fixtures, fully editable)

Matches ERPNext's actual module/doctype structure rather than generic
categories -- Assets is folded into Accounts (where it lives in real
ERPNext), Quality was dropped, and Internal was added for shared master
data used across every module.

| Agent | Key | Core DocTypes |
|---|---|---|
| Internal (General) | `internal` | Company, Warehouse, Item, Address, Contact, Email |
| Accounts | `accounts` | Payment Entry, Journal Entry, Account, Sales/Purchase Invoice, Asset, Asset Depreciation, Cost Center, GL/P&L/Balance Sheet reports |
| Buying (Procurement) | `buying` | Supplier, Material Request, RFQ, Supplier Quotation, Purchase Order, Purchase Receipt |
| Selling (Sales) | `selling` | Customer, Quotation, Sales Order, Pick List, Delivery Note |
| CRM | `crm` | Lead, Enquiry, Deal, Quotation |
| HR | `hr` | Employee, Leave Application, Salary Structure (+ Assignment), Shift Type (+ Assignment), Holiday |
| Manufacturing | `manufacturing` | BOM, Work Order, Job Card, Operation, Stock Entry (Manufacture, Material Transfer for Manufacturing) |
| Project | `projects` | Task, Timesheet |
| Inventory (Stock) | `stock` | Stock Entry (Material Transfer, Material Receipt, Material Issue), Stock Balance report |
| Support (Helpdesk) | `support` | HD Ticket, SLA |

Each ships with ~70 router training examples (700 total) generated
across varied phrasing templates in real ERPNext doctype terminology,
and ~10 knowledge base documents per agent describing that module's
actual workflows.

## Installation

```bash
# From your frappe-bench directory

# 1. Get the app
#    use 
bench get-app --branch gguf_llm_super_fast https://github.com/zafar26/frappe_ai.git

# NOTE on llama-cpp-python: prebuilt wheels exist for most common
# platforms (Linux x86_64, macOS, Windows), so the line above usually
# just works. If pip falls back to building from source and fails,
# install a C++ compiler first:
#   sudo apt install build-essential cmake -y   (Debian/Ubuntu)
# then re-run the pip install command above.

# 2. Install the app on your site
bench --site <your-site> install-app frappe_ai

# 3. Install Dependencies
bench setup requirements

# 4. Run migrations (creates the DocTypes, loads AI Agent + Router
#    Training Example fixtures automatically)
bench --site <your-site> migrate
```

## First-time setup (after install)

```bash
# 1. Warm up the models -- this is the ONE step that needs internet
#    access, and it's the local LLM setup, made explicit and visible
#    (with progress bars) instead of happening silently mid-chat.
bench --site <your-site> execute frappe_ai.setup.warm_up_models.run

# 2. Seed sample ERPNext knowledge base documents for the 10 default
#    agents (Internal, Accounts, Buying, Selling, Stock, Manufacturing,
#    HR, Projects, CRM, Support)
bench --site <your-site> execute frappe_ai.setup.seed_sample_data.run

# 3. Train the router classifier on the ~700 ERPNext-flavored example
#    queries that ship as fixtures (70 per agent, varied phrasing)
bench --site <your-site> train-router
```

You should see output like:
```
Trained router on 700 examples.
Labels: ['accounts', 'buying', 'crm', 'hr', 'internal', 'manufacturing',
         'projects', 'selling', 'stock', 'support']
Validation accuracy: ~90%+
```

## About the local LLM (important -- read this if you're not seeing one)

The app runs a genuinely **local** LLM -- it is NOT a wrapper around
OpenAI, Anthropic, or any other hosted API. Every response is generated
on your own machine. There are two backends, switchable in **Frappe AI
Settings > Model Backend**:

| Backend | Speed on CPU | RAM | Setup |
|---|---|---|---|
| **GGUF (llama.cpp)** — default | 3-5x faster | Much lower (~320MB model at q4_k_m) | Auto-downloads a pre-quantized file, no build tools needed |
| Transformers (PyTorch) | Slower | ~1GB+ | Downloads full-precision weights via `transformers` |

**GGUF is the recommended default.** It uses `llama-cpp-python` to run
Qwen2.5-0.5B-Instruct already quantized by the Qwen team
(`Qwen/Qwen2.5-0.5B-Instruct-GGUF`, filename `qwen2.5-0.5b-instruct-q4_k_m.gguf`
by default) -- no `cmake`/`build-essential`/cloning llama.cpp required,
just a direct file download. `warm_up_models.run` fetches it
automatically based on whatever's configured in Frappe AI Settings.

Quantization options, if you want to trade size/speed for quality
(set **GGUF Filename** in Frappe AI Settings to the matching file from
the same repo):

| Type | Size | RAM Needed | Quality |
|---|---|---|---|
| f16 | ~1GB | 2GB+ | Best |
| q8_0 | ~530MB | 1GB+ | Very Good |
| q4_k_m | ~320MB | 512MB+ | Good ✅ recommended |
| q2_k | ~200MB | 256MB+ | Acceptable |

What can be confusing either way: model weights (whether GGUF or full
Transformers) are **not** bundled in this app's files -- no code
repository ships hundreds of MB to GB of weights. They download once,
automatically, and are cached locally (GGUF under this site's private
files; Transformers under `~/.cache/huggingface`) -- reused on every
request after that with zero further internet dependency. Running
`warm_up_models.run` (step 1 above) makes this download happen
predictably during setup instead of surprising you mid-chat.

**Using a custom/fine-tuned model with no pre-made GGUF:** run the
standalone `scripts/convert_to_gguf.py` (requires `cmake`,
`build-essential`, and cloning llama.cpp -- see the script's docstring),
then set **GGUF Model Path** in Frappe AI Settings to the resulting
`.gguf` file. This bypasses the auto-download entirely.

To switch back to the Transformers backend (e.g. to A-B compare answer
quality), set **Model Backend = Transformers (PyTorch)** and
**Local LLM Model** to any `transformers`-compatible causal LM, then
re-run the warm-up step.

## Optional: HF_TOKEN (removes the rate-limit warning)

Without a token, model downloads still work fine, but you'll see this
in your logs:

```
Warning: You are sending unauthenticated requests to the HF Hub.
Please set a HF_TOKEN to enable higher rate limits and faster downloads
```

To remove it and get faster/higher-rate-limit downloads, get a free
**Read**-access token from
[huggingface.co/settings/tokens](https://huggingface.co/settings/tokens),
then set it either:

- **In the Desk (recommended):** Frappe AI Settings → Hugging Face
  Token field (stored encrypted, same as any Frappe Password field), or
- **As an environment variable** before running bench commands:
  ```bash
  export HF_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
  bench --site <your-site> execute frappe_ai.setup.warm_up_models.run
  ```

The Desk setting takes priority if both are set. This is entirely
optional — everything works without it, just slower on the first
download.

## Using it

Open **`https://<your-site>/frappe-ai`** in your browser while logged
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
- **`Frappe AI Settings`** — change the LLM model, embedding model,
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
5. Refresh `/frappe-ai` — Billing now shows up as a routable agent.

## Notes on the neural network router

The router is a small feed-forward network (embedding → hidden layers
→ softmax over agent classes), not a large model — routing is a simple
classification task over a handful of categories, so a heavier
architecture isn't warranted. It's trained fresh every time you run
`train-router`, using whatever `Router Training Example` records exist
at that moment, so it always reflects your current set of agents.

**Embedding model:** upgraded from `all-MiniLM-L6-v2` (384-dim) to
`all-mpnet-base-v2` (768-dim) -- a stronger sentence-transformers model
that gives noticeably better semantic separation between agents,
directly improving both routing accuracy and RAG retrieval quality.
Same architecture, just a better pretrained embedding. Change it back
in **Frappe AI Settings** if you'd rather trade some accuracy for a
smaller download / faster inference.

**Training data:** 700 examples (70 per agent), generated across ~20
distinct phrasing templates ("How do I create a...", "Where do I find
the...", "Steps to create...", etc.) combined with each agent's real
DocTypes. This gives the router genuine phrasing diversity to learn
from, rather than 25-ish near-identical examples per class.

## Notes on answer precision

The LLM prompt now includes explicit precision instructions: always
answer in terms of real Frappe/ERPNext DocTypes and fields, give exact
Desk navigation paths ("Module > DocType > New"), use precise DocType
names instead of vague paraphrases ("Purchase Order" not "the
purchasing screen"), and explicitly say when the knowledge base doesn't
cover something rather than drifting into generic, non-ERPNext filler.
Generation temperature was also lowered (0.7 → 0.3) for more
deterministic, factual answers instead of creative variation.

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

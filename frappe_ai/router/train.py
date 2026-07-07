"""
Trains the router classifier from Router Training Example records.

Callable two ways:
  1. bench console:  bench --site <site> execute frappe_ai.router.train.train_router
  2. Whitelisted API: POST /api/method/frappe_ai.api.train_router (System Manager only)
"""

import frappe
import numpy as np
import torch
import torch.nn as nn
from sklearn.model_selection import train_test_split

from frappe_ai.rag.embeddings import embed_texts, EMBEDDING_DIM
from frappe_ai.router.classifier import RouterClassifier, save_model

EPOCHS = 60
LEARNING_RATE = 1e-3
MIN_EXAMPLES_PER_CLASS = 4  # below this, train/val split gets unreliable


def _load_training_data():
    agents = frappe.get_all("AI Agent", filters={"enabled": 1}, fields=["name", "agent_key"])
    if len(agents) < 2:
        frappe.throw("Need at least 2 enabled AI Agent records to train a router.")

    labels = sorted(a["agent_key"] for a in agents)

    texts, y = [], []
    for label in labels:
        examples = frappe.get_all(
            "Router Training Example",
            filters={"agent": label},
            pluck="query_text",
        )
        if len(examples) < MIN_EXAMPLES_PER_CLASS:
            frappe.throw(
                f"Agent '{label}' has only {len(examples)} training examples. "
                f"Add at least {MIN_EXAMPLES_PER_CLASS} Router Training Example "
                f"records for it before training."
            )
        for query in examples:
            texts.append(query)
            y.append(labels.index(label))

    return texts, np.array(y), labels


def train_router() -> dict:
    """Train and persist the router classifier. Returns a small report dict."""
    texts, y, labels = _load_training_data()

    X = embed_texts(texts)

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    X_train_t = torch.tensor(X_train, dtype=torch.float32)
    y_train_t = torch.tensor(y_train, dtype=torch.long)
    X_val_t = torch.tensor(X_val, dtype=torch.float32)
    y_val_t = torch.tensor(y_val, dtype=torch.long)

    model = RouterClassifier(input_dim=EMBEDDING_DIM, num_classes=len(labels))
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    criterion = nn.CrossEntropyLoss()

    final_val_acc = 0.0
    for epoch in range(1, EPOCHS + 1):
        model.train()
        optimizer.zero_grad()
        logits = model(X_train_t)
        loss = criterion(logits, y_train_t)
        loss.backward()
        optimizer.step()

        if epoch == EPOCHS:
            model.eval()
            with torch.no_grad():
                val_preds = model(X_val_t).argmax(dim=-1)
                final_val_acc = (val_preds == y_val_t).float().mean().item()

    save_model(model, labels)

    return {
        "labels": labels,
        "num_examples": len(texts),
        "final_val_accuracy": round(final_val_acc, 4),
    }

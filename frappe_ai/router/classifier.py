"""
Neural network (small feed-forward MLP) that routes a query to the
right AI Agent. Trained on Router Training Example records, which are
managed from the Frappe Desk UI rather than a static file -- so adding
a new agent + training examples + retraining is all doable without
touching code.
"""

import json
import os
from typing import Dict, List, Tuple

import frappe
import torch
import torch.nn as nn


class RouterClassifier(nn.Module):
    def __init__(self, input_dim: int = 768, hidden_dim: int = 64, num_classes: int = 3):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, num_classes),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x)


def _weights_dir() -> str:
    path = frappe.get_site_path("private", "files", "frappe_ai")
    os.makedirs(path, exist_ok=True)
    return path


def _weights_path() -> str:
    return os.path.join(_weights_dir(), "router_classifier.pt")


def _labels_path() -> str:
    return os.path.join(_weights_dir(), "router_labels.json")


def save_model(model: RouterClassifier, label_list: List[str],  input_dim: int) -> None:
    torch.save(model.state_dict(), _weights_path())
    with open(_labels_path(), "w") as f:
        # json.dump(label_list, f)
        json.dump({"labels": label_list, "input_dim": input_dim}, f)



def load_model() -> Tuple[RouterClassifier, List[str]]:
    weights_path, labels_path = _weights_path(), _labels_path()
    if not os.path.exists(weights_path) or not os.path.exists(labels_path):
        raise FileNotFoundError(
            "Router classifier not trained yet. Run bench command "
            "`bench --site <site> train-router` or call frappe_ai.api.train_router."
        )

    with open(labels_path, "r") as f:
        meta = json.load(f)

    # ✅ Handle both old format (list) and new format (dict)
    if isinstance(meta, list):
        label_list = meta
        input_dim = 768  # old default
    else:
        label_list = meta["labels"]
        input_dim = meta["input_dim"]

    # ✅ Build model with correct input_dim from saved metadata
    model = RouterClassifier(
        input_dim=input_dim,
        num_classes=len(label_list)
    )
    model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    model.eval()
    return model, label_list


def predict_label(model: RouterClassifier, label_list: List[str], embedding) -> Dict:
    with torch.no_grad():
        x = torch.tensor(embedding, dtype=torch.float32).unsqueeze(0)
        logits = model(x)
        probs = torch.softmax(logits, dim=-1).squeeze(0).tolist()

    scored = {label_list[i]: round(probs[i], 4) for i in range(len(label_list))}
    predicted = max(scored, key=scored.get)
    return {"predicted_agent": predicted, "confidence_scores": scored}

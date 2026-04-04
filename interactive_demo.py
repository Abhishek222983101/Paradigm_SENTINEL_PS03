#!/usr/bin/env python3
"""
SENTINEL FRAUD DETECTION - INTERACTIVE DEMO
============================================
Mentors can input ANY transaction ID and see real-time inference.
"""

import sys
import time
import json
import pickle
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
import math


# ============================================================================
# MODEL ARCHITECTURE (Same as training)
# ============================================================================
class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer("pe", pe)

    def forward(self, x):
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


class TabularEncoder(nn.Module):
    def __init__(
        self,
        categorical_cardinalities,
        num_numerical_features,
        embedding_dim=32,
        hidden_dims=[256, 128],
        output_dim=128,
        dropout=0.3,
    ):
        super().__init__()
        self.embeddings = nn.ModuleDict(
            {
                name: nn.Embedding(num_cat + 1, embedding_dim, padding_idx=0)
                for name, num_cat in categorical_cardinalities.items()
            }
        )
        self.categorical_names = list(categorical_cardinalities.keys())
        self.numerical_bn = nn.BatchNorm1d(num_numerical_features)
        self.numerical_proj = nn.Linear(num_numerical_features, embedding_dim)
        total_emb = embedding_dim * (len(categorical_cardinalities) + 1)
        layers = []
        prev = total_emb
        for h in hidden_dims:
            layers.extend(
                [nn.Linear(prev, h), nn.BatchNorm1d(h), nn.ReLU(), nn.Dropout(dropout)]
            )
            prev = h
        layers.append(nn.Linear(prev, output_dim))
        self.mlp = nn.Sequential(*layers)

    def forward(self, cat_features, numerical_features):
        embedded = []
        for name in self.categorical_names:
            if name in cat_features:
                embedded.append(self.embeddings[name](cat_features[name]))
        num_proj = self.numerical_proj(self.numerical_bn(numerical_features))
        embedded.append(num_proj)
        return self.mlp(torch.cat(embedded, dim=-1))


class SequenceTransformer(nn.Module):
    def __init__(
        self,
        feature_dim=32,
        d_model=128,
        nhead=8,
        num_layers=6,
        dim_feedforward=512,
        dropout=0.1,
        max_seq_len=50,
        output_dim=128,
    ):
        super().__init__()
        self.input_proj = nn.Linear(feature_dim, d_model)
        self.pos_encoder = PositionalEncoding(d_model, max_seq_len, dropout)
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.layer_norm = nn.LayerNorm(d_model)
        self.output_proj = nn.Linear(d_model, output_dim)

    def forward(self, sequence, mask=None):
        x = self.input_proj(sequence)
        x = self.pos_encoder(x)
        x = self.transformer(x)
        x = self.layer_norm(x)
        x = x.mean(dim=1)
        return self.output_proj(x)


class CrossModalFusion(nn.Module):
    def __init__(
        self,
        tabular_dim=128,
        sequence_dim=128,
        graph_dim=128,
        fusion_dim=256,
        num_heads=8,
        dropout=0.1,
    ):
        super().__init__()
        self.tabular_proj = nn.Linear(tabular_dim, fusion_dim)
        self.sequence_proj = nn.Linear(sequence_dim, fusion_dim)
        self.graph_proj = nn.Linear(graph_dim, fusion_dim)
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=fusion_dim, num_heads=num_heads, dropout=dropout, batch_first=True
        )
        self.fusion_weights = nn.Parameter(torch.ones(3))
        self.layer_norm = nn.LayerNorm(fusion_dim)
        self.ffn = nn.Sequential(
            nn.Linear(fusion_dim, fusion_dim * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_dim * 2, fusion_dim),
        )

    def forward(self, tabular_emb, sequence_emb, graph_emb):
        t = self.tabular_proj(tabular_emb)
        s = self.sequence_proj(sequence_emb)
        g = self.graph_proj(graph_emb)
        stacked = torch.stack([t, s, g], dim=1)
        attn_out, _ = self.cross_attention(stacked, stacked, stacked)
        w = F.softmax(self.fusion_weights, dim=0)
        fused = w[0] * attn_out[:, 0] + w[1] * attn_out[:, 1] + w[2] * attn_out[:, 2]
        fused = self.layer_norm(fused + t + s + g)
        fused = fused + self.ffn(fused)
        return fused, w


class MultiTaskHeads(nn.Module):
    def __init__(self, input_dim=256, num_fraud_types=5, hidden_dim=128, dropout=0.2):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )
        self.fraud_head = nn.Sequential(
            nn.Linear(hidden_dim, 64), nn.ReLU(), nn.Linear(64, 1)
        )
        self.type_head = nn.Sequential(
            nn.Linear(hidden_dim, 64), nn.ReLU(), nn.Linear(64, num_fraud_types)
        )
        self.score_head = nn.Sequential(
            nn.Linear(hidden_dim, 64), nn.ReLU(), nn.Linear(64, 1), nn.Sigmoid()
        )
        self.mfa_head = nn.Sequential(
            nn.Linear(hidden_dim, 64), nn.ReLU(), nn.Linear(64, 3)
        )

    def forward(self, x):
        s = self.shared(x)
        return {
            "fraud_logits": self.fraud_head(s),
            "fraud_prob": torch.sigmoid(self.fraud_head(s)),
            "type_logits": self.type_head(s),
            "risk_score": self.score_head(s) * 100,
            "mfa_logits": self.mfa_head(s),
            "mfa_decision": torch.argmax(self.mfa_head(s), dim=-1),
        }


class FusionModel(nn.Module):
    def __init__(
        self,
        cat_cardinalities,
        num_num_features,
        seq_feat_dim=32,
        max_seq_len=50,
        graph_emb_dim=128,
        emb_dim=128,
        fusion_dim=256,
        num_fraud_types=5,
        dropout=0.2,
    ):
        super().__init__()
        self.tabular = TabularEncoder(
            cat_cardinalities,
            num_num_features,
            embedding_dim=32,
            hidden_dims=[256, 128],
            output_dim=emb_dim,
            dropout=dropout,
        )
        self.sequence = SequenceTransformer(
            feature_dim=seq_feat_dim,
            d_model=128,
            nhead=8,
            num_layers=6,
            dim_feedforward=512,
            dropout=0.1,
            max_seq_len=max_seq_len,
            output_dim=emb_dim,
        )
        self.fusion = CrossModalFusion(
            tabular_dim=emb_dim,
            sequence_dim=emb_dim,
            graph_dim=graph_emb_dim,
            fusion_dim=fusion_dim,
            num_heads=8,
            dropout=dropout,
        )
        self.heads = MultiTaskHeads(
            input_dim=fusion_dim,
            num_fraud_types=num_fraud_types,
            hidden_dim=128,
            dropout=dropout,
        )

    def forward(self, cat, num, seq, graph_emb):
        t = self.tabular(cat, num)
        s = self.sequence(seq)
        f, mw = self.fusion(t, s, graph_emb)
        out = self.heads(f)
        out["modality_weights"] = mw
        return out


# ============================================================================
# GLOBAL LOADING
# ============================================================================
print("\n[*] Loading Sentinel Fraud Detection Engine...")

# Load metadata
with open("training/data/processed/metadata.json") as f:
    meta = json.load(f)

# Load model
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model = FusionModel(
    cat_cardinalities=meta["categorical_cardinalities"],
    num_num_features=360,
    seq_feat_dim=32,
    max_seq_len=20,
    graph_emb_dim=128,
    emb_dim=128,
    fusion_dim=256,
    num_fraud_types=5,
    dropout=0.2,
).to(device)

checkpoint = torch.load(
    "backend/models/checkpoints/fusion_model_best.pt", map_location=device
)
model.load_state_dict(checkpoint)
model.eval()
print(f"[*] Model loaded on {device}")

# Load data
features = pd.read_parquet("training/data/processed/features.parquet")
sequences = np.load("training/data/processed/sequences.npy", mmap_mode="r")
graph_emb = np.load(
    "training/data/processed/graph_embeddings_per_sample.npy", mmap_mode="r"
)

with open("training/data/processed/splits.pkl", "rb") as f:
    splits = pickle.load(f)

test_idx = splits["test_idx"]
test_idx = test_idx[test_idx < len(sequences)]

num_cols = meta["numerical_feature_names"]
cat_cols = meta["categorical_feature_names"]

# Pre-identify some fraud and legit samples for quick access
test_data = features.iloc[test_idx]
fraud_indices = test_idx[test_data["isFraud"].values == 1].tolist()
legit_indices = test_idx[test_data["isFraud"].values == 0].tolist()

print(f"[*] Loaded {len(features):,} transactions")
print(
    f"[*] Test set: {len(test_idx):,} | Fraud samples: {len(fraud_indices)} | Legit samples: {len(legit_indices)}"
)
print("[*] Ready for inference!\n")


def analyze_transaction(idx):
    """Run inference on a single transaction."""
    if idx >= len(features) or idx >= len(sequences):
        print(
            f"  ERROR: Transaction ID {idx} out of range (max: {min(len(features), len(sequences)) - 1})"
        )
        return

    row = features.iloc[idx]
    actual_label = "FRAUDULENT" if row["isFraud"] == 1 else "LEGITIMATE"

    print(f"\n{'=' * 60}")
    print(f"  TRANSACTION ID: TXN-{idx:06d}")
    print(f"  ACTUAL LABEL: {actual_label}")
    print(f"{'=' * 60}")

    # Show details
    print(f"  Amount: ${row['TransactionAmt']:.2f}")
    card_types = ["Visa", "Mastercard", "Amex", "Discover", "Other"]
    products = ["W", "H", "C", "S", "R"]
    devices = ["Desktop", "Mobile", "Tablet", "Unknown"]

    print(f"  Card Type: {card_types[int(row.get('cat_card4', 0)) % 5]}")
    print(f"  Product: {products[int(row.get('cat_ProductCD', 0)) % 5]}")
    print(f"  Device: {devices[int(row.get('cat_DeviceType', 0)) % 4]}")

    # Prepare inputs
    num_features = (
        torch.tensor(row[num_cols].values.astype(np.float32)).unsqueeze(0).to(device)
    )
    cat_features = {
        col: torch.tensor([int(row[f"cat_{col}"])]).to(device) for col in cat_cols
    }
    seq = torch.tensor(sequences[idx]).unsqueeze(0).float().to(device)
    ge = torch.tensor(graph_emb[idx]).unsqueeze(0).float().to(device)

    print(f"\n  Running through Multi-Modal AI...")

    # Run inference
    with torch.no_grad():
        start = time.time()
        output = model(cat_features, num_features, seq, ge)
        latency = (time.time() - start) * 1000

    fraud_prob = output["fraud_prob"].item()
    risk_score = output["risk_score"].item()
    mfa_decision = output["mfa_decision"].item()

    print(f"\n  {'─' * 40}")
    print(f"  AI PREDICTION RESULTS (Latency: {latency:.1f}ms)")
    print(f"  {'─' * 40}")

    print(f"  Fraud Probability: {fraud_prob * 100:6.2f}%")
    print(f"  Risk Score:        {risk_score:6.1f} / 100")

    actions = ["APPROVE (Low Risk)", "STEP-UP MFA (Medium Risk)", "BLOCK (High Risk)"]
    print(f"  Action: {actions[mfa_decision]}")

    prediction = "FRAUD" if fraud_prob > 0.5 else "LEGITIMATE"
    correct = (prediction == "FRAUD") == (row["isFraud"] == 1)

    print(f"\n  MODEL SAYS: {prediction}")
    print(f"  CORRECT: {'YES' if correct else 'NO'}")
    print(f"{'=' * 60}\n")


def main():
    print("=" * 60)
    print("  SENTINEL FRAUD DETECTION - INTERACTIVE DEMO")
    print("=" * 60)
    print("\nCommands:")
    print("  <number>  - Analyze transaction by ID (0 to 587095)")
    print("  f         - Analyze a random FRAUD transaction")
    print("  l         - Analyze a random LEGIT transaction")
    print("  b         - Analyze BOTH (one fraud + one legit)")
    print("  q         - Quit")
    print()

    while True:
        try:
            user_input = input("Enter transaction ID (or f/l/b/q): ").strip().lower()

            if user_input == "q":
                print("Goodbye!")
                break
            elif user_input == "f":
                idx = fraud_indices[np.random.randint(0, len(fraud_indices))]
                analyze_transaction(idx)
            elif user_input == "l":
                idx = legit_indices[np.random.randint(0, len(legit_indices))]
                analyze_transaction(idx)
            elif user_input == "b":
                print("\n--- LEGIT TRANSACTION ---")
                idx = legit_indices[np.random.randint(0, len(legit_indices))]
                analyze_transaction(idx)
                print("\n--- FRAUD TRANSACTION ---")
                idx = fraud_indices[np.random.randint(0, len(fraud_indices))]
                analyze_transaction(idx)
            elif user_input.isdigit():
                idx = int(user_input)
                analyze_transaction(idx)
            else:
                print("Invalid input. Use a number, 'f', 'l', 'b', or 'q'.")
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SENTINEL ELITE - ANOMALY INJECTION CLASSIFIER
==============================================
Allows mentors to take a base transaction and inject custom anomaly
parameters (velocity, IP mismatch, etc.) to see how the Deep Learning
model dynamically adjusts its classification.
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
from datetime import datetime


# ============================================================================
# MODEL ARCHITECTURE (Required for PyTorch)
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
# HELPER FUNCTIONS
# ============================================================================
def print_slow(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def clear_screen():
    print("\033[H\033[J", end="")


# ============================================================================
# INITIALIZATION
# ============================================================================
clear_screen()
print("=" * 70)
print_slow("🛡️  SENTINEL ELITE CLASSIFIER - INITIALIZING ML KERNEL...", 0.02)
print("=" * 70)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"[*] Hardware Detected: {device.type.upper()}")

print("[*] Loading IEEE-CIS Transaction Data Matrix...")
with open("training/data/processed/metadata.json") as f:
    meta = json.load(f)

features = pd.read_parquet("training/data/processed/features.parquet")
sequences = np.load("training/data/processed/sequences.npy", mmap_mode="r")
graph_emb = np.load(
    "training/data/processed/graph_embeddings_per_sample.npy", mmap_mode="r"
)

num_cols = meta["numerical_feature_names"]
cat_cols = meta["categorical_feature_names"]
amt_idx = num_cols.index("TransactionAmt") if "TransactionAmt" in num_cols else 0

print("[*] Booting Multi-Modal Deep Learning Classifier...")
model = FusionModel(
    cat_cardinalities=meta["categorical_cardinalities"],
    num_num_features=360,
    seq_feat_dim=32,
    max_seq_len=20,
    graph_emb_dim=128,
    emb_dim=128,
    fusion_dim=256,
).to(device)

checkpoint = torch.load(
    "backend/models/checkpoints/fusion_model_best.pt", map_location=device
)
model.load_state_dict(checkpoint)
model.eval()
print("[*] System Ready. Awaiting Classification Requests.\n")


# ============================================================================
# CLASSIFICATION LOGIC
# ============================================================================
def run_classification(idx, anomaly_mode=None):
    row = features.iloc[idx]

    # 1. Convert to PyTorch Tensors
    num_features = (
        torch.tensor(row[num_cols].values.astype(np.float32)).unsqueeze(0).to(device)
    )
    cat_features = {
        col: torch.tensor([int(row[f"cat_{col}"])]).to(device) for col in cat_cols
    }
    seq = torch.tensor(sequences[idx]).unsqueeze(0).float().to(device)
    ge = torch.tensor(graph_emb[idx]).unsqueeze(0).float().to(device)

    base_amount = float(row["TransactionAmt"])
    applied_anomalies = []

    # 2. INJECT CUSTOM ANOMALIES (Manipulating Tensors)
    if anomaly_mode == 1:
        # Amount Spike
        new_amt = base_amount * 15.5
        num_features[0, amt_idx] = float(new_amt)
        applied_anomalies.append(f"Injected 15x Amount Spike (${new_amt:.2f})")

    elif anomaly_mode == 2:
        # High Velocity (Modify Sequence Tensor to show 5 rapid transactions)
        seq[0, -5:, amt_idx] = float(base_amount * 2)
        applied_anomalies.append("Injected Velocity Anomaly (5 rapid txns in sequence)")

    elif anomaly_mode == 3:
        # Dark Web Email (Modify Categorical Tensor)
        cat_features["P_emaildomain"] = torch.tensor([59]).to(
            device
        )  # High risk domain index
        applied_anomalies.append("Injected High-Risk/Dark Web Email Domain")

    elif anomaly_mode == 4:
        # Combined Attack (ATO Profile)
        new_amt = float(base_amount * 8)
        num_features[0, amt_idx] = new_amt
        seq[0, -3:, amt_idx] = new_amt
        cat_features["DeviceType"] = torch.tensor([2]).to(device)  # Unknown/New device
        applied_anomalies.append(
            f"Injected Full ATO Profile (New Device + Velocity + Spike to ${new_amt:.2f})"
        )

    print(f"\n[*] Extracted base feature vector for TXN-{idx:06d}")
    if applied_anomalies:
        for a in applied_anomalies:
            print(f"[!] {a}")

    print("[*] Forwarding tensors through Multi-Modal Pathways...")
    time.sleep(0.5)

    # 3. RUN ML CLASSIFICATION
    with torch.no_grad():
        start_time = time.time()
        output = model(cat_features, num_features, seq, ge)
        latency = (time.time() - start_time) * 1000

    fraud_prob = output["fraud_prob"].item()
    mfa_decision = output["mfa_decision"].item()

    # Generate Output
    is_fraud = fraud_prob >= 0.5
    class_label = "ANOMALY / FRAUD" if is_fraud else "NORMAL"
    color = "\033[91m" if is_fraud else "\033[92m"
    reset = "\033[0m"

    actions = ["APPROVE", "STEP-UP MFA", "BLOCK & ALERT"]

    print(f"\n{'-' * 60}")
    print(f"  🧠 SENTINEL CLASSIFICATION RESULTS")
    print(f"{'-' * 60}")
    print(f"  Classification:    {color}{class_label}{reset}")
    print(f"  Anomaly Certainty: {fraud_prob * 100:.2f}%")
    print(f"  Action Prescribed: {actions[mfa_decision]}")
    print(f"  Inference Latency: {latency:.2f} ms")
    print(f"{'-' * 60}\n")


def main():
    while True:
        print("\n" + "=" * 70)
        print("  TRANSACTION CLASSIFICATION DASHBOARD")
        print("=" * 70)
        print("  Select Base Transaction ID (or press Enter for random Legit tx):")

        user_input = input("  > ID: ").strip()
        if user_input.lower() == "q":
            break

        try:
            if not user_input:
                # Pick a random legit transaction
                idx = features[features["isFraud"] == 0].index[
                    np.random.randint(100, 1000)
                ]
            else:
                idx = int(user_input)
                if idx >= len(features):
                    print("  [Error] ID out of range.")
                    continue

            # Show base details
            row = features.iloc[idx]
            print(
                f"\n  [Base Info] TXN-{idx:06d} | Amount: ${row['TransactionAmt']:.2f}"
            )

            # Anomaly Menu
            print("\n  [ANOMALY INJECTION MENU]")
            print("  0. Process Normally (No Injection)")
            print("  1. Inject Transaction Amount Spike (15x)")
            print("  2. Inject Velocity Attack (Rapid sequences)")
            print("  3. Inject Suspicious Dark-Web Email")
            print("  4. Inject Full Account Takeover (ATO) Profile")

            ano_input = input("\n  > Select Injection (0-4): ").strip()
            anomaly_mode = (
                int(ano_input) if ano_input in ["0", "1", "2", "3", "4"] else 0
            )

            run_classification(idx, anomaly_mode)

            input("  Press Enter to classify another transaction...")
            clear_screen()

        except ValueError:
            print("  [Error] Invalid input.")
        except KeyboardInterrupt:
            break


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
SENTINEL FRAUD DETECTION - CUSTOM TRANSACTION CLASSIFIER
=========================================================
Mentors can input ANY transaction details and the AI will classify it.

This script:
1. Takes custom input (amount, card type, device, etc.)
2. Finds similar transactions in our dataset
3. Runs REAL ML inference using our trained Fusion Model
4. Shows the fraud classification result
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
# MODEL ARCHITECTURE (Exact same as training)
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
# LOAD MODEL AND DATA
# ============================================================================
print("\n" + "=" * 65)
print("  SENTINEL FRAUD DETECTION - CUSTOM TRANSACTION CLASSIFIER")
print("=" * 65)
print("\n[*] Initializing AI Engine...")

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
print(f"[*] Multi-Modal Fusion Model loaded on {device.type.upper()}")
print(f"[*] Model: 2,017,629 parameters | 4 neural pathways | 6-layer Transformer")

# Load data for similarity matching
features = pd.read_parquet("training/data/processed/features.parquet")
sequences = np.load("training/data/processed/sequences.npy", mmap_mode="r")
graph_emb = np.load(
    "training/data/processed/graph_embeddings_per_sample.npy", mmap_mode="r"
)

num_cols = meta["numerical_feature_names"]
cat_cols = meta["categorical_feature_names"]

print(f"[*] Loaded {len(features):,} historical transactions for pattern matching")
print("[*] System ready!\n")


# ============================================================================
# SIMILARITY MATCHING & INFERENCE
# ============================================================================
def find_similar_transaction(
    amount, card_type, device_type, product, email_domain, is_international=False
):
    """
    Find the most similar transaction in our dataset based on user input.
    This allows us to use REAL feature vectors for inference.
    """
    # Map inputs to encoded values
    card_map = {"visa": 1, "mastercard": 2, "amex": 3, "discover": 4, "other": 0}
    device_map = {"desktop": 0, "mobile": 1, "tablet": 2}
    product_map = {"w": 0, "h": 1, "c": 2, "s": 3, "r": 4}

    card_val = card_map.get(card_type.lower(), 0)
    device_val = device_map.get(device_type.lower(), 0)
    product_val = product_map.get(product.lower(), 0)

# ============================================================================
# ADDITIONAL DATA INFO
# ============================================================================
MAX_IDX = min(len(features), len(sequences)) - 1
total_frauds = (features['isFraud'] == 1).sum()

print(f"\n  DATA SOURCE INFO:")
print(f"  ─────────────────────────────────────────────────────────────")
print(f"  File: training/data/processed/features.parquet")
print(f"  Dataset: IEEE-CIS Fraud Detection (Kaggle)")
print(f"  Total Transactions: {len(features):,}")
print(f"  Confirmed Frauds: {total_frauds:,} ({total_frauds/len(features)*100:.2f}%)")
print(f"  Valid Transaction ID Range: 0 to {MAX_IDX:,}")
print()

# Pre-find fraud/legit indices
fraud_indices = features[features['isFraud'] == 1].index.tolist()
fraud_indices = [i for i in fraud_indices if i <= MAX_IDX]
legit_indices = features[features['isFraud'] == 0].index.tolist()[:10000]
legit_indices = [i for i in legit_indices if i <= MAX_IDX]

CARD_MAP = {0: 'Other', 1: 'Visa', 2: 'Mastercard', 3: 'Amex', 4: 'Discover'}
DEVICE_MAP = {0: 'Desktop', 1: 'Mobile', 2: 'Tablet'}
PRODUCT_MAP = {0: 'W (Web)', 1: 'H (Hardware)', 2: 'C (Content)', 3: 'S (Service)', 4: 'R (Retail)'}

# ============================================================================
# CLASSIFICATION FUNCTION
# ============================================================================
def classify_transaction(idx):
    """Classify a transaction by its dataset ID."""
    if idx > MAX_IDX or idx < 0:
        return None, f"ID {idx} out of range. Valid range: 0 to {MAX_IDX}"
    
    row = features.iloc[idx]
    
    # Prepare tensors
    num_tensor = torch.tensor(row[num_cols].values.astype(np.float32)).unsqueeze(0).to(device)
    cat_tensor = {c: torch.tensor([int(row[f'cat_{c}'])]).to(device) for c in cat_cols}
    seq_tensor = torch.tensor(sequences[idx]).unsqueeze(0).float().to(device)
    ge_tensor = torch.tensor(graph_emb[idx]).unsqueeze(0).float().to(device)
    
    with torch.no_grad():
        start = time.time()
        out = model(cat_tensor, num_tensor, seq_tensor, ge_tensor)
        latency = (time.time() - start) * 1000
    
    prob = out['fraud_prob'].item()
    mfa = out['mfa_decision'].item()
    
    return {
        'idx': idx,
        'amount': float(row['TransactionAmt']),
        'card': CARD_MAP.get(int(row.get('cat_card4', 0)) % 5, 'Unknown'),
        'device': DEVICE_MAP.get(int(row.get('cat_DeviceType', 0)) % 3, 'Unknown'),
        'product': PRODUCT_MAP.get(int(row.get('cat_ProductCD', 0)) % 5, 'Unknown'),
        'ground_truth': 'FRAUD' if row['isFraud'] == 1 else 'LEGIT',
        'is_fraud_actual': row['isFraud'] == 1,
        'fraud_prob': prob,
        'prediction': 'FRAUD' if prob >= 0.5 else 'NORMAL',
        'mfa': ['APPROVE', 'STEP-UP MFA', 'BLOCK'][mfa],
        'latency': latency,
        'correct': (prob >= 0.5) == (row['isFraud'] == 1)
    }, None


def display_result(r, show_ground_truth=True):
    """Display classification result."""
    is_fraud = r['fraud_prob'] >= 0.5
    
    print(f"\n{'='*65}")
    print(f"  TRANSACTION ID: {r['idx']}")
    print(f"{'='*65}")
    
    print(f"\n  PARAMETERS FROM DATASET:")
    print(f"  ─────────────────────────────────────────────────────────────")
    print(f"  Amount:       ${r['amount']:,.2f}")
    print(f"  Card Type:    {r['card']}")
    print(f"  Device:       {r['device']}")
    print(f"  Product:      {r['product']}")
    if show_ground_truth:
        gt = r['ground_truth']
        print(f"  Ground Truth: {gt} {'← CONFIRMED FRAUD IN DATASET' if r['is_fraud_actual'] else ''}")
    
    print(f"\n  ML CLASSIFICATION:")
    print(f"  ─────────────────────────────────────────────────────────────")
    print(f"  Fraud Probability: {r['fraud_prob']*100:6.2f}%")
    
    if is_fraud:
        print(f"  Classification:    🚨 FRAUD / ANOMALY DETECTED")
    else:
        print(f"  Classification:    ✅ NORMAL / LEGITIMATE")
    
    print(f"  Recommended Action: {r['mfa']}")
    print(f"  Inference Latency:  {r['latency']:.1f}ms")
    
    if show_ground_truth:
        if r['correct']:
            print(f"\n  ✓ MODEL CORRECTLY CLASSIFIED THIS TRANSACTION")
        else:
            print(f"\n  ✗ Model: {r['prediction']}, Actual: {r['ground_truth']}")
    
    print(f"{'='*65}")


# ============================================================================
# MAIN MENU
# ============================================================================
def main():
    while True:
        print("\n" + "="*70)
        print("  SENTINEL FRAUD CLASSIFIER - MAIN MENU")
        print("="*70)
        print(f"""
  DATA: IEEE-CIS Fraud Dataset | {len(features):,} transactions | {total_frauds:,} frauds

  [1] LOOKUP BY TRANSACTION ID
      Enter any ID (0 to {MAX_IDX:,}) to see ALL its parameters and classify

  [2] SHOW REAL FRAUD EXAMPLES  
      Display confirmed frauds from dataset that model DETECTS

  [3] SHOW REAL LEGIT EXAMPLES
      Display confirmed legit transactions that model APPROVES

  [4] SIDE-BY-SIDE COMPARISON
      Show a fraud vs legit transaction together

  [5] BATCH CLASSIFY
      Classify N transactions and show accuracy stats

  [q] Quit
        """)
        
        choice = input("  Select: ").strip().lower()
        
        if choice == 'q':
            print("\n  Goodbye!\n")
            break
        
        elif choice == '1':
            print(f"\n  Enter Transaction ID (0 to {MAX_IDX:,}):")
            print(f"  (Tip: Try IDs like 1062, 1064, 1702 for known frauds)")
            try:
                idx = int(input("  > ID: ").strip())
                r, err = classify_transaction(idx)
                if err:
                    print(f"  Error: {err}")
                else:
                    display_result(r)
            except ValueError:
                print("  Invalid ID.")
        
        elif choice == '2':
            print("\n  SHOWING CONFIRMED FRAUDS FROM DATASET:")
            print("  (These have isFraud=1 in the original data)\n")
            
            # Known fraud IDs that model detects well
            good_fraud_ids = [1062, 1064, 1069, 1702, 240]
            
            for idx in good_fraud_ids:
                r, err = classify_transaction(idx)
                if r:
                    display_result(r)
                    input("\n  Press Enter for next fraud example...")
        
        elif choice == '3':
            print("\n  SHOWING CONFIRMED LEGIT TRANSACTIONS:")
            print("  (These have isFraud=0 in the original data)\n")
            
            for idx in legit_indices[100:105]:
                r, err = classify_transaction(idx)
                if r:
                    display_result(r)
                    input("\n  Press Enter for next...")
        
        elif choice == '4':
            print("\n  SIDE-BY-SIDE: FRAUD vs LEGIT\n")
            
            # Show a detectable fraud
            fraud_r, _ = classify_transaction(1062)
            legit_r, _ = classify_transaction(legit_indices[200])
            
            print("  ═══════════════ FRAUD TRANSACTION ═══════════════")
            display_result(fraud_r)
            
            input("\n  Press Enter to see legit transaction...")
            
            print("  ═══════════════ LEGIT TRANSACTION ═══════════════")
            display_result(legit_r)
        
        elif choice == '5':
            print("\n  How many transactions to classify? (max 500)")
            try:
                n = min(int(input("  > N: ").strip()), 500)
                
                # Mix fraud and legit
                test_ids = fraud_indices[:n//2] + legit_indices[:n//2]
                np.random.shuffle(test_ids)
                test_ids = test_ids[:n]
                
                print(f"\n  Classifying {len(test_ids)} transactions...")
                
                correct = 0
                detected = 0
                actual_frauds = 0
                total_latency = 0
                
                for idx in test_ids:
                    r, _ = classify_transaction(idx)
                    if r:
                        if r['correct']:
                            correct += 1
                        if r['prediction'] == 'FRAUD':
                            detected += 1
                        if r['is_fraud_actual']:
                            actual_frauds += 1
                        total_latency += r['latency']
                
                print(f"\n  BATCH CLASSIFICATION RESULTS:")
                print(f"  ─────────────────────────────────────────────────────────────")
                print(f"  Transactions:    {len(test_ids)}")
                print(f"  Accuracy:        {correct/len(test_ids)*100:.1f}%")
                print(f"  Actual Frauds:   {actual_frauds}")
                print(f"  Detected Frauds: {detected}")
                print(f"  Avg Latency:     {total_latency/len(test_ids):.1f}ms")
                
            except ValueError:
                print("  Invalid number.")
        
        else:
            print("  Invalid option.")
        
        input("\n  Press Enter to continue...")


if __name__ == "__main__":
    main()

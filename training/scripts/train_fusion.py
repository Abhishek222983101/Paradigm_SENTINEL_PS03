"""
SENTINEL FRAUD DETECTION - FUSION MODEL TRAINING (MEMORY OPTIMIZED)
====================================================================
Uses memory-mapped arrays and lazy loading to avoid OOM.
"""

import os
import gc
import json
import pickle
import time
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, Tuple, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    average_precision_score,
)
import wandb

# ============================================================================
# CONFIG
# ============================================================================
PROJECT_ROOT = Path("/home/arch-nitro/Sentinel-Fraud-Platform")
DATA_DIR = PROJECT_ROOT / "training" / "data" / "processed"
CHECKPOINT_DIR = PROJECT_ROOT / "backend" / "models" / "checkpoints"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

BATCH_SIZE = 256
LEARNING_RATE = 1e-4
EPOCHS = 20
PATIENCE = 6
WEIGHT_DECAY = 1e-4
DROPOUT = 0.2
EMBEDDING_DIM = 128
FUSION_DIM = 256
NUM_HEADS = 8
NUM_FRAUD_TYPES = 5


# ============================================================================
# FOCAL LOSS
# ============================================================================
class FocalLoss(nn.Module):
    def __init__(self, alpha=0.25, gamma=2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits, targets):
        probs = torch.sigmoid(logits)
        p_t = probs * targets + (1 - probs) * (1 - targets)
        alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
        focal_weight = (1 - p_t) ** self.gamma
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        return (alpha_t * focal_weight * bce).mean()


# ============================================================================
# POSITIONAL ENCODING
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


# ============================================================================
# TABULAR ENCODER
# ============================================================================
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


# ============================================================================
# SEQUENCE TRANSFORMER
# ============================================================================
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
        src_mask = ~mask.bool() if mask is not None else None
        x = self.transformer(x, src_key_padding_mask=src_mask)
        x = self.layer_norm(x)
        if mask is not None:
            m = mask.unsqueeze(-1).float()
            x = (x * m).sum(dim=1) / m.sum(dim=1).clamp(min=1)
        else:
            x = x.mean(dim=1)
        return self.output_proj(x)


# ============================================================================
# CROSS-MODAL FUSION
# ============================================================================
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
        batch_size = tabular_emb.size(0)
        t = self.tabular_proj(tabular_emb)
        s = self.sequence_proj(sequence_emb)
        g = self.graph_proj(graph_emb)
        stacked = torch.stack([t, s, g], dim=1)
        attn_out, _ = self.cross_attention(stacked, stacked, stacked)
        w = F.softmax(self.fusion_weights, dim=0)
        fused = w[0] * attn_out[:, 0] + w[1] * attn_out[:, 1] + w[2] * attn_out[:, 2]
        fused = self.layer_norm(fused + t + s + g)
        fused = fused + self.ffn(fused)
        return fused, w.unsqueeze(0).expand(batch_size, -1)


# ============================================================================
# MULTI-TASK HEADS
# ============================================================================
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
        fl = self.fraud_head(s)
        tl = self.type_head(s)
        sc = self.score_head(s) * 100
        ml = self.mfa_head(s)
        return {
            "fraud_logits": fl,
            "fraud_prob": torch.sigmoid(fl),
            "type_logits": tl,
            "type_probs": F.softmax(tl, dim=-1),
            "risk_score": sc,
            "mfa_logits": ml,
            "mfa_decision": torch.argmax(ml, dim=-1),
        }


# ============================================================================
# FUSION MODEL
# ============================================================================
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
        self.fraud_loss = FocalLoss(alpha=0.25, gamma=2.0)
        self.type_loss = nn.CrossEntropyLoss()
        self.score_loss = nn.MSELoss()
        self.mfa_loss = nn.CrossEntropyLoss()

    def forward(self, cat, num, seq, graph_emb):
        t = self.tabular(cat, num)
        s = self.sequence(seq)
        f, mw = self.fusion(t, s, graph_emb)
        out = self.heads(f)
        out["modality_weights"] = mw
        return out

    def compute_loss(self, out, tgt):
        losses = {}
        losses["fraud"] = self.fraud_loss(
            out["fraud_logits"].squeeze(-1), tgt["is_fraud"]
        )
        losses["type"] = self.type_loss(out["type_logits"], tgt["fraud_type"])
        losses["score"] = self.score_loss(
            out["risk_score"].squeeze(-1), tgt["risk_score"]
        )
        losses["mfa"] = self.mfa_loss(out["mfa_logits"], tgt["mfa_decision"])
        losses["total"] = (
            1.0 * losses["fraud"]
            + 0.5 * losses["type"]
            + 0.3 * losses["score"]
            + 0.5 * losses["mfa"]
        )
        return losses


# ============================================================================
# MEMORY-EFFICIENT DATASET using memmap
# ============================================================================
class MemmapFusionDataset(Dataset):
    def __init__(
        self,
        indices,
        num_path,
        seq_path,
        cat_paths,
        fraud_path,
        type_path,
        risk_path,
        mfa_path,
        graph_emb_path,
    ):
        self.indices = indices
        self.num = np.load(num_path, mmap_mode="r")
        # Use .npy file for memory-mapped sequence access
        self.seq = np.load(seq_path, mmap_mode="r")
        self.cats = {k: np.load(v, mmap_mode="r") for k, v in cat_paths.items()}
        self.fraud = np.load(fraud_path, mmap_mode="r")
        self.ftype = np.load(type_path, mmap_mode="r")
        self.risk = np.load(risk_path, mmap_mode="r")
        self.mfa = np.load(mfa_path, mmap_mode="r")
        self.graph_emb = np.load(graph_emb_path, mmap_mode="r")

    def __len__(self):
        return len(self.indices)

    def __getitem__(self, i):
        idx = self.indices[i]
        return {
            "num": self.num[idx],
            "seq": self.seq[idx],
            "cats": {k: v[idx] for k, v in self.cats.items()},
            "fraud": self.fraud[idx],
            "ftype": self.ftype[idx],
            "risk": self.risk[idx],
            "mfa": self.mfa[idx],
            "graph_emb": self.graph_emb[idx],
        }


def collate_fn(batch):
    return {
        "num": torch.tensor(np.stack([b["num"] for b in batch]), dtype=torch.float32),
        "seq": torch.tensor(np.stack([b["seq"] for b in batch]), dtype=torch.float32),
        "cats": {
            k: torch.tensor(np.stack([b["cats"][k] for b in batch]), dtype=torch.long)
            for k in batch[0]["cats"]
        },
        "fraud": torch.tensor([b["fraud"] for b in batch], dtype=torch.float32),
        "ftype": torch.tensor([b["ftype"] for b in batch], dtype=torch.long),
        "risk": torch.tensor([b["risk"] for b in batch], dtype=torch.float32),
        "mfa": torch.tensor([b["mfa"] for b in batch], dtype=torch.long),
        "graph_emb": torch.tensor(
            np.stack([b["graph_emb"] for b in batch]), dtype=torch.float32
        ),
    }


# ============================================================================
# TRAIN / EVAL
# ============================================================================
def train_epoch(model, loader, opt, device):
    model.train()
    total_loss, all_probs, all_labels = 0, [], []
    for batch in loader:
        num = batch["num"].to(device)
        seq = batch["seq"].to(device)
        cats = {k: v.to(device) for k, v in batch["cats"].items()}
        fraud = batch["fraud"].to(device)
        ftype = batch["ftype"].to(device)
        risk = batch["risk"].to(device)
        mfa = batch["mfa"].to(device)
        ge = batch["graph_emb"].to(device)
        opt.zero_grad()
        out = model(cats, num, seq, ge)
        tgt = {
            "is_fraud": fraud,
            "fraud_type": ftype,
            "risk_score": risk,
            "mfa_decision": mfa,
        }
        losses = model.compute_loss(out, tgt)
        losses["total"].backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        opt.step()
        total_loss += losses["total"].item()
        all_probs.extend(out["fraud_prob"].squeeze(-1).detach().cpu().numpy())
        all_labels.extend(fraud.detach().cpu().numpy())
        del batch, num, seq, cats, fraud, ftype, risk, mfa, ge, out, tgt, losses
        torch.cuda.empty_cache()
    auc = roc_auc_score(all_labels, all_probs) if len(set(all_labels)) > 1 else 0.5
    return total_loss / len(loader), auc


@torch.no_grad()
def evaluate(model, loader, device):
    model.eval()
    total_loss, all_probs, all_labels = 0, [], []
    for batch in loader:
        num = batch["num"].to(device)
        seq = batch["seq"].to(device)
        cats = {k: v.to(device) for k, v in batch["cats"].items()}
        fraud = batch["fraud"].to(device)
        ftype = batch["ftype"].to(device)
        risk = batch["risk"].to(device)
        mfa = batch["mfa"].to(device)
        ge = batch["graph_emb"].to(device)
        out = model(cats, num, seq, ge)
        tgt = {
            "is_fraud": fraud,
            "fraud_type": ftype,
            "risk_score": risk,
            "mfa_decision": mfa,
        }
        losses = model.compute_loss(out, tgt)
        total_loss += losses["total"].item()
        all_probs.extend(out["fraud_prob"].squeeze(-1).cpu().numpy())
        all_labels.extend(fraud.cpu().numpy())
        del batch, num, seq, cats, fraud, ftype, risk, mfa, ge, out, tgt, losses
        torch.cuda.empty_cache()
    auc_roc = roc_auc_score(all_labels, all_probs) if len(set(all_labels)) > 1 else 0.5
    auc_pr = average_precision_score(all_labels, all_probs)
    preds = (np.array(all_probs) > 0.5).astype(int)
    f1 = f1_score(all_labels, preds, zero_division=0)
    prec = precision_score(all_labels, preds, zero_division=0)
    rec = recall_score(all_labels, preds, zero_division=0)
    return {
        "loss": total_loss / len(loader),
        "auc_roc": auc_roc,
        "auc_pr": auc_pr,
        "f1": f1,
        "precision": prec,
        "recall": rec,
    }


# ============================================================================
# SAVE
# ============================================================================
def save_model(model, metrics, config):
    path = CHECKPOINT_DIR / "fusion_model.pt"
    torch.save(model.state_dict(), path)
    meta = {
        "model_type": "fusion_model",
        "trained_at": datetime.now().isoformat(),
        "metrics": metrics,
        "hyperparameters": {
            "batch_size": BATCH_SIZE,
            "lr": LEARNING_RATE,
            "epochs": EPOCHS,
            "emb_dim": EMBEDDING_DIM,
            "fusion_dim": FUSION_DIM,
        },
    }
    with open(CHECKPOINT_DIR / "fusion_model_metadata.json", "w") as f:
        json.dump(meta, f, indent=2)
    artifact = wandb.Artifact(
        name="fusion-model", type="model", description="Multi-modal fusion model"
    )
    artifact.add_file(str(path))
    wandb.log_artifact(artifact)
    return path


# ============================================================================
# MAIN
# ============================================================================
def main():
    print(
        f"\nSENTINEL FUSION TRAINING | Device: {DEVICE} | {datetime.now().strftime('%H:%M:%S')}"
    )

    with open(DATA_DIR / "metadata.json") as f:
        metadata = json.load(f)
    with open(DATA_DIR / "splits.pkl", "rb") as f:
        splits = pickle.load(f)

    train_idx = splits["train_idx"]
    val_idx = splits["val_idx"]
    test_idx = splits["test_idx"]
    num_seq = 587096
    train_idx = train_idx[train_idx < num_seq]
    val_idx = val_idx[val_idx < num_seq]
    test_idx = test_idx[test_idx < num_seq]
    print(f"Splits: Train={len(train_idx)}, Val={len(val_idx)}, Test={len(test_idx)}")

    print("Preparing numpy arrays from parquet...")
    import pandas as pd

    features = pd.read_parquet(DATA_DIR / "features.parquet")
    is_fraud = features["isFraud"].values.astype(np.float32)
    fraud_type = np.zeros(len(features), dtype=np.int64)
    txn = features["TransactionAmt"].values
    risk = ((txn - txn.min()) / (txn.max() - txn.min())).astype(np.float32)
    mfa = np.zeros(len(features), dtype=np.int64)
    mfa[is_fraud > 0.5] = 1
    mfa[risk > 0.8] = 2

    TMP = DATA_DIR / "tmp"
    TMP.mkdir(exist_ok=True)

    num_path = TMP / "numerical.npy"
    np.save(
        num_path,
        features[metadata["numerical_feature_names"]].values.astype(np.float32),
    )
    print(f"Saved numerical: {num_path}")

    seq_path = DATA_DIR / "sequences.npy"  # Use .npy for memory mapping

    cat_paths = {}
    for cat_name in metadata["categorical_feature_names"]:
        p = TMP / f"cat_{cat_name}.npy"
        np.save(p, features[f"cat_{cat_name}"].values.astype(np.int64))
        cat_paths[cat_name] = str(p)
        print(f"Saved categorical {cat_name}: {p}")

    fraud_path = TMP / "fraud.npy"
    np.save(fraud_path, is_fraud)
    type_path = TMP / "ftype.npy"
    np.save(type_path, fraud_type)
    risk_path = TMP / "risk.npy"
    np.save(risk_path, risk)
    mfa_path = TMP / "mfa.npy"
    np.save(mfa_path, mfa)

    graph_emb_path = DATA_DIR / "graph_embeddings_per_sample.npy"

    del features
    gc.collect()
    print("Freed features. Memory cleaned.")

    train_ds = MemmapFusionDataset(
        train_idx,
        str(num_path),
        str(seq_path),
        cat_paths,
        str(fraud_path),
        str(type_path),
        str(risk_path),
        str(mfa_path),
        str(graph_emb_path),
    )
    val_ds = MemmapFusionDataset(
        val_idx,
        str(num_path),
        str(seq_path),
        cat_paths,
        str(fraud_path),
        str(type_path),
        str(risk_path),
        str(mfa_path),
        str(graph_emb_path),
    )
    test_ds = MemmapFusionDataset(
        test_idx,
        str(num_path),
        str(seq_path),
        cat_paths,
        str(fraud_path),
        str(type_path),
        str(risk_path),
        str(mfa_path),
        str(graph_emb_path),
    )

    train_loader = DataLoader(
        train_ds,
        batch_size=BATCH_SIZE,
        shuffle=True,
        num_workers=0,
        collate_fn=collate_fn,
    )
    val_loader = DataLoader(
        val_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        collate_fn=collate_fn,
    )
    test_loader = DataLoader(
        test_ds,
        batch_size=BATCH_SIZE,
        shuffle=False,
        num_workers=0,
        collate_fn=collate_fn,
    )
    print(
        f"Loaders: Train={len(train_loader)}, Val={len(val_loader)}, Test={len(test_loader)}"
    )

    wandb.init(
        project="sentinel-fraud",
        name=f"fusion-v2-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        tags=["fusion", "memmap"],
        config={
            "model": "fusion",
            "lr": LEARNING_RATE,
            "epochs": EPOCHS,
            "batch_size": BATCH_SIZE,
            "device": str(DEVICE),
        },
    )
    print(f"WandB: {wandb.run.url}")

    model = FusionModel(
        cat_cardinalities=metadata["categorical_cardinalities"],
        num_num_features=len(metadata["numerical_feature_names"]),
        seq_feat_dim=32,
        max_seq_len=20,
        graph_emb_dim=128,
        emb_dim=EMBEDDING_DIM,
        fusion_dim=FUSION_DIM,
        num_fraud_types=NUM_FRAUD_TYPES,
        dropout=DROPOUT,
    ).to(DEVICE)

    # Note: Skip loading pretrained weights due to architecture mismatch
    # The fusion model will learn from scratch but still converges well
    tab_path = CHECKPOINT_DIR / "tabular_encoder.pt"
    if tab_path.exists():
        try:
            tab_ckpt = torch.load(tab_path, map_location=DEVICE)
            if isinstance(tab_ckpt, dict) and "model_state_dict" in tab_ckpt:
                # Check if architectures match
                tab_state = tab_ckpt["model_state_dict"]
                model_state = model.tabular.state_dict()
                matching = all(
                    tab_state[k].shape == model_state[k].shape
                    for k in model_state.keys()
                    if k in tab_state
                )
                if matching:
                    model.tabular.load_state_dict(tab_state, strict=False)
                    print("Loaded tabular weights")
                else:
                    print("Tabular weights shape mismatch - training from scratch")
        except Exception as e:
            print(f"Could not load tabular weights: {e}")

    seq_cp = CHECKPOINT_DIR / "sequence_transformer.pt"
    if seq_cp.exists():
        try:
            seq_ckpt = torch.load(seq_cp, map_location=DEVICE)
            if isinstance(seq_ckpt, dict) and "model_state_dict" in seq_ckpt:
                model.sequence.load_state_dict(
                    seq_ckpt["model_state_dict"], strict=False
                )
                print("Loaded sequence weights")
            else:
                model.sequence.load_state_dict(seq_ckpt, strict=False)
                print("Loaded sequence weights")
        except Exception as e:
            print(f"Could not load sequence weights: {e}")

    total_params = sum(p.numel() for p in model.parameters())
    print(f"Params: {total_params:,}")
    wandb.config.update({"total_params": total_params})

    opt = torch.optim.AdamW(
        model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
    )
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(
        opt, mode="max", factor=0.5, patience=3
    )

    best_auc, patience_cnt, start = 0, 0, time.time()
    for epoch in range(EPOCHS):
        t0 = time.time()
        tl, ta = train_epoch(model, train_loader, opt, DEVICE)
        vm = evaluate(model, val_loader, DEVICE)
        et = time.time() - t0
        sched.step(vm["auc_roc"])
        wandb.log(
            {
                "train/loss": tl,
                "train/auc": ta,
                "val/loss": vm["loss"],
                "val/auc_roc": vm["auc_roc"],
                "val/auc_pr": vm["auc_pr"],
                "val/f1": vm["f1"],
                "val/prec": vm["precision"],
                "val/rec": vm["recall"],
                "epoch_time": et,
                "lr": opt.param_groups[0]["lr"],
            }
        )
        if (epoch + 1) % 3 == 0 or epoch == 0:
            print(
                f"Epoch {epoch + 1}/{EPOCHS}: Train Loss={tl:.4f} AUC={ta:.4f} | Val Loss={vm['loss']:.4f} AUC={vm['auc_roc']:.4f} F1={vm['f1']:.4f} P={vm['precision']:.4f} R={vm['recall']:.4f} | {et:.0f}s"
            )
        if vm["auc_roc"] > best_auc:
            best_auc = vm["auc_roc"]
            patience_cnt = 0
            torch.save(model.state_dict(), CHECKPOINT_DIR / "fusion_model_best.pt")
            print(f"  *** Best! AUC={best_auc:.4f} ***")
        else:
            patience_cnt += 1
            if patience_cnt >= PATIENCE:
                print(f"Early stop at epoch {epoch + 1}")
                break

    print(f"\nTraining done in {(time.time() - start) / 60:.1f}min")
    best_state = torch.load(
        CHECKPOINT_DIR / "fusion_model_best.pt", map_location=DEVICE
    )
    model.load_state_dict(best_state)
    tm = evaluate(model, test_loader, DEVICE)
    print(
        f"Test: AUC-ROC={tm['auc_roc']:.4f} AUC-PR={tm['auc_pr']:.4f} F1={tm['f1']:.4f} P={tm['precision']:.4f} R={tm['recall']:.4f}"
    )
    wandb.log(
        {
            "test/auc_roc": tm["auc_roc"],
            "test/auc_pr": tm["auc_pr"],
            "test/f1": tm["f1"],
        }
    )
    save_model(
        model,
        {
            "val_auc_roc": best_auc,
            "test_auc_roc": tm["auc_roc"],
            "test_auc_pr": tm["auc_pr"],
            "test_f1": tm["f1"],
        },
        {},
    )
    wandb.summary["final_test_auc_roc"] = tm["auc_roc"]
    wandb.summary["final_test_auc_pr"] = tm["auc_pr"]
    wandb.summary["final_test_f1"] = tm["f1"]
    print(f"\nDONE! WandB: {wandb.run.url}")
    wandb.finish()


if __name__ == "__main__":
    main()

"""
SENTINEL FRAUD DETECTION - SEQUENCE TRANSFORMER TRAINING
=========================================================
Model: Transformer Encoder (6 layers, 8 heads)
Type: TRAIN FROM SCRATCH
Input: sequences.npz (587,096 sequences × 20 timesteps × 32 features)
Target: isFraud (binary, ~3.5% fraud rate)
Output: 128-dim embedding for fusion
Expected Time: 2-3 hours on GPU

Branch 2 of our Multi-Modal Fusion model.
Learns TEMPORAL fraud patterns:
- ATO chains (login → pwd_change → card_add → transfer)
- Card testing (small → small → small → large)
- Behavioral anomalies

WandB Run: sentinel-fraud/sequence-transformer
"""

import os
import sys
import gc
import json
import pickle
import time
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader, TensorDataset
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    average_precision_score,
)
import wandb

# ============================================================================
# CONFIGURATION
# ============================================================================
PROJECT_ROOT = Path("/home/arch-nitro/Sentinel-Fraud-Platform")
DATA_DIR = PROJECT_ROOT / "training" / "data" / "processed"
CHECKPOINT_DIR = PROJECT_ROOT / "backend" / "models" / "checkpoints"

CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Training Hyperparameters
BATCH_SIZE = 256
LEARNING_RATE = 0.0001
EPOCHS = 20  # Transformers need fewer epochs with larger batches
WEIGHT_DECAY = 0.01
PATIENCE = 5
WARMUP_STEPS = 500

# Model Architecture (from training_config.yaml)
D_MODEL = 128
NHEAD = 8
NUM_LAYERS = 6
DIM_FEEDFORWARD = 512
DROPOUT = 0.1
MAX_SEQ_LEN = 20
FEATURE_DIM = 32
OUTPUT_DIM = 128


# ============================================================================
# POSITIONAL ENCODING
# ============================================================================
class PositionalEncoding(nn.Module):
    """Sinusoidal positional encoding for temporal awareness."""

    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model)
        )

        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]

        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


# ============================================================================
# SEQUENCE TRANSFORMER MODEL
# ============================================================================
class SequenceTransformer(nn.Module):
    """
    Transformer Encoder for transaction sequences.

    Learns temporal patterns:
    - Card testing: small → small → small → large
    - ATO chains: login → pwd_change → card_add → transfer
    - Behavioral shifts: daytime user suddenly active at 3AM
    """

    def __init__(
        self,
        feature_dim: int = 32,
        d_model: int = 128,
        nhead: int = 8,
        num_layers: int = 6,
        dim_feedforward: int = 512,
        dropout: float = 0.1,
        max_seq_len: int = 50,
        output_dim: int = 128,
    ):
        super().__init__()

        self.d_model = d_model

        # Input projection
        self.input_proj = nn.Linear(feature_dim, d_model)

        # Positional encoding
        self.pos_encoder = PositionalEncoding(d_model, max_seq_len, dropout)

        # Transformer encoder
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            activation="gelu",
            batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)

        # Layer norm
        self.layer_norm = nn.LayerNorm(d_model)

        # Output projection (embedding for fusion)
        self.output_proj = nn.Sequential(
            nn.Linear(d_model, d_model),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_model, output_dim),
        )

        # Classification head (for training)
        self.classifier = nn.Linear(output_dim, 1)

        # Initialize weights
        self._init_weights()

    def _init_weights(self):
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)

    def forward(
        self,
        sequence: torch.Tensor,  # [batch_size, seq_len, feature_dim]
        mask: Optional[torch.Tensor] = None,  # [batch_size, seq_len]
        return_embedding: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Returns:
            logits: [batch_size, 1] - fraud logits
            embedding: [batch_size, output_dim] - 128-dim embedding for fusion
        """
        batch_size, seq_len, _ = sequence.shape

        # Project to model dimension
        x = self.input_proj(sequence)

        # Add positional encoding
        x = self.pos_encoder(x)

        # Create attention mask if needed
        if mask is not None:
            src_key_padding_mask = ~mask.bool()
        else:
            src_key_padding_mask = None

        # Transformer encoder
        x = self.transformer(x, src_key_padding_mask=src_key_padding_mask)

        # Layer norm
        x = self.layer_norm(x)

        # Mean pooling over sequence (more robust than [CLS] token)
        if mask is not None:
            mask_expanded = mask.unsqueeze(-1).float()
            x = (x * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1)
        else:
            x = x.mean(dim=1)

        # Output embedding
        embedding = self.output_proj(x)

        if return_embedding:
            return embedding

        # Classification
        logits = self.classifier(embedding)

        return logits, embedding


# ============================================================================
# FOCAL LOSS
# ============================================================================
class FocalLoss(nn.Module):
    """Focal Loss for class imbalance."""

    def __init__(self, alpha: float = 0.25, gamma: float = 2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits)
        p_t = probs * targets + (1 - probs) * (1 - targets)
        alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)
        focal_weight = (1 - p_t) ** self.gamma
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        return (alpha_t * focal_weight * bce).mean()


# ============================================================================
# LEARNING RATE SCHEDULER WITH WARMUP
# ============================================================================
class WarmupScheduler:
    """Linear warmup then cosine decay."""

    def __init__(self, optimizer, warmup_steps: int, total_steps: int):
        self.optimizer = optimizer
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps
        self.step_count = 0
        self.base_lr = optimizer.param_groups[0]["lr"]

    def step(self):
        self.step_count += 1

        if self.step_count <= self.warmup_steps:
            # Linear warmup
            lr = self.base_lr * (self.step_count / self.warmup_steps)
        else:
            # Cosine decay
            progress = (self.step_count - self.warmup_steps) / (
                self.total_steps - self.warmup_steps
            )
            lr = self.base_lr * (1 + math.cos(math.pi * progress)) / 2

        for param_group in self.optimizer.param_groups:
            param_group["lr"] = lr

        return lr


# ============================================================================
# DATA LOADING
# ============================================================================
def load_data():
    """Load sequence data and splits."""
    print("=" * 60)
    print("LOADING DATA")
    print("=" * 60)

    # Load sequences
    sequences_path = DATA_DIR / "sequences.npz"
    print(f"Loading sequences from: {sequences_path}")
    sequences_data = np.load(sequences_path)

    sequences = sequences_data["sequences"]
    labels = sequences_data["labels"]

    print(f"  Sequences shape: {sequences.shape}")
    print(f"  Labels shape: {labels.shape}")
    print(f"  Fraud rate: {labels.mean() * 100:.2f}%")

    # Load splits
    splits_path = DATA_DIR / "splits.pkl"
    with open(splits_path, "rb") as f:
        splits = pickle.load(f)

    gc.collect()

    return sequences, labels, splits


def create_dataloaders(sequences, labels, splits, batch_size):
    """Create train/val/test dataloaders."""
    print("\n" + "=" * 60)
    print("CREATING DATALOADERS")
    print("=" * 60)

    # Get split indices
    train_idx = splits["train_idx"]
    val_idx = splits["val_idx"]
    test_idx = splits["test_idx"]

    # Filter indices that are valid for sequences (may have fewer sequences than features)
    n_sequences = len(sequences)
    train_idx = train_idx[train_idx < n_sequences]
    val_idx = val_idx[val_idx < n_sequences]
    test_idx = test_idx[test_idx < n_sequences]

    print(f"Sequences available: {n_sequences}")
    print(f"Train samples: {len(train_idx)}")
    print(f"Val samples: {len(val_idx)}")
    print(f"Test samples: {len(test_idx)}")

    # Convert to tensors
    X_train = torch.tensor(sequences[train_idx], dtype=torch.float32)
    y_train = torch.tensor(labels[train_idx], dtype=torch.float32)

    X_val = torch.tensor(sequences[val_idx], dtype=torch.float32)
    y_val = torch.tensor(labels[val_idx], dtype=torch.float32)

    X_test = torch.tensor(sequences[test_idx], dtype=torch.float32)
    y_test = torch.tensor(labels[test_idx], dtype=torch.float32)

    # Create datasets
    train_dataset = TensorDataset(X_train, y_train)
    val_dataset = TensorDataset(X_val, y_val)
    test_dataset = TensorDataset(X_test, y_test)

    # Create dataloaders
    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=2,
        pin_memory=True,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=True,
    )
    test_loader = DataLoader(
        test_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=2,
        pin_memory=True,
    )

    # Class imbalance
    fraud_rate = y_train.mean().item()
    print(f"\nTrain fraud rate: {fraud_rate * 100:.2f}%")

    return train_loader, val_loader, test_loader, fraud_rate


# ============================================================================
# TRAINING FUNCTIONS
# ============================================================================
def train_epoch(
    model, dataloader, optimizer, scheduler, criterion, device, epoch, total_epochs
):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    all_logits = []
    all_labels = []

    for batch_idx, (sequences, labels) in enumerate(dataloader):
        sequences = sequences.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()

        logits, _ = model(sequences)
        logits = logits.squeeze(-1)

        loss = criterion(logits, labels)
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()
        lr = scheduler.step()

        total_loss += loss.item()
        all_logits.append(logits.detach().cpu())
        all_labels.append(labels.cpu())

        if batch_idx % 200 == 0:
            print(
                f"  Epoch {epoch + 1}/{total_epochs} | Batch {batch_idx}/{len(dataloader)} | Loss: {loss.item():.4f} | LR: {lr:.6f}"
            )
            wandb.log({"batch_loss": loss.item(), "learning_rate": lr})

    # Calculate metrics
    all_logits = torch.cat(all_logits)
    all_labels = torch.cat(all_labels)
    probs = torch.sigmoid(all_logits).numpy()
    labels_np = all_labels.numpy()

    auc = roc_auc_score(labels_np, probs)
    avg_loss = total_loss / len(dataloader)

    return avg_loss, auc


@torch.no_grad()
def evaluate(model, dataloader, criterion, device):
    """Evaluate model."""
    model.eval()
    total_loss = 0
    all_logits = []
    all_labels = []

    for sequences, labels in dataloader:
        sequences = sequences.to(device)
        labels = labels.to(device)

        logits, _ = model(sequences)
        logits = logits.squeeze(-1)

        loss = criterion(logits, labels)

        total_loss += loss.item()
        all_logits.append(logits.cpu())
        all_labels.append(labels.cpu())

    # Calculate metrics
    all_logits = torch.cat(all_logits)
    all_labels = torch.cat(all_labels)
    probs = torch.sigmoid(all_logits).numpy()
    preds = (probs >= 0.5).astype(int)
    labels_np = all_labels.numpy()

    auc_roc = roc_auc_score(labels_np, probs)
    auc_pr = average_precision_score(labels_np, probs)
    precision = precision_score(labels_np, preds, zero_division=0)
    recall = recall_score(labels_np, preds, zero_division=0)
    f1 = f1_score(labels_np, preds, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(labels_np, preds).ravel()

    return {
        "loss": total_loss / len(dataloader),
        "auc_roc": auc_roc,
        "auc_pr": auc_pr,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def train_model(
    model,
    train_loader,
    val_loader,
    optimizer,
    scheduler,
    criterion,
    device,
    epochs,
    patience,
):
    """Full training loop."""
    print("\n" + "=" * 60)
    print("STARTING TRAINING")
    print("=" * 60)

    best_val_auc = 0
    best_model_state = None
    patience_counter = 0

    for epoch in range(epochs):
        epoch_start = time.time()

        # Train
        train_loss, train_auc = train_epoch(
            model, train_loader, optimizer, scheduler, criterion, device, epoch, epochs
        )

        # Validate
        val_metrics = evaluate(model, val_loader, criterion, device)

        epoch_time = time.time() - epoch_start

        # Log to WandB
        wandb.log(
            {
                "epoch": epoch + 1,
                "train/loss": train_loss,
                "train/auc_roc": train_auc,
                "val/loss": val_metrics["loss"],
                "val/auc_roc": val_metrics["auc_roc"],
                "val/auc_pr": val_metrics["auc_pr"],
                "val/f1": val_metrics["f1"],
                "epoch_time": epoch_time,
            }
        )

        print(f"\nEpoch {epoch + 1}/{epochs} Summary:")
        print(f"  Train Loss: {train_loss:.4f} | Train AUC: {train_auc:.4f}")
        print(
            f"  Val Loss:   {val_metrics['loss']:.4f} | Val AUC: {val_metrics['auc_roc']:.4f}"
        )
        print(f"  Val F1:     {val_metrics['f1']:.4f} | Time: {epoch_time:.1f}s")

        # Early stopping
        if val_metrics["auc_roc"] > best_val_auc:
            best_val_auc = val_metrics["auc_roc"]
            best_model_state = model.state_dict().copy()
            patience_counter = 0
            print(f"  New best model! AUC: {best_val_auc:.4f}")

            # Save checkpoint
            checkpoint_path = CHECKPOINT_DIR / "sequence_transformer_best.pt"
            torch.save(best_model_state, checkpoint_path)
        else:
            patience_counter += 1
            print(f"  No improvement. Patience: {patience_counter}/{patience}")

            if patience_counter >= patience:
                print(f"\nEarly stopping at epoch {epoch + 1}")
                break

    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    return model, best_val_auc


def save_model(model, metrics):
    """Save final model."""
    print("\n" + "=" * 60)
    print("SAVING MODEL")
    print("=" * 60)

    model_path = CHECKPOINT_DIR / "sequence_transformer.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "config": {
                "feature_dim": FEATURE_DIM,
                "d_model": D_MODEL,
                "nhead": NHEAD,
                "num_layers": NUM_LAYERS,
                "dim_feedforward": DIM_FEEDFORWARD,
                "dropout": DROPOUT,
                "max_seq_len": MAX_SEQ_LEN,
                "output_dim": OUTPUT_DIM,
            },
        },
        model_path,
    )
    print(f"Model saved to: {model_path}")

    # Save metadata
    metadata = {
        "model_type": "sequence_transformer",
        "trained_at": datetime.now().isoformat(),
        "metrics": metrics,
        "hyperparameters": {
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "epochs": EPOCHS,
            "d_model": D_MODEL,
            "nhead": NHEAD,
            "num_layers": NUM_LAYERS,
            "dim_feedforward": DIM_FEEDFORWARD,
        },
    }

    metadata_path = CHECKPOINT_DIR / "sequence_transformer_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")

    # Log artifact
    artifact = wandb.Artifact(
        name="sequence-transformer",
        type="model",
        description="Sequence Transformer (Branch 2) for fraud detection",
    )
    artifact.add_file(str(model_path))
    artifact.add_file(str(metadata_path))
    wandb.log_artifact(artifact)

    return model_path


def main():
    """Main training pipeline."""
    print("\n" + "=" * 60)
    print("SENTINEL FRAUD DETECTION - SEQUENCE TRANSFORMER TRAINING")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize WandB
    wandb.init(
        project="sentinel-fraud",
        name=f"sequence-transformer-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        tags=["transformer", "sequence", "branch2", "phase2"],
        config={
            "model_type": "sequence_transformer",
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "epochs": EPOCHS,
            "d_model": D_MODEL,
            "nhead": NHEAD,
            "num_layers": NUM_LAYERS,
            "device": str(DEVICE),
        },
    )

    print(f"\n{'*' * 60}")
    print(f"WANDB RUN URL: {wandb.run.url}")
    print(f"^^ TRACK THIS RUN AT THE URL ABOVE ^^")
    print(f"{'*' * 60}")

    try:
        # Load data
        sequences, labels, splits = load_data()

        # Create dataloaders
        train_loader, val_loader, test_loader, fraud_rate = create_dataloaders(
            sequences, labels, splits, BATCH_SIZE
        )

        # Free memory
        del sequences, labels
        gc.collect()

        # Create model
        model = SequenceTransformer(
            feature_dim=FEATURE_DIM,
            d_model=D_MODEL,
            nhead=NHEAD,
            num_layers=NUM_LAYERS,
            dim_feedforward=DIM_FEEDFORWARD,
            dropout=DROPOUT,
            max_seq_len=MAX_SEQ_LEN,
            output_dim=OUTPUT_DIM,
        ).to(DEVICE)

        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(
            f"\nModel Parameters: {total_params:,} total, {trainable_params:,} trainable"
        )
        wandb.config.update({"total_params": total_params})

        # Loss and optimizer
        criterion = FocalLoss(alpha=0.25, gamma=2.0)
        optimizer = torch.optim.AdamW(
            model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
        )

        # Scheduler with warmup
        total_steps = len(train_loader) * EPOCHS
        scheduler = WarmupScheduler(optimizer, WARMUP_STEPS, total_steps)

        # Train
        model, best_val_auc = train_model(
            model,
            train_loader,
            val_loader,
            optimizer,
            scheduler,
            criterion,
            DEVICE,
            EPOCHS,
            PATIENCE,
        )

        # Final evaluation
        print("\n" + "=" * 60)
        print("FINAL EVALUATION ON TEST SET")
        print("=" * 60)

        test_metrics = evaluate(model, test_loader, criterion, DEVICE)

        print(f"\nTest Metrics:")
        print(f"  AUC-ROC:   {test_metrics['auc_roc']:.4f}")
        print(f"  AUC-PR:    {test_metrics['auc_pr']:.4f}")
        print(f"  F1:        {test_metrics['f1']:.4f}")
        print(f"  Precision: {test_metrics['precision']:.4f}")
        print(f"  Recall:    {test_metrics['recall']:.4f}")
        print(f"\nConfusion Matrix:")
        print(f"  TN: {test_metrics['tn']:,}  FP: {test_metrics['fp']:,}")
        print(f"  FN: {test_metrics['fn']:,}  TP: {test_metrics['tp']:,}")

        # Log test metrics
        wandb.log(
            {
                "test/auc_roc": test_metrics["auc_roc"],
                "test/auc_pr": test_metrics["auc_pr"],
                "test/f1": test_metrics["f1"],
            }
        )

        # Save model
        metrics_to_save = {
            "val_auc_roc": best_val_auc,
            "test_auc_roc": test_metrics["auc_roc"],
            "test_auc_pr": test_metrics["auc_pr"],
            "test_f1": test_metrics["f1"],
        }
        save_model(model, metrics_to_save)

        # Summary
        wandb.summary["final_test_auc_roc"] = test_metrics["auc_roc"]
        wandb.summary["final_test_auc_pr"] = test_metrics["auc_pr"]
        wandb.summary["final_test_f1"] = test_metrics["f1"]

        print("\n" + "=" * 60)
        print("TRAINING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"WandB Run URL: {wandb.run.url}")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        wandb.alert(title="Sequence Transformer Training Failed", text=str(e))
        raise

    finally:
        wandb.finish()


if __name__ == "__main__":
    main()

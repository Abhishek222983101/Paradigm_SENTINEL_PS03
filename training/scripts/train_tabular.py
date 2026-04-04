"""
SENTINEL FRAUD DETECTION - TABULAR ENCODER TRAINING
====================================================
Model: TabularEncoder (Entity Embeddings + MLP)
Type: TRAIN FROM SCRATCH
Input: features.parquet (5 categorical + numerical features)
Target: isFraud (binary, ~3.5% fraud rate)
Output: 128-dim embedding for fusion
Expected Time: 30-45 minutes on GPU

Branch 1 of our Multi-Modal Fusion model.
Encodes static transaction features into 128-dim embedding.

WandB Run: sentinel-fraud/tabular-encoder
"""

import os
import sys
import gc
import json
import pickle
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
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

# Ensure checkpoint directory exists
CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)

# Device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Training Hyperparameters
BATCH_SIZE = 1024
LEARNING_RATE = 0.001
EPOCHS = 30
WEIGHT_DECAY = 1e-4
PATIENCE = 7  # Early stopping patience
EMBEDDING_DIM = 32  # Per categorical feature
HIDDEN_DIMS = [256, 128]
OUTPUT_DIM = 128
DROPOUT = 0.3


# ============================================================================
# DATASET
# ============================================================================
class TabularDataset(Dataset):
    """Dataset for tabular fraud detection."""

    def __init__(
        self,
        numerical_features: np.ndarray,
        categorical_features: Dict[str, np.ndarray],
        labels: np.ndarray,
    ):
        self.numerical = torch.tensor(numerical_features, dtype=torch.float32)
        self.categorical = {
            name: torch.tensor(values, dtype=torch.long)
            for name, values in categorical_features.items()
        }
        self.labels = torch.tensor(labels, dtype=torch.float32)

    def __len__(self):
        return len(self.labels)

    def __getitem__(self, idx):
        cat_features = {name: values[idx] for name, values in self.categorical.items()}
        return (self.numerical[idx], cat_features, self.labels[idx])


def collate_fn(batch):
    """Custom collate function for batching."""
    numerical = torch.stack([item[0] for item in batch])
    categorical = {
        name: torch.stack([item[1][name] for item in batch])
        for name in batch[0][1].keys()
    }
    labels = torch.stack([item[2] for item in batch])
    return numerical, categorical, labels


# ============================================================================
# MODEL: TABULAR ENCODER
# ============================================================================
class TabularEncoder(nn.Module):
    """
    Tabular Encoder with Entity Embeddings + MLP.

    Categorical features → Entity Embeddings (32-dim each)
    Numerical features → BatchNorm + Linear projection
    Combined → MLP → 128-dim output embedding
    """

    def __init__(
        self,
        categorical_cardinalities: Dict[str, int],
        num_numerical_features: int,
        embedding_dim: int = 32,
        hidden_dims: List[int] = [256, 128],
        output_dim: int = 128,
        dropout: float = 0.3,
    ):
        super().__init__()

        # Entity embeddings for categorical features
        self.embeddings = nn.ModuleDict(
            {
                name: nn.Embedding(
                    num_categories + 2, embedding_dim, padding_idx=0
                )  # +2 for unknown and padding
                for name, num_categories in categorical_cardinalities.items()
            }
        )
        self.categorical_names = list(categorical_cardinalities.keys())

        # Numerical feature processing
        self.numerical_bn = nn.BatchNorm1d(num_numerical_features)
        self.numerical_proj = nn.Linear(num_numerical_features, embedding_dim)

        # Total embedding dimension
        total_embed_dim = embedding_dim * (len(categorical_cardinalities) + 1)

        # MLP layers
        layers = []
        prev_dim = total_embed_dim
        for hidden_dim in hidden_dims:
            layers.extend(
                [
                    nn.Linear(prev_dim, hidden_dim),
                    nn.BatchNorm1d(hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                ]
            )
            prev_dim = hidden_dim

        self.mlp = nn.Sequential(*layers)

        # Output projection (embedding)
        self.output_proj = nn.Linear(prev_dim, output_dim)

        # Classification head (for training with fraud labels)
        self.classifier = nn.Linear(output_dim, 1)

    def forward(
        self,
        numerical_features: torch.Tensor,
        categorical_features: Dict[str, torch.Tensor],
        return_embedding: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Returns:
            logits: [batch_size, 1] - fraud logits
            embedding: [batch_size, output_dim] - 128-dim embedding for fusion
        """
        batch_size = numerical_features.size(0)

        # Embed categorical features (use zeros for missing)
        embedded = []
        for name in self.categorical_names:
            if name in categorical_features:
                emb = self.embeddings[name](categorical_features[name])
            else:
                # Create zero embedding if feature is missing
                emb = torch.zeros(batch_size, 32, device=numerical_features.device)
            embedded.append(emb)

        # Process numerical features
        num_normed = self.numerical_bn(numerical_features)
        num_proj = self.numerical_proj(num_normed)
        embedded.append(num_proj)

        # Concatenate all embeddings
        combined = torch.cat(embedded, dim=-1)

        # MLP
        hidden = self.mlp(combined)

        # Output embedding
        embedding = self.output_proj(hidden)

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
# TRAINING FUNCTIONS
# ============================================================================
def load_data():
    """Load and prepare data."""
    print("=" * 60)
    print("LOADING DATA")
    print("=" * 60)

    # Load features
    features_path = DATA_DIR / "features.parquet"
    print(f"Loading features from: {features_path}")
    df = pd.read_parquet(features_path)
    print(f"  Shape: {df.shape}")

    # Load splits
    splits_path = DATA_DIR / "splits.pkl"
    with open(splits_path, "rb") as f:
        splits = pickle.load(f)

    # Load metadata
    metadata_path = DATA_DIR / "metadata.json"
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    # Load encoders
    encoders_path = DATA_DIR / "encoders.pkl"
    with open(encoders_path, "rb") as f:
        encoders = pickle.load(f)

    gc.collect()

    return df, splits, metadata, encoders


def prepare_datasets(df, splits, metadata, encoders):
    """Prepare train/val/test datasets."""
    print("\n" + "=" * 60)
    print("PREPARING DATASETS")
    print("=" * 60)

    # Get categorical columns
    categorical_cols = metadata["categorical_feature_names"]
    categorical_cardinalities = metadata["categorical_cardinalities"]

    # Get numerical columns (exclude categorical and target)
    target_col = "isFraud"
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    numeric_cols = [col for col in numeric_cols if col != target_col]

    # Encode categorical features
    categorical_data = {}
    for col in categorical_cols:
        if col in df.columns:
            # Convert to string and encode using LabelEncoder
            values = df[col].astype(str).values
            encoded = np.zeros(len(values), dtype=np.int64)

            if col in encoders:
                encoder = encoders[col]
                # Create mapping from class to index
                class_to_idx = {cls: idx for idx, cls in enumerate(encoder.classes_)}

                for i, v in enumerate(values):
                    if v in class_to_idx:
                        encoded[i] = class_to_idx[v] + 1  # +1 to leave 0 for padding
                    else:
                        encoded[i] = 1  # Unknown category

            categorical_data[col] = encoded

    # Get numerical features
    numerical_data = df[numeric_cols].values.astype(np.float32)

    # Handle NaN in numerical features
    numerical_data = np.nan_to_num(numerical_data, nan=0.0)

    # Get labels
    labels = df[target_col].values.astype(np.float32)

    # Split data
    train_idx = splits["train_idx"]
    val_idx = splits["val_idx"]
    test_idx = splits["test_idx"]

    # Create datasets
    def create_split_data(idx):
        num = numerical_data[idx]
        cat = {name: data[idx] for name, data in categorical_data.items()}
        lab = labels[idx]
        return num, cat, lab

    train_num, train_cat, train_labels = create_split_data(train_idx)
    val_num, val_cat, val_labels = create_split_data(val_idx)
    test_num, test_cat, test_labels = create_split_data(test_idx)

    # Create datasets
    train_dataset = TabularDataset(train_num, train_cat, train_labels)
    val_dataset = TabularDataset(val_num, val_cat, val_labels)
    test_dataset = TabularDataset(test_num, test_cat, test_labels)

    # Class weights for imbalanced data
    fraud_rate = train_labels.mean()
    pos_weight = (1 - fraud_rate) / fraud_rate

    print(f"\nDataset sizes:")
    print(
        f"  Train: {len(train_dataset):,} samples ({train_labels.sum():.0f} fraud, {fraud_rate * 100:.2f}%)"
    )
    print(f"  Val:   {len(val_dataset):,} samples ({val_labels.sum():.0f} fraud)")
    print(f"  Test:  {len(test_dataset):,} samples ({test_labels.sum():.0f} fraud)")
    print(f"\nCategorical features: {categorical_cols}")
    print(f"Categorical cardinalities: {categorical_cardinalities}")
    print(f"Numerical features: {len(numeric_cols)}")
    print(f"Class imbalance: pos_weight = {pos_weight:.2f}")

    return (
        train_dataset,
        val_dataset,
        test_dataset,
        categorical_cardinalities,
        len(numeric_cols),
        pos_weight,
    )


def train_epoch(model, dataloader, optimizer, criterion, device, epoch, total_epochs):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    all_logits = []
    all_labels = []

    for batch_idx, (numerical, categorical, labels) in enumerate(dataloader):
        numerical = numerical.to(device)
        categorical = {k: v.to(device) for k, v in categorical.items()}
        labels = labels.to(device)

        optimizer.zero_grad()

        logits, _ = model(numerical, categorical)
        logits = logits.squeeze(-1)

        loss = criterion(logits, labels)
        loss.backward()

        # Gradient clipping
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

        optimizer.step()

        total_loss += loss.item()
        all_logits.append(logits.detach().cpu())
        all_labels.append(labels.cpu())

        if batch_idx % 100 == 0:
            print(
                f"  Epoch {epoch + 1}/{total_epochs} | Batch {batch_idx}/{len(dataloader)} | Loss: {loss.item():.4f}"
            )

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
    all_embeddings = []

    for numerical, categorical, labels in dataloader:
        numerical = numerical.to(device)
        categorical = {k: v.to(device) for k, v in categorical.items()}
        labels = labels.to(device)

        logits, embeddings = model(numerical, categorical)
        logits = logits.squeeze(-1)

        loss = criterion(logits, labels)

        total_loss += loss.item()
        all_logits.append(logits.cpu())
        all_labels.append(labels.cpu())
        all_embeddings.append(embeddings.cpu())

    # Concatenate
    all_logits = torch.cat(all_logits)
    all_labels = torch.cat(all_labels)
    all_embeddings = torch.cat(all_embeddings)

    # Calculate metrics
    probs = torch.sigmoid(all_logits).numpy()
    preds = (probs >= 0.5).astype(int)
    labels_np = all_labels.numpy()

    auc_roc = roc_auc_score(labels_np, probs)
    auc_pr = average_precision_score(labels_np, probs)
    precision = precision_score(labels_np, preds, zero_division=0)
    recall = recall_score(labels_np, preds, zero_division=0)
    f1 = f1_score(labels_np, preds, zero_division=0)

    tn, fp, fn, tp = confusion_matrix(labels_np, preds).ravel()

    avg_loss = total_loss / len(dataloader)

    return {
        "loss": avg_loss,
        "auc_roc": auc_roc,
        "auc_pr": auc_pr,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
        "embeddings": all_embeddings,
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
    """Full training loop with early stopping."""
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
            model, train_loader, optimizer, criterion, device, epoch, epochs
        )

        # Validate
        val_metrics = evaluate(model, val_loader, criterion, device)

        # Update scheduler
        scheduler.step(val_metrics["auc_roc"])

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
                "val/precision": val_metrics["precision"],
                "val/recall": val_metrics["recall"],
                "learning_rate": optimizer.param_groups[0]["lr"],
                "epoch_time": epoch_time,
            }
        )

        print(f"\nEpoch {epoch + 1}/{epochs} Summary:")
        print(f"  Train Loss: {train_loss:.4f} | Train AUC: {train_auc:.4f}")
        print(
            f"  Val Loss:   {val_metrics['loss']:.4f} | Val AUC: {val_metrics['auc_roc']:.4f}"
        )
        print(f"  Val F1:     {val_metrics['f1']:.4f} | Time: {epoch_time:.1f}s")

        # Early stopping check
        if val_metrics["auc_roc"] > best_val_auc:
            best_val_auc = val_metrics["auc_roc"]
            best_model_state = model.state_dict().copy()
            patience_counter = 0
            print(f"  New best model! AUC: {best_val_auc:.4f}")
        else:
            patience_counter += 1
            print(f"  No improvement. Patience: {patience_counter}/{patience}")

            if patience_counter >= patience:
                print(f"\nEarly stopping at epoch {epoch + 1}")
                break

    # Load best model
    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    return model, best_val_auc


def save_model(model, metrics, categorical_cardinalities, num_numerical):
    """Save model checkpoint."""
    print("\n" + "=" * 60)
    print("SAVING MODEL")
    print("=" * 60)

    # Save model
    model_path = CHECKPOINT_DIR / "tabular_encoder.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "categorical_cardinalities": categorical_cardinalities,
            "num_numerical_features": num_numerical,
            "embedding_dim": EMBEDDING_DIM,
            "hidden_dims": HIDDEN_DIMS,
            "output_dim": OUTPUT_DIM,
            "dropout": DROPOUT,
        },
        model_path,
    )
    print(f"Model saved to: {model_path}")

    # Save metadata
    metadata = {
        "model_type": "tabular_encoder",
        "trained_at": datetime.now().isoformat(),
        "metrics": metrics,
        "hyperparameters": {
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "epochs": EPOCHS,
            "embedding_dim": EMBEDDING_DIM,
            "hidden_dims": HIDDEN_DIMS,
            "output_dim": OUTPUT_DIM,
            "dropout": DROPOUT,
        },
    }

    metadata_path = CHECKPOINT_DIR / "tabular_encoder_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")

    # Log artifact to WandB
    artifact = wandb.Artifact(
        name="tabular-encoder",
        type="model",
        description="Tabular Encoder (Branch 1) for fraud detection",
    )
    artifact.add_file(str(model_path))
    artifact.add_file(str(metadata_path))
    wandb.log_artifact(artifact)

    return model_path


def main():
    """Main training pipeline."""
    print("\n" + "=" * 60)
    print("SENTINEL FRAUD DETECTION - TABULAR ENCODER TRAINING")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize WandB
    wandb.init(
        project="sentinel-fraud",
        name=f"tabular-encoder-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        tags=["tabular", "encoder", "branch1", "phase2"],
        config={
            "model_type": "tabular_encoder",
            "batch_size": BATCH_SIZE,
            "learning_rate": LEARNING_RATE,
            "epochs": EPOCHS,
            "embedding_dim": EMBEDDING_DIM,
            "hidden_dims": HIDDEN_DIMS,
            "output_dim": OUTPUT_DIM,
            "dropout": DROPOUT,
            "device": str(DEVICE),
        },
    )

    print(f"\n{'*' * 60}")
    print(f"WANDB RUN URL: {wandb.run.url}")
    print(f"^^ TRACK THIS RUN AT THE URL ABOVE ^^")
    print(f"{'*' * 60}")

    try:
        # Load data
        df, splits, metadata, encoders = load_data()

        # Prepare datasets
        (
            train_dataset,
            val_dataset,
            test_dataset,
            categorical_cardinalities,
            num_numerical,
            pos_weight,
        ) = prepare_datasets(df, splits, metadata, encoders)

        # Free memory
        del df
        gc.collect()

        # Create dataloaders
        train_loader = DataLoader(
            train_dataset,
            batch_size=BATCH_SIZE,
            shuffle=True,
            collate_fn=collate_fn,
            num_workers=2,
            pin_memory=True,
        )
        val_loader = DataLoader(
            val_dataset,
            batch_size=BATCH_SIZE,
            shuffle=False,
            collate_fn=collate_fn,
            num_workers=2,
            pin_memory=True,
        )
        test_loader = DataLoader(
            test_dataset,
            batch_size=BATCH_SIZE,
            shuffle=False,
            collate_fn=collate_fn,
            num_workers=2,
            pin_memory=True,
        )

        # Create model
        model = TabularEncoder(
            categorical_cardinalities=categorical_cardinalities,
            num_numerical_features=num_numerical,
            embedding_dim=EMBEDDING_DIM,
            hidden_dims=HIDDEN_DIMS,
            output_dim=OUTPUT_DIM,
            dropout=DROPOUT,
        ).to(DEVICE)

        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
        print(
            f"\nModel Parameters: {total_params:,} total, {trainable_params:,} trainable"
        )
        wandb.config.update(
            {"total_params": total_params, "trainable_params": trainable_params}
        )

        # Loss, optimizer, scheduler
        criterion = FocalLoss(alpha=0.25, gamma=2.0)
        optimizer = torch.optim.AdamW(
            model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
        )
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="max", factor=0.5, patience=3
        )

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

        # Final evaluation on test set
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
                "test/loss": test_metrics["loss"],
                "test/auc_roc": test_metrics["auc_roc"],
                "test/auc_pr": test_metrics["auc_pr"],
                "test/f1": test_metrics["f1"],
                "test/precision": test_metrics["precision"],
                "test/recall": test_metrics["recall"],
                "test/tn": test_metrics["tn"],
                "test/fp": test_metrics["fp"],
                "test/fn": test_metrics["fn"],
                "test/tp": test_metrics["tp"],
            }
        )

        # Save model
        metrics_to_save = {
            "val_auc_roc": best_val_auc,
            "test_auc_roc": test_metrics["auc_roc"],
            "test_auc_pr": test_metrics["auc_pr"],
            "test_f1": test_metrics["f1"],
        }
        save_model(model, metrics_to_save, categorical_cardinalities, num_numerical)

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
        wandb.alert(title="Tabular Encoder Training Failed", text=str(e))
        raise

    finally:
        wandb.finish()


if __name__ == "__main__":
    main()

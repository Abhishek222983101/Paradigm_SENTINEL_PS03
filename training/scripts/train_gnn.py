"""
SENTINEL FRAUD DETECTION - GRAPH ATTENTION NETWORK TRAINING
============================================================
Model: Graph Attention Network (GAT) - 3 layers, 4 heads
Type: TRAIN FROM SCRATCH
Input: graph.pt (15,732 nodes, 367,990 edges, 64-dim features)
Target: Node-level fraud labels
Output: 128-dim embedding for fusion
Expected Time: 45-90 minutes on GPU

Branch 3 of our Multi-Modal Fusion model.
Detects FRAUD RINGS:
- Accounts sharing same device/IP
- Coordinated fraud clusters
- Network-based risk propagation

WandB Run: sentinel-fraud/graph-gat
"""

import os
import sys
import gc
import json
import pickle
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch_geometric.data import Data
from torch_geometric.nn import GATConv
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
LEARNING_RATE = 0.001
EPOCHS = 100
WEIGHT_DECAY = 5e-4
PATIENCE = 15

# Model Architecture
INPUT_DIM = 64  # From graph.pt node features
HIDDEN_DIM = 128
OUTPUT_DIM = 128
NUM_LAYERS = 3
NUM_HEADS = 4
DROPOUT = 0.2


# ============================================================================
# GRAPH ATTENTION NETWORK MODEL
# ============================================================================
class GraphEncoder(nn.Module):
    """
    Graph Attention Network for fraud ring detection.

    Uses multi-head attention to learn:
    - Which neighbors are important for classification
    - How fraud propagates through network connections
    - Device/IP sharing patterns that indicate fraud rings
    """

    def __init__(
        self,
        input_dim: int = 64,
        hidden_dim: int = 128,
        output_dim: int = 128,
        num_layers: int = 3,
        num_heads: int = 4,
        dropout: float = 0.2,
    ):
        super().__init__()

        self.num_layers = num_layers

        # Input projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)

        # GAT layers
        self.gat_layers = nn.ModuleList()
        self.norms = nn.ModuleList()

        for i in range(num_layers):
            in_dim = hidden_dim if i == 0 else hidden_dim * num_heads
            out_dim = hidden_dim

            # Last layer: concat=False (average heads)
            concat = i < num_layers - 1

            self.gat_layers.append(
                GATConv(
                    in_channels=in_dim,
                    out_channels=out_dim,
                    heads=num_heads,
                    concat=concat,
                    dropout=dropout,
                    add_self_loops=True,
                )
            )

            norm_dim = hidden_dim * num_heads if concat else hidden_dim
            self.norms.append(nn.LayerNorm(norm_dim))

        self.dropout = nn.Dropout(dropout)

        # Output projection
        self.output_proj = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, output_dim),
        )

        # Classification head (for training)
        self.classifier = nn.Linear(output_dim, 1)

    def forward(
        self,
        x: torch.Tensor,  # [num_nodes, input_dim]
        edge_index: torch.Tensor,  # [2, num_edges]
        return_embedding: bool = False,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass.

        Returns:
            logits: [num_nodes, 1] - fraud logits for each node
            embedding: [num_nodes, output_dim] - embeddings for fusion
        """
        # Input projection
        h = self.input_proj(x)

        # GAT layers with residual connections
        for i, (gat, norm) in enumerate(zip(self.gat_layers, self.norms)):
            h_prev = h
            h = gat(h, edge_index)
            h = norm(h)
            h = F.relu(h)
            h = self.dropout(h)

            # Residual connection (when dimensions match)
            if h.shape == h_prev.shape:
                h = h + h_prev

        # Output embedding
        embedding = self.output_proj(h)

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
# DATA LOADING
# ============================================================================
def load_graph_data():
    """Load graph data."""
    print("=" * 60)
    print("LOADING GRAPH DATA")
    print("=" * 60)

    # Load graph
    graph_path = DATA_DIR / "graph.pt"
    print(f"Loading graph from: {graph_path}")
    graph_data = torch.load(graph_path, weights_only=False)

    print(f"  Node features shape: {graph_data.x.shape}")
    print(f"  Edge index shape: {graph_data.edge_index.shape}")
    print(f"  Number of nodes: {graph_data.x.shape[0]}")
    print(f"  Number of edges: {graph_data.edge_index.shape[1]}")

    # Get labels
    node_labels = (
        graph_data.y if hasattr(graph_data, "y") and graph_data.y is not None else None
    )
    if node_labels is not None:
        print(f"  Node labels shape: {node_labels.shape}")
        print(f"  Fraud rate: {node_labels.float().mean().item() * 100:.2f}%")

    # Get train/val/test masks
    train_mask = (
        graph_data.train_mask
        if hasattr(graph_data, "train_mask") and graph_data.train_mask is not None
        else None
    )
    val_mask = (
        graph_data.val_mask
        if hasattr(graph_data, "val_mask") and graph_data.val_mask is not None
        else None
    )
    test_mask = (
        graph_data.test_mask
        if hasattr(graph_data, "test_mask") and graph_data.test_mask is not None
        else None
    )

    if train_mask is not None:
        print(f"\nSplit sizes:")
        print(f"  Train: {train_mask.sum().item()}")
        print(f"  Val: {val_mask.sum().item()}")
        print(f"  Test: {test_mask.sum().item()}")

    return graph_data


def prepare_data(graph_data):
    """Prepare PyG Data object."""
    print("\n" + "=" * 60)
    print("PREPARING DATA")
    print("=" * 60)

    # Convert to tensors
    x = graph_data.x
    if not isinstance(x, torch.Tensor):
        x = torch.tensor(x, dtype=torch.float32)

    edge_index = graph_data.edge_index
    if not isinstance(edge_index, torch.Tensor):
        edge_index = torch.tensor(edge_index, dtype=torch.long)

    # Get labels
    y = (
        graph_data.y
        if hasattr(graph_data, "y") and graph_data.y is not None
        else torch.zeros(x.shape[0])
    )
    if not isinstance(y, torch.Tensor):
        y = torch.tensor(y, dtype=torch.float32)
    elif y.dtype == torch.long:
        y = y.float()

    # Get masks (create if not present)
    num_nodes = x.shape[0]

    if hasattr(graph_data, "train_mask") and graph_data.train_mask is not None:
        train_mask = graph_data.train_mask
        val_mask = graph_data.val_mask
        test_mask = graph_data.test_mask

        if not isinstance(train_mask, torch.Tensor):
            train_mask = torch.tensor(train_mask, dtype=torch.bool)
            val_mask = torch.tensor(val_mask, dtype=torch.bool)
            test_mask = torch.tensor(test_mask, dtype=torch.bool)
    else:
        # Create masks (80/10/10 split)
        perm = torch.randperm(num_nodes)
        train_size = int(0.8 * num_nodes)
        val_size = int(0.1 * num_nodes)

        train_mask = torch.zeros(num_nodes, dtype=torch.bool)
        val_mask = torch.zeros(num_nodes, dtype=torch.bool)
        test_mask = torch.zeros(num_nodes, dtype=torch.bool)

        train_mask[perm[:train_size]] = True
        val_mask[perm[train_size : train_size + val_size]] = True
        test_mask[perm[train_size + val_size :]] = True

    # Print stats
    print(f"Node features: {x.shape}")
    print(f"Edge index: {edge_index.shape}")
    print(f"Labels: {y.shape}")
    print(f"Train mask: {train_mask.sum().item()} nodes")
    print(f"Val mask: {val_mask.sum().item()} nodes")
    print(f"Test mask: {test_mask.sum().item()} nodes")

    # Create PyG Data object
    data = Data(
        x=x,
        edge_index=edge_index,
        y=y,
        train_mask=train_mask,
        val_mask=val_mask,
        test_mask=test_mask,
    )

    return data


# ============================================================================
# TRAINING FUNCTIONS
# ============================================================================
def train_epoch(model, data, optimizer, criterion, device):
    """Train for one epoch (full-batch on graph)."""
    model.train()

    data = data.to(device)
    optimizer.zero_grad()

    logits, _ = model(data.x, data.edge_index)
    logits = logits.squeeze(-1)

    # Only compute loss on training nodes
    loss = criterion(logits[data.train_mask], data.y[data.train_mask])
    loss.backward()

    # Gradient clipping
    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)

    optimizer.step()

    # Calculate training AUC
    with torch.no_grad():
        probs = torch.sigmoid(logits[data.train_mask]).cpu().numpy()
        labels = data.y[data.train_mask].cpu().numpy()

        if len(np.unique(labels)) > 1:
            auc = roc_auc_score(labels, probs)
        else:
            auc = 0.5

    return loss.item(), auc


@torch.no_grad()
def evaluate(model, data, criterion, device, mask_name="val"):
    """Evaluate model on a specific split."""
    model.eval()

    data = data.to(device)

    logits, embeddings = model(data.x, data.edge_index)
    logits = logits.squeeze(-1)

    # Get mask
    if mask_name == "val":
        mask = data.val_mask
    elif mask_name == "test":
        mask = data.test_mask
    else:
        mask = data.train_mask

    # Compute loss
    loss = criterion(logits[mask], data.y[mask]).item()

    # Calculate metrics
    probs = torch.sigmoid(logits[mask]).cpu().numpy()
    preds = (probs >= 0.5).astype(int)
    labels = data.y[mask].cpu().numpy()

    if len(np.unique(labels)) > 1:
        auc_roc = roc_auc_score(labels, probs)
        auc_pr = average_precision_score(labels, probs)
    else:
        auc_roc = 0.5
        auc_pr = 0.5

    precision = precision_score(labels, preds, zero_division=0)
    recall = recall_score(labels, preds, zero_division=0)
    f1 = f1_score(labels, preds, zero_division=0)

    if len(preds) > 0 and len(np.unique(preds)) > 1:
        tn, fp, fn, tp = confusion_matrix(labels, preds).ravel()
    else:
        tn, fp, fn, tp = 0, 0, 0, 0

    return {
        "loss": loss,
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


def train_model(model, data, optimizer, scheduler, criterion, device, epochs, patience):
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
        train_loss, train_auc = train_epoch(model, data, optimizer, criterion, device)

        # Validate
        val_metrics = evaluate(model, data, criterion, device, "val")

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
                "learning_rate": optimizer.param_groups[0]["lr"],
                "epoch_time": epoch_time,
            }
        )

        if epoch % 10 == 0:
            print(f"\nEpoch {epoch + 1}/{epochs}:")
            print(f"  Train Loss: {train_loss:.4f} | Train AUC: {train_auc:.4f}")
            print(
                f"  Val Loss:   {val_metrics['loss']:.4f} | Val AUC: {val_metrics['auc_roc']:.4f}"
            )

        # Early stopping
        if val_metrics["auc_roc"] > best_val_auc:
            best_val_auc = val_metrics["auc_roc"]
            best_model_state = model.state_dict().copy()
            patience_counter = 0

            if epoch % 10 == 0:
                print(f"  New best model! AUC: {best_val_auc:.4f}")
        else:
            patience_counter += 1

            if patience_counter >= patience:
                print(f"\nEarly stopping at epoch {epoch + 1}")
                break

    if best_model_state is not None:
        model.load_state_dict(best_model_state)

    return model, best_val_auc


def save_model(model, metrics, config):
    """Save final model."""
    print("\n" + "=" * 60)
    print("SAVING MODEL")
    print("=" * 60)

    model_path = CHECKPOINT_DIR / "graph_model.pt"
    torch.save({"model_state_dict": model.state_dict(), "config": config}, model_path)
    print(f"Model saved to: {model_path}")

    # Save metadata
    metadata = {
        "model_type": "graph_attention_network",
        "trained_at": datetime.now().isoformat(),
        "metrics": metrics,
        "config": config,
    }

    metadata_path = CHECKPOINT_DIR / "graph_model_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")

    # Log artifact
    artifact = wandb.Artifact(
        name="graph-gat",
        type="model",
        description="Graph Attention Network (Branch 3) for fraud detection",
    )
    artifact.add_file(str(model_path))
    artifact.add_file(str(metadata_path))
    wandb.log_artifact(artifact)

    return model_path


def main():
    """Main training pipeline."""
    print("\n" + "=" * 60)
    print("SENTINEL FRAUD DETECTION - GRAPH ATTENTION NETWORK TRAINING")
    print("=" * 60)
    print(f"Device: {DEVICE}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Config
    config = {
        "input_dim": INPUT_DIM,
        "hidden_dim": HIDDEN_DIM,
        "output_dim": OUTPUT_DIM,
        "num_layers": NUM_LAYERS,
        "num_heads": NUM_HEADS,
        "dropout": DROPOUT,
    }

    # Initialize WandB
    wandb.init(
        project="sentinel-fraud",
        name=f"graph-gat-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        tags=["gat", "graph", "branch3", "phase2"],
        config={
            "model_type": "graph_attention_network",
            "learning_rate": LEARNING_RATE,
            "epochs": EPOCHS,
            **config,
            "device": str(DEVICE),
        },
    )

    print(f"\n{'*' * 60}")
    print(f"WANDB RUN URL: {wandb.run.url}")
    print(f"^^ TRACK THIS RUN AT THE URL ABOVE ^^")
    print(f"{'*' * 60}")

    try:
        # Load data
        graph_data = load_graph_data()

        # Prepare PyG data
        data = prepare_data(graph_data)

        # Free memory
        del graph_data
        gc.collect()

        # Create model
        model = GraphEncoder(
            input_dim=data.x.shape[1],  # Use actual input dim
            hidden_dim=HIDDEN_DIM,
            output_dim=OUTPUT_DIM,
            num_layers=NUM_LAYERS,
            num_heads=NUM_HEADS,
            dropout=DROPOUT,
        ).to(DEVICE)

        # Update config with actual input dim
        config["input_dim"] = data.x.shape[1]

        # Count parameters
        total_params = sum(p.numel() for p in model.parameters())
        print(f"\nModel Parameters: {total_params:,}")
        wandb.config.update({"total_params": total_params})

        # Loss and optimizer
        criterion = FocalLoss(alpha=0.25, gamma=2.0)
        optimizer = torch.optim.AdamW(
            model.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY
        )
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="max", factor=0.5, patience=5
        )

        # Train
        model, best_val_auc = train_model(
            model, data, optimizer, scheduler, criterion, DEVICE, EPOCHS, PATIENCE
        )

        # Final evaluation
        print("\n" + "=" * 60)
        print("FINAL EVALUATION ON TEST SET")
        print("=" * 60)

        test_metrics = evaluate(model, data, criterion, DEVICE, "test")

        print(f"\nTest Metrics:")
        print(f"  AUC-ROC:   {test_metrics['auc_roc']:.4f}")
        print(f"  AUC-PR:    {test_metrics['auc_pr']:.4f}")
        print(f"  F1:        {test_metrics['f1']:.4f}")
        print(f"  Precision: {test_metrics['precision']:.4f}")
        print(f"  Recall:    {test_metrics['recall']:.4f}")

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
        save_model(model, metrics_to_save, config)

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
        wandb.alert(title="GAT Training Failed", text=str(e))
        raise

    finally:
        wandb.finish()


if __name__ == "__main__":
    main()

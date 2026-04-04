#!/usr/bin/env python3
"""
SENTINEL FRAUD DETECTION - TRANSACTION GRAPH BUILDER
=====================================================
Sub-Phase 1.4: Build PyTorch Geometric graph from transaction data.

Graph Structure:
- Nodes: Users (card1), Devices (DeviceInfo), IPs (addr1)
- Edges: User→Device (uses), User→IP (from), Device→User (shared)
- Node features: Aggregated transaction statistics
- Edge features: Transaction characteristics

This graph enables:
1. Fraud ring detection (shared devices/IPs)
2. Network-based risk propagation
3. Community detection

Usage:
    from graph_builder import TransactionGraphBuilder
    builder = TransactionGraphBuilder()
    graph = builder.build_graph(features_df)

Author: Sentinel Team - Phase 1
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict
import pickle

import torch
from torch_geometric.data import Data


# =============================================================================
# CONFIGURATION
# =============================================================================
NODE_TYPES = {
    "user": 0,  # card1 - user accounts
    "device": 1,  # DeviceInfo - device fingerprints
    "ip": 2,  # addr1 - IP/location identifiers
    "email": 3,  # P_emaildomain - email providers
}

EDGE_TYPES = {
    "user_uses_device": 0,
    "user_from_ip": 1,
    "user_uses_email": 2,
    "device_shared": 3,  # Device shared between users
    "ip_shared": 4,  # IP shared between users
}


# =============================================================================
# TRANSACTION GRAPH BUILDER
# =============================================================================
class TransactionGraphBuilder:
    """
    Builds a heterogeneous transaction graph for GNN training.

    The graph captures relationships between:
    - Users (identified by card1)
    - Devices (identified by DeviceInfo)
    - IPs/Locations (identified by addr1)
    - Email domains (identified by P_emaildomain)

    These relationships are crucial for detecting:
    - Fraud rings (multiple accounts on same device)
    - Account takeovers (new device for existing user)
    - Synthetic identities (unusual network patterns)
    """

    def __init__(
        self,
        node_feature_dim: int = 64,
        min_connections: int = 1,
        max_nodes_per_type: Optional[int] = None,
    ):
        """
        Initialize the graph builder.

        Args:
            node_feature_dim: Dimension of node feature vectors
            min_connections: Minimum connections for a node to be included
            max_nodes_per_type: Maximum nodes per type (for memory efficiency)
        """
        self.node_feature_dim = node_feature_dim
        self.min_connections = min_connections
        self.max_nodes_per_type = max_nodes_per_type

        # Node mappings (ID -> index)
        self.user_to_idx = {}
        self.device_to_idx = {}
        self.ip_to_idx = {}
        self.email_to_idx = {}

        # Reverse mappings (index -> ID)
        self.idx_to_user = {}
        self.idx_to_device = {}
        self.idx_to_ip = {}
        self.idx_to_email = {}

    def build_graph(
        self,
        df: pd.DataFrame,
        fraud_labels: Optional[np.ndarray] = None,
        verbose: bool = True,
    ) -> Data:
        """
        Build PyTorch Geometric Data object from DataFrame.

        Args:
            df: DataFrame with columns: card1, DeviceInfo, addr1, P_emaildomain, TransactionAmt, isFraud
            fraud_labels: Optional pre-computed fraud labels
            verbose: Print progress

        Returns:
            PyTorch Geometric Data object
        """
        if verbose:
            print("\n" + "=" * 70)
            print("BUILDING TRANSACTION GRAPH")
            print("=" * 70)

        # =====================================================================
        # STEP 1: CREATE NODE MAPPINGS
        # =====================================================================
        if verbose:
            print("\n[1/5] Creating node mappings...")

        self._create_node_mappings(df)

        n_users = len(self.user_to_idx)
        n_devices = len(self.device_to_idx)
        n_ips = len(self.ip_to_idx)
        n_emails = len(self.email_to_idx)
        n_total = n_users + n_devices + n_ips + n_emails

        if verbose:
            print(f"  Users: {n_users:,}")
            print(f"  Devices: {n_devices:,}")
            print(f"  IPs: {n_ips:,}")
            print(f"  Emails: {n_emails:,}")
            print(f"  Total nodes: {n_total:,}")

        # =====================================================================
        # STEP 2: CREATE EDGES
        # =====================================================================
        if verbose:
            print("\n[2/5] Creating edges...")

        edges, edge_attrs = self._create_edges(df)

        if verbose:
            print(f"  Total edges: {len(edges[0]):,}")

        # =====================================================================
        # STEP 3: CREATE NODE FEATURES
        # =====================================================================
        if verbose:
            print("\n[3/5] Computing node features...")

        node_features = self._compute_node_features(df, n_total)

        if verbose:
            print(f"  Feature shape: {node_features.shape}")

        # =====================================================================
        # STEP 4: CREATE NODE LABELS
        # =====================================================================
        if verbose:
            print("\n[4/5] Creating node labels...")

        node_labels = self._compute_node_labels(df, n_total, fraud_labels)

        if verbose:
            fraud_count = (node_labels > 0).sum()
            print(
                f"  Fraud nodes: {fraud_count:,} ({fraud_count / n_total * 100:.2f}%)"
            )

        # =====================================================================
        # STEP 5: CREATE TRAIN/VAL/TEST MASKS
        # =====================================================================
        if verbose:
            print("\n[5/5] Creating masks...")

        train_mask, val_mask, test_mask = self._create_masks(n_total, n_users)

        if verbose:
            print(f"  Train nodes: {train_mask.sum():,}")
            print(f"  Val nodes: {val_mask.sum():,}")
            print(f"  Test nodes: {test_mask.sum():,}")

        # =====================================================================
        # CREATE PyG DATA OBJECT
        # =====================================================================
        edge_index = torch.tensor(edges, dtype=torch.long)
        x = torch.tensor(node_features, dtype=torch.float32)
        y = torch.tensor(node_labels, dtype=torch.long)
        edge_attr = (
            torch.tensor(edge_attrs, dtype=torch.float32) if edge_attrs else None
        )

        data = Data(
            x=x,
            edge_index=edge_index,
            edge_attr=edge_attr,
            y=y,
            train_mask=torch.tensor(train_mask, dtype=torch.bool),
            val_mask=torch.tensor(val_mask, dtype=torch.bool),
            test_mask=torch.tensor(test_mask, dtype=torch.bool),
            num_users=n_users,
            num_devices=n_devices,
            num_ips=n_ips,
            num_emails=n_emails,
        )

        if verbose:
            print("\n[GRAPH BUILD COMPLETE]")
            print(f"  Nodes: {data.num_nodes:,}")
            print(f"  Edges: {data.num_edges:,}")
            print(f"  Node features: {data.x.shape}")
            print(
                f"  Memory: {(data.x.numel() * 4 + data.edge_index.numel() * 8) / 1024**2:.1f} MB"
            )

        return data

    def _create_node_mappings(self, df: pd.DataFrame) -> None:
        """Create mappings from entity IDs to node indices."""

        # Reset mappings
        self.user_to_idx = {}
        self.device_to_idx = {}
        self.ip_to_idx = {}
        self.email_to_idx = {}

        offset = 0

        # Users (card1)
        users = df["card1"].dropna().unique()
        if self.max_nodes_per_type:
            users = users[: self.max_nodes_per_type]
        for i, user in enumerate(users):
            self.user_to_idx[user] = offset + i
            self.idx_to_user[offset + i] = user
        offset += len(users)

        # Devices (DeviceInfo)
        if "DeviceInfo" in df.columns:
            devices = df["DeviceInfo"].dropna().unique()
            if self.max_nodes_per_type:
                devices = devices[: self.max_nodes_per_type]
            for i, device in enumerate(devices):
                self.device_to_idx[device] = offset + i
                self.idx_to_device[offset + i] = device
            offset += len(devices)

        # IPs (addr1)
        if "addr1" in df.columns:
            ips = df["addr1"].dropna().unique()
            if self.max_nodes_per_type:
                ips = ips[: self.max_nodes_per_type]
            for i, ip in enumerate(ips):
                self.ip_to_idx[ip] = offset + i
                self.idx_to_ip[offset + i] = ip
            offset += len(ips)

        # Emails (P_emaildomain)
        if "P_emaildomain" in df.columns:
            emails = df["P_emaildomain"].dropna().unique()
            if self.max_nodes_per_type:
                emails = emails[: self.max_nodes_per_type]
            for i, email in enumerate(emails):
                self.email_to_idx[email] = offset + i
                self.idx_to_email[offset + i] = email

    def _create_edges(
        self, df: pd.DataFrame
    ) -> Tuple[List[List[int]], Optional[List[List[float]]]]:
        """Create edge list from transactions using vectorized operations."""

        src_nodes = []
        dst_nodes = []

        # Track connections for shared device/IP edges
        device_users = defaultdict(set)
        ip_users = defaultdict(set)

        # Vectorized edge creation using groupby
        # User → Device edges
        if "DeviceInfo" in df.columns and len(self.device_to_idx) > 0:
            user_device = df[["card1", "DeviceInfo"]].dropna().drop_duplicates()
            for _, row in user_device.iterrows():
                user = row["card1"]
                device = row["DeviceInfo"]
                if user in self.user_to_idx and device in self.device_to_idx:
                    user_idx = self.user_to_idx[user]
                    device_idx = self.device_to_idx[device]
                    src_nodes.extend([user_idx, device_idx])
                    dst_nodes.extend([device_idx, user_idx])
                    device_users[device].add(user_idx)

        # User → IP edges
        if "addr1" in df.columns and len(self.ip_to_idx) > 0:
            user_ip = df[["card1", "addr1"]].dropna().drop_duplicates()
            for _, row in user_ip.iterrows():
                user = row["card1"]
                ip = row["addr1"]
                if user in self.user_to_idx and ip in self.ip_to_idx:
                    user_idx = self.user_to_idx[user]
                    ip_idx = self.ip_to_idx[ip]
                    src_nodes.extend([user_idx, ip_idx])
                    dst_nodes.extend([ip_idx, user_idx])
                    ip_users[ip].add(user_idx)

        # User → Email edges
        if "P_emaildomain" in df.columns and len(self.email_to_idx) > 0:
            user_email = df[["card1", "P_emaildomain"]].dropna().drop_duplicates()
            for _, row in user_email.iterrows():
                user = row["card1"]
                email = row["P_emaildomain"]
                if user in self.user_to_idx and email in self.email_to_idx:
                    user_idx = self.user_to_idx[user]
                    email_idx = self.email_to_idx[email]
                    src_nodes.extend([user_idx, email_idx])
                    dst_nodes.extend([email_idx, user_idx])

        # Add shared device edges (users sharing same device) - limit to avoid explosion
        for device, users in device_users.items():
            users = list(users)
            if len(users) > 100:  # Limit shared edges to avoid memory explosion
                users = users[:100]
            for i in range(len(users)):
                for j in range(i + 1, min(len(users), i + 10)):  # Limit connections
                    src_nodes.extend([users[i], users[j]])
                    dst_nodes.extend([users[j], users[i]])

        # Add shared IP edges (users from same IP) - limit to avoid explosion
        for ip, users in ip_users.items():
            users = list(users)
            if len(users) > 100:  # Limit shared edges
                users = users[:100]
            for i in range(len(users)):
                for j in range(i + 1, min(len(users), i + 10)):  # Limit connections
                    src_nodes.extend([users[i], users[j]])
                    dst_nodes.extend([users[j], users[i]])

        # Remove duplicates
        edge_set = set(zip(src_nodes, dst_nodes))
        edges = [list(x) for x in zip(*edge_set)] if edge_set else [[], []]

        return edges, None

    def _compute_node_features(self, df: pd.DataFrame, n_nodes: int) -> np.ndarray:
        """
        Compute feature vectors for each node.

        For users: Transaction statistics (count, avg amount, std, etc.)
        For devices/IPs/emails: Usage statistics
        """

        features = np.zeros((n_nodes, self.node_feature_dim), dtype=np.float32)

        # User features (first N nodes)
        user_stats = df.groupby("card1").agg(
            {
                "TransactionAmt": ["count", "mean", "std", "min", "max", "sum"],
                "isFraud": ["mean", "sum"],
            }
        )
        user_stats.columns = [
            "txn_count",
            "txn_mean",
            "txn_std",
            "txn_min",
            "txn_max",
            "txn_sum",
            "fraud_rate",
            "fraud_count",
        ]
        user_stats = user_stats.fillna(0)

        for user, idx in self.user_to_idx.items():
            if user in user_stats.index:
                stats = user_stats.loc[user]
                # Normalize and assign to first 8 feature dimensions
                features[idx, 0] = np.log1p(stats["txn_count"])
                features[idx, 1] = np.log1p(stats["txn_mean"])
                features[idx, 2] = (
                    np.log1p(stats["txn_std"]) if stats["txn_std"] > 0 else 0
                )
                features[idx, 3] = np.log1p(stats["txn_min"])
                features[idx, 4] = np.log1p(stats["txn_max"])
                features[idx, 5] = np.log1p(stats["txn_sum"])
                features[idx, 6] = stats["fraud_rate"]
                features[idx, 7] = np.log1p(stats["fraud_count"])

        # Device features
        if "DeviceInfo" in df.columns:
            device_stats = df.groupby("DeviceInfo").agg(
                {
                    "card1": "nunique",  # Number of unique users
                    "TransactionAmt": "mean",
                    "isFraud": "mean",
                }
            )
            device_stats.columns = ["user_count", "avg_amt", "fraud_rate"]
            device_stats = device_stats.fillna(0)

            for device, idx in self.device_to_idx.items():
                if device in device_stats.index:
                    stats = device_stats.loc[device]
                    features[idx, 0] = np.log1p(stats["user_count"])
                    features[idx, 1] = np.log1p(stats["avg_amt"])
                    features[idx, 2] = stats["fraud_rate"]

        # IP features
        if "addr1" in df.columns:
            ip_stats = df.groupby("addr1").agg(
                {
                    "card1": "nunique",
                    "TransactionAmt": "mean",
                    "isFraud": "mean",
                }
            )
            ip_stats.columns = ["user_count", "avg_amt", "fraud_rate"]
            ip_stats = ip_stats.fillna(0)

            for ip, idx in self.ip_to_idx.items():
                if ip in ip_stats.index:
                    stats = ip_stats.loc[ip]
                    features[idx, 0] = np.log1p(stats["user_count"])
                    features[idx, 1] = np.log1p(stats["avg_amt"])
                    features[idx, 2] = stats["fraud_rate"]

        # Email features
        if "P_emaildomain" in df.columns:
            email_stats = df.groupby("P_emaildomain").agg(
                {
                    "card1": "nunique",
                    "TransactionAmt": "mean",
                    "isFraud": "mean",
                }
            )
            email_stats.columns = ["user_count", "avg_amt", "fraud_rate"]
            email_stats = email_stats.fillna(0)

            for email, idx in self.email_to_idx.items():
                if email in email_stats.index:
                    stats = email_stats.loc[email]
                    features[idx, 0] = np.log1p(stats["user_count"])
                    features[idx, 1] = np.log1p(stats["avg_amt"])
                    features[idx, 2] = stats["fraud_rate"]

        # Add node type encoding (one-hot in last 4 dimensions)
        n_users = len(self.user_to_idx)
        n_devices = len(self.device_to_idx)
        n_ips = len(self.ip_to_idx)
        n_emails = len(self.email_to_idx)

        # User type
        features[:n_users, -4] = 1.0
        # Device type
        features[n_users : n_users + n_devices, -3] = 1.0
        # IP type
        features[n_users + n_devices : n_users + n_devices + n_ips, -2] = 1.0
        # Email type
        features[n_users + n_devices + n_ips :, -1] = 1.0

        return features

    def _compute_node_labels(
        self, df: pd.DataFrame, n_nodes: int, fraud_labels: Optional[np.ndarray] = None
    ) -> np.ndarray:
        """
        Compute fraud labels for nodes.

        For users: Max fraud label across all transactions
        For devices/IPs/emails: 1 if any associated user is fraudulent
        """

        labels = np.zeros(n_nodes, dtype=np.int64)

        # User fraud labels
        user_fraud = df.groupby("card1")["isFraud"].max()
        for user, idx in self.user_to_idx.items():
            if user in user_fraud.index:
                labels[idx] = int(user_fraud.loc[user])

        # Device labels (1 if any user is fraud)
        if "DeviceInfo" in df.columns:
            device_fraud = df.groupby("DeviceInfo")["isFraud"].max()
            for device, idx in self.device_to_idx.items():
                if device in device_fraud.index:
                    labels[idx] = int(device_fraud.loc[device])

        # IP labels
        if "addr1" in df.columns:
            ip_fraud = df.groupby("addr1")["isFraud"].max()
            for ip, idx in self.ip_to_idx.items():
                if ip in ip_fraud.index:
                    labels[idx] = int(ip_fraud.loc[ip])

        # Email labels
        if "P_emaildomain" in df.columns:
            email_fraud = df.groupby("P_emaildomain")["isFraud"].max()
            for email, idx in self.email_to_idx.items():
                if email in email_fraud.index:
                    labels[idx] = int(email_fraud.loc[email])

        return labels

    def _create_masks(
        self,
        n_nodes: int,
        n_users: int,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Create train/val/test masks for nodes."""

        train_mask = np.zeros(n_nodes, dtype=bool)
        val_mask = np.zeros(n_nodes, dtype=bool)
        test_mask = np.zeros(n_nodes, dtype=bool)

        # Only mask user nodes (we predict fraud for users)
        user_indices = np.arange(n_users)
        np.random.shuffle(user_indices)

        n_train = int(n_users * train_ratio)
        n_val = int(n_users * val_ratio)

        train_mask[user_indices[:n_train]] = True
        val_mask[user_indices[n_train : n_train + n_val]] = True
        test_mask[user_indices[n_train + n_val :]] = True

        return train_mask, val_mask, test_mask

    def save_graph(self, graph: Data, path: Path) -> None:
        """Save graph to disk."""
        torch.save(graph, path)
        print(f"Graph saved to: {path}")

    def save_mappings(self, path: Path) -> None:
        """Save node ID mappings to disk."""
        mappings = {
            "user_to_idx": self.user_to_idx,
            "device_to_idx": self.device_to_idx,
            "ip_to_idx": self.ip_to_idx,
            "email_to_idx": self.email_to_idx,
            "idx_to_user": self.idx_to_user,
            "idx_to_device": self.idx_to_device,
            "idx_to_ip": self.idx_to_ip,
            "idx_to_email": self.idx_to_email,
        }
        with open(path, "wb") as f:
            pickle.dump(mappings, f)
        print(f"Mappings saved to: {path}")

    @classmethod
    def load_mappings(cls, path: Path) -> "TransactionGraphBuilder":
        """Load graph builder with saved mappings."""
        with open(path, "rb") as f:
            mappings = pickle.load(f)

        builder = cls()
        builder.user_to_idx = mappings["user_to_idx"]
        builder.device_to_idx = mappings["device_to_idx"]
        builder.ip_to_idx = mappings["ip_to_idx"]
        builder.email_to_idx = mappings["email_to_idx"]
        builder.idx_to_user = mappings["idx_to_user"]
        builder.idx_to_device = mappings["idx_to_device"]
        builder.idx_to_ip = mappings["idx_to_ip"]
        builder.idx_to_email = mappings["idx_to_email"]

        return builder


# =============================================================================
# STANDALONE GRAPH BUILDING FUNCTION
# =============================================================================
def build_transaction_graph(
    features_parquet_path: Path,
    output_dir: Path,
    node_feature_dim: int = 64,
    max_nodes_per_type: Optional[int] = None,
    verbose: bool = True,
) -> Data:
    """
    Build transaction graph from processed features.

    This is the main entry point for Sub-Phase 1.4.

    Args:
        features_parquet_path: Path to features.parquet
        output_dir: Directory to save graph.pt and mappings
        node_feature_dim: Dimension of node features (aligned with training_config.yaml)
        max_nodes_per_type: Max nodes per type (for memory efficiency)
        verbose: Print progress

    Returns:
        PyTorch Geometric Data object
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.4: TRANSACTION GRAPH CONSTRUCTION")
    print("=" * 70)

    # Load features
    print(f"\nLoading features from: {features_parquet_path}")
    df = pd.read_parquet(features_parquet_path)
    print(f"  Loaded {len(df):,} transactions")

    # Build graph
    builder = TransactionGraphBuilder(
        node_feature_dim=node_feature_dim, max_nodes_per_type=max_nodes_per_type
    )

    graph = builder.build_graph(df, verbose=verbose)

    # Save outputs
    output_dir.mkdir(parents=True, exist_ok=True)

    graph_path = output_dir / "graph.pt"
    builder.save_graph(graph, graph_path)

    mappings_path = output_dir / "graph_mappings.pkl"
    builder.save_mappings(mappings_path)

    return graph


# =============================================================================
# MAIN (for standalone testing)
# =============================================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build transaction graph")
    parser.add_argument(
        "--features", type=str, required=True, help="Path to features.parquet"
    )
    parser.add_argument("--output", type=str, required=True, help="Output directory")
    parser.add_argument("--dim", type=int, default=64, help="Node feature dimension")
    args = parser.parse_args()

    graph = build_transaction_graph(
        features_parquet_path=Path(args.features),
        output_dir=Path(args.output),
        node_feature_dim=args.dim,
    )

    print(f"\nGraph built successfully!")
    print(f"  Nodes: {graph.num_nodes:,}")
    print(f"  Edges: {graph.num_edges:,}")

"""
SENTINEL FRAUD DETECTION - MULTI-MODAL FUSION MODEL
====================================================
This is the CORE MODEL that combines:
1. Tabular features (transaction metadata)
2. Sequential features (user behavior over time)
3. Graph features (network relationships)

Architecture inspired by:
- BiFPN (Bidirectional Feature Pyramid Network) for fusion
- Multi-task learning (fraud detection + type + score + MFA decision)
- Focal Loss for class imbalance handling

Training Time: ~2-3 hours on RTX 5050
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, Tuple, Optional
import math


# =============================================================================
# FOCAL LOSS (Handles extreme class imbalance - fraud is ~0.1%)
# =============================================================================
class FocalLoss(nn.Module):
    """
    Focal Loss from 'Focal Loss for Dense Object Detection' paper.

    Down-weights easy examples, focuses on hard ones.
    Critical for fraud detection where fraud is rare.

    Standard BCE: -log(p)
    Focal Loss: -(1-p)^gamma * log(p)
    """

    def __init__(self, alpha: float = 0.25, gamma: float = 2.0):
        super().__init__()
        self.alpha = alpha
        self.gamma = gamma

    def forward(self, logits: torch.Tensor, targets: torch.Tensor) -> torch.Tensor:
        probs = torch.sigmoid(logits)

        # p_t = p if y=1, else 1-p
        p_t = probs * targets + (1 - probs) * (1 - targets)

        # alpha_t = alpha if y=1, else 1-alpha
        alpha_t = self.alpha * targets + (1 - self.alpha) * (1 - targets)

        # Focal weight: (1 - p_t)^gamma
        focal_weight = (1 - p_t) ** self.gamma

        # Standard BCE
        bce = F.binary_cross_entropy_with_logits(logits, targets, reduction="none")

        # Apply focal weight
        focal_loss = alpha_t * focal_weight * bce

        return focal_loss.mean()


# =============================================================================
# POSITIONAL ENCODING (For Transformer)
# =============================================================================
class PositionalEncoding(nn.Module):
    """
    Sinusoidal positional encoding for sequence awareness.
    Tells the transformer the ORDER of transactions.
    """

    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        # Create positional encoding matrix
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
        """
        Args:
            x: [batch_size, seq_len, d_model]
        Returns:
            [batch_size, seq_len, d_model] with positional info added
        """
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


# =============================================================================
# BRANCH 1: TABULAR ENCODER (Entity Embeddings + MLP)
# =============================================================================
class TabularEncoder(nn.Module):
    """
    Encodes tabular features (transaction metadata) into dense embeddings.

    Handles:
    - Categorical features → Entity Embeddings (like word embeddings for categories)
    - Numerical features → Normalization + Linear projection

    Why this works better than one-hot:
    - Learns semantic relationships between categories
    - "Amazon" and "Flipkart" might have similar embeddings (both e-commerce)
    - Much more parameter-efficient
    """

    def __init__(
        self,
        categorical_cardinalities: Dict[str, int],  # {feature_name: num_categories}
        num_numerical_features: int,
        embedding_dim: int = 32,
        hidden_dims: list = [256, 128, 64],
        output_dim: int = 128,
        dropout: float = 0.3,
    ):
        super().__init__()

        # Create embedding layer for each categorical feature
        self.embeddings = nn.ModuleDict(
            {
                name: nn.Embedding(num_categories + 1, embedding_dim, padding_idx=0)
                for name, num_categories in categorical_cardinalities.items()
            }
        )

        self.categorical_names = list(categorical_cardinalities.keys())

        # Project numerical features
        self.numerical_bn = nn.BatchNorm1d(num_numerical_features)
        self.numerical_proj = nn.Linear(num_numerical_features, embedding_dim)

        # Calculate total input dim
        total_embedding_dim = embedding_dim * (len(categorical_cardinalities) + 1)

        # MLP layers
        layers = []
        prev_dim = total_embedding_dim
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

        # Final projection
        layers.append(nn.Linear(prev_dim, output_dim))

        self.mlp = nn.Sequential(*layers)

    def forward(
        self,
        categorical_features: Dict[str, torch.Tensor],  # {name: [batch_size]}
        numerical_features: torch.Tensor,  # [batch_size, num_numerical]
    ) -> torch.Tensor:
        """
        Returns: [batch_size, output_dim] embedding
        """
        # Embed each categorical feature
        embedded = []
        for name in self.categorical_names:
            if name in categorical_features:
                emb = self.embeddings[name](categorical_features[name])
                embedded.append(emb)

        # Project numerical features
        num_normed = self.numerical_bn(numerical_features)
        num_proj = self.numerical_proj(num_normed)
        embedded.append(num_proj)

        # Concatenate all embeddings
        combined = torch.cat(embedded, dim=-1)

        # Pass through MLP
        return self.mlp(combined)


# =============================================================================
# BRANCH 2: SEQUENCE TRANSFORMER (User Behavior Over Time)
# =============================================================================
class SequenceTransformer(nn.Module):
    """
    Transformer encoder for transaction sequences.

    Processes user's last N transactions to understand behavioral patterns.

    Detects:
    - Card testing (small → small → small → large)
    - ATO chains (login → password change → add card → transfer)
    - Behavioral anomalies (user always shops daytime, suddenly 3AM)

    Architecture:
    - 6-layer Transformer Encoder (like BERT)
    - Multi-head self-attention
    - Positional encoding for temporal awareness
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

        # Project input features to model dimension
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

        # Output projection
        self.output_proj = nn.Linear(d_model, output_dim)

        # Attention weights for explainability
        self.attention_weights = None

    def forward(
        self,
        sequence: torch.Tensor,  # [batch_size, seq_len, feature_dim]
        mask: Optional[torch.Tensor] = None,  # [batch_size, seq_len] padding mask
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            output: [batch_size, output_dim] - Behavioral embedding
            attention_weights: [batch_size, seq_len] - For explainability
        """
        batch_size, seq_len, _ = sequence.shape

        # Project to model dimension
        x = self.input_proj(sequence)

        # Add positional encoding
        x = self.pos_encoder(x)

        # Create attention mask if padding mask provided
        if mask is not None:
            # Convert padding mask to attention mask
            # True = padding (ignore), False = valid
            src_key_padding_mask = ~mask.bool()
        else:
            src_key_padding_mask = None

        # Apply transformer
        x = self.transformer(x, src_key_padding_mask=src_key_padding_mask)

        # Layer norm
        x = self.layer_norm(x)

        # Use mean pooling over sequence (or could use [CLS] token)
        # Mean pooling is more robust
        if mask is not None:
            # Masked mean pooling
            mask_expanded = mask.unsqueeze(-1).float()
            x = (x * mask_expanded).sum(dim=1) / mask_expanded.sum(dim=1).clamp(min=1)
        else:
            x = x.mean(dim=1)

        # Calculate attention weights for explainability (simplified)
        # Which time steps were most important?
        attention_weights = F.softmax(
            x.norm(dim=-1, keepdim=True).expand(-1, seq_len), dim=1
        )

        # Final projection
        output = self.output_proj(x)

        return output, attention_weights


# =============================================================================
# BRANCH 3: GRAPH ATTENTION NETWORK (Fraud Ring Detection)
# =============================================================================
# Note: Full implementation uses PyTorch Geometric
# This is a simplified version for understanding


class SimpleGraphAttention(nn.Module):
    """
    Simplified Graph Attention layer.

    For full implementation, we use PyTorch Geometric's GATConv.

    This demonstrates the concept:
    - Each node attends to its neighbors
    - Learns which neighbors are important
    - Aggregates neighbor information
    """

    def __init__(self, in_dim: int, out_dim: int, num_heads: int = 4):
        super().__init__()
        self.num_heads = num_heads
        self.head_dim = out_dim // num_heads

        # Linear projections for Q, K, V
        self.W_q = nn.Linear(in_dim, out_dim)
        self.W_k = nn.Linear(in_dim, out_dim)
        self.W_v = nn.Linear(in_dim, out_dim)

        # Output projection
        self.W_o = nn.Linear(out_dim, out_dim)

    def forward(
        self,
        node_features: torch.Tensor,  # [num_nodes, in_dim]
        adjacency: torch.Tensor,  # [num_nodes, num_nodes] adjacency matrix
    ) -> torch.Tensor:
        """
        Returns: [num_nodes, out_dim] - Updated node embeddings
        """
        num_nodes = node_features.size(0)

        # Compute Q, K, V
        Q = self.W_q(node_features)  # [num_nodes, out_dim]
        K = self.W_k(node_features)
        V = self.W_v(node_features)

        # Compute attention scores
        attention = torch.matmul(Q, K.transpose(-1, -2)) / math.sqrt(self.head_dim)

        # Mask non-neighbors (set to -inf before softmax)
        mask = adjacency == 0
        attention = attention.masked_fill(mask, float("-inf"))

        # Softmax over neighbors
        attention = F.softmax(attention, dim=-1)
        attention = torch.nan_to_num(attention, nan=0.0)  # Handle isolated nodes

        # Aggregate neighbor values
        output = torch.matmul(attention, V)

        # Output projection
        return self.W_o(output)


class GraphEncoder(nn.Module):
    """
    Multi-layer Graph Attention Network for fraud ring detection.

    What it learns:
    - Accounts connected to many fraud accounts → Higher risk
    - Devices shared across multiple accounts → Device farming
    - Tight clusters of accounts → Potential fraud ring
    - Temporal synchronization → Coordinated attacks
    """

    def __init__(
        self,
        input_dim: int = 64,
        hidden_dim: int = 128,
        output_dim: int = 128,
        num_layers: int = 3,
        dropout: float = 0.2,
    ):
        super().__init__()

        # Initial projection
        self.input_proj = nn.Linear(input_dim, hidden_dim)

        # Graph attention layers
        self.layers = nn.ModuleList()
        for i in range(num_layers):
            self.layers.append(SimpleGraphAttention(hidden_dim, hidden_dim))

        # Layer norms
        self.norms = nn.ModuleList(
            [nn.LayerNorm(hidden_dim) for _ in range(num_layers)]
        )

        self.dropout = nn.Dropout(dropout)

        # Output projection
        self.output_proj = nn.Linear(hidden_dim, output_dim)

    def forward(
        self,
        node_features: torch.Tensor,  # [num_nodes, input_dim]
        adjacency: torch.Tensor,  # [num_nodes, num_nodes]
        target_node_idx: torch.Tensor,  # [batch_size] - Which nodes to get embeddings for
    ) -> torch.Tensor:
        """
        Returns: [batch_size, output_dim] - Embeddings for target nodes
        """
        # Initial projection
        x = self.input_proj(node_features)

        # Apply graph attention layers
        for layer, norm in zip(self.layers, self.norms):
            residual = x
            x = layer(x, adjacency)
            x = norm(x + residual)  # Residual connection
            x = self.dropout(x)

        # Extract embeddings for target nodes
        target_embeddings = x[target_node_idx]

        # Output projection
        return self.output_proj(target_embeddings)


# =============================================================================
# CROSS-MODAL FUSION MODULE (Combines All Three Branches)
# =============================================================================
class CrossModalFusion(nn.Module):
    """
    Fuses embeddings from Tabular, Sequential, and Graph branches.

    Uses cross-attention to learn:
    - For ATO attack: Sequential features matter more
    - For fraud ring: Graph features matter more
    - For synthetic identity: Tabular features matter more

    Inspired by BiFPN's weighted fusion.
    """

    def __init__(
        self,
        tabular_dim: int = 128,
        sequence_dim: int = 128,
        graph_dim: int = 128,
        fusion_dim: int = 256,
        num_heads: int = 8,
        dropout: float = 0.1,
    ):
        super().__init__()

        # Project all inputs to same dimension
        self.tabular_proj = nn.Linear(tabular_dim, fusion_dim)
        self.sequence_proj = nn.Linear(sequence_dim, fusion_dim)
        self.graph_proj = nn.Linear(graph_dim, fusion_dim)

        # Cross-attention between modalities
        self.cross_attention = nn.MultiheadAttention(
            embed_dim=fusion_dim, num_heads=num_heads, dropout=dropout, batch_first=True
        )

        # Learnable fusion weights (like BiFPN)
        self.fusion_weights = nn.Parameter(torch.ones(3))

        # Final layers
        self.layer_norm = nn.LayerNorm(fusion_dim)
        self.ffn = nn.Sequential(
            nn.Linear(fusion_dim, fusion_dim * 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(fusion_dim * 2, fusion_dim),
        )

        # Store attention weights for explainability
        self.modality_attention = None

    def forward(
        self,
        tabular_emb: torch.Tensor,  # [batch_size, tabular_dim]
        sequence_emb: torch.Tensor,  # [batch_size, sequence_dim]
        graph_emb: torch.Tensor,  # [batch_size, graph_dim]
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Returns:
            fused: [batch_size, fusion_dim] - Fused representation
            modality_weights: [batch_size, 3] - Weight of each modality (for explainability)
        """
        batch_size = tabular_emb.size(0)

        # Project to same dimension
        tabular = self.tabular_proj(tabular_emb)
        sequence = self.sequence_proj(sequence_emb)
        graph = self.graph_proj(graph_emb)

        # Stack as sequence for cross-attention: [batch_size, 3, fusion_dim]
        stacked = torch.stack([tabular, sequence, graph], dim=1)

        # Apply cross-attention (each modality attends to others)
        attn_out, attn_weights = self.cross_attention(stacked, stacked, stacked)

        # Learnable weighted fusion
        weights = F.softmax(self.fusion_weights, dim=0)
        fused = (
            weights[0] * attn_out[:, 0]
            + weights[1] * attn_out[:, 1]
            + weights[2] * attn_out[:, 2]
        )

        # Residual + LayerNorm + FFN
        fused = self.layer_norm(fused + tabular + sequence + graph)
        fused = fused + self.ffn(fused)

        # Store for explainability
        self.modality_attention = weights.detach()

        # Return modality weights for each sample
        modality_weights = weights.unsqueeze(0).expand(batch_size, -1)

        return fused, modality_weights


# =============================================================================
# MULTI-TASK OUTPUT HEADS
# =============================================================================
class MultiTaskHeads(nn.Module):
    """
    Multiple prediction heads sharing the fused representation.

    Heads:
    1. Fraud Binary: Is this fraud? (0/1)
    2. Fraud Type: What kind? (ATO, Card Theft, Synthetic ID, Mule, Legit)
    3. Risk Score: Continuous 0-100
    4. MFA Decision: Allow / Trigger MFA / Block

    Multi-task learning helps because:
    - Related tasks share representations
    - Knowing fraud type helps fraud detection
    - Single model = faster inference
    """

    def __init__(
        self,
        input_dim: int = 256,
        num_fraud_types: int = 5,
        hidden_dim: int = 128,
        dropout: float = 0.2,
    ):
        super().__init__()

        # Shared representation
        self.shared = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Dropout(dropout),
        )

        # Head 1: Binary fraud detection
        self.fraud_head = nn.Sequential(
            nn.Linear(hidden_dim, 64), nn.ReLU(), nn.Linear(64, 1)
        )

        # Head 2: Fraud type classification
        self.type_head = nn.Sequential(
            nn.Linear(hidden_dim, 64), nn.ReLU(), nn.Linear(64, num_fraud_types)
        )

        # Head 3: Risk score regression (0-100)
        self.score_head = nn.Sequential(
            nn.Linear(hidden_dim, 64),
            nn.ReLU(),
            nn.Linear(64, 1),
            nn.Sigmoid(),  # Output 0-1, multiply by 100 later
        )

        # Head 4: MFA decision (Allow=0, MFA=1, Block=2)
        self.mfa_head = nn.Sequential(
            nn.Linear(hidden_dim, 64), nn.ReLU(), nn.Linear(64, 3)
        )

    def forward(self, fused_representation: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Returns dict of predictions:
        - fraud_logits: [batch_size, 1]
        - fraud_prob: [batch_size, 1]
        - type_logits: [batch_size, num_fraud_types]
        - type_probs: [batch_size, num_fraud_types]
        - risk_score: [batch_size, 1] (0-100)
        - mfa_logits: [batch_size, 3]
        - mfa_decision: [batch_size] (0, 1, or 2)
        """
        shared = self.shared(fused_representation)

        # Fraud detection
        fraud_logits = self.fraud_head(shared)
        fraud_prob = torch.sigmoid(fraud_logits)

        # Fraud type
        type_logits = self.type_head(shared)
        type_probs = F.softmax(type_logits, dim=-1)

        # Risk score
        risk_score = self.score_head(shared) * 100  # Scale to 0-100

        # MFA decision
        mfa_logits = self.mfa_head(shared)
        mfa_decision = torch.argmax(mfa_logits, dim=-1)

        return {
            "fraud_logits": fraud_logits,
            "fraud_prob": fraud_prob,
            "type_logits": type_logits,
            "type_probs": type_probs,
            "risk_score": risk_score,
            "mfa_logits": mfa_logits,
            "mfa_decision": mfa_decision,
        }


# =============================================================================
# COMPLETE SENTINEL FRAUD MODEL
# =============================================================================
class SentinelFraudModel(nn.Module):
    """
    The complete SENTINEL multi-modal fraud detection model.

    Architecture:
    ┌─────────────────────────────────────────────────────────────┐
    │                    INPUT TRANSACTION                        │
    └───────────────────────────┬─────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
            ▼                   ▼                   ▼
    ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
    │   TABULAR     │   │  SEQUENTIAL   │   │    GRAPH      │
    │   ENCODER     │   │  TRANSFORMER  │   │     GNN       │
    │  (128-dim)    │   │   (128-dim)   │   │   (128-dim)   │
    └───────┬───────┘   └───────┬───────┘   └───────┬───────┘
            │                   │                   │
            └───────────────────┼───────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │   CROSS-MODAL FUSION  │
                    │      (256-dim)        │
                    └───────────┬───────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │           │           │           │
            ▼           ▼           ▼           ▼
        ┌───────┐   ┌───────┐   ┌───────┐   ┌───────┐
        │ FRAUD │   │ TYPE  │   │ SCORE │   │  MFA  │
        │ HEAD  │   │ HEAD  │   │ HEAD  │   │ HEAD  │
        └───────┘   └───────┘   └───────┘   └───────┘
    """

    def __init__(
        self,
        # Tabular encoder params
        categorical_cardinalities: Dict[str, int],
        num_numerical_features: int,
        # Sequence transformer params
        sequence_feature_dim: int = 32,
        max_sequence_length: int = 50,
        # Graph encoder params
        graph_node_dim: int = 64,
        # General params
        embedding_dim: int = 128,
        fusion_dim: int = 256,
        num_fraud_types: int = 5,
        dropout: float = 0.2,
    ):
        super().__init__()

        # Branch 1: Tabular
        self.tabular_encoder = TabularEncoder(
            categorical_cardinalities=categorical_cardinalities,
            num_numerical_features=num_numerical_features,
            embedding_dim=32,
            hidden_dims=[256, 128],
            output_dim=embedding_dim,
            dropout=dropout,
        )

        # Branch 2: Sequential
        self.sequence_encoder = SequenceTransformer(
            feature_dim=sequence_feature_dim,
            d_model=128,
            nhead=8,
            num_layers=6,
            dim_feedforward=512,
            dropout=0.1,
            max_seq_len=max_sequence_length,
            output_dim=embedding_dim,
        )

        # Branch 3: Graph
        self.graph_encoder = GraphEncoder(
            input_dim=graph_node_dim,
            hidden_dim=128,
            output_dim=embedding_dim,
            num_layers=3,
            dropout=dropout,
        )

        # Fusion
        self.fusion = CrossModalFusion(
            tabular_dim=embedding_dim,
            sequence_dim=embedding_dim,
            graph_dim=embedding_dim,
            fusion_dim=fusion_dim,
            num_heads=8,
            dropout=dropout,
        )

        # Output heads
        self.heads = MultiTaskHeads(
            input_dim=fusion_dim,
            num_fraud_types=num_fraud_types,
            hidden_dim=128,
            dropout=dropout,
        )

        # Loss functions
        self.fraud_loss_fn = FocalLoss(alpha=0.25, gamma=2.0)
        self.type_loss_fn = nn.CrossEntropyLoss()
        self.score_loss_fn = nn.MSELoss()
        self.mfa_loss_fn = nn.CrossEntropyLoss()

    def forward(
        self,
        categorical_features: Dict[str, torch.Tensor],
        numerical_features: torch.Tensor,
        transaction_sequence: torch.Tensor,
        sequence_mask: Optional[torch.Tensor],
        graph_node_features: torch.Tensor,
        graph_adjacency: torch.Tensor,
        target_node_idx: torch.Tensor,
    ) -> Dict[str, torch.Tensor]:
        """
        Full forward pass through all branches and heads.
        """
        # Tabular branch
        tabular_emb = self.tabular_encoder(categorical_features, numerical_features)

        # Sequence branch
        sequence_emb, seq_attention = self.sequence_encoder(
            transaction_sequence, sequence_mask
        )

        # Graph branch
        graph_emb = self.graph_encoder(
            graph_node_features, graph_adjacency, target_node_idx
        )

        # Fusion
        fused, modality_weights = self.fusion(tabular_emb, sequence_emb, graph_emb)

        # Output heads
        outputs = self.heads(fused)

        # Add explainability info
        outputs["sequence_attention"] = seq_attention
        outputs["modality_weights"] = modality_weights

        return outputs

    def compute_loss(
        self, outputs: Dict[str, torch.Tensor], targets: Dict[str, torch.Tensor]
    ) -> Dict[str, torch.Tensor]:
        """
        Compute multi-task loss.

        targets:
            - is_fraud: [batch_size] float
            - fraud_type: [batch_size] long
            - risk_score: [batch_size] float
            - mfa_decision: [batch_size] long
        """
        losses = {}

        # Fraud detection loss (Focal Loss)
        losses["fraud_loss"] = self.fraud_loss_fn(
            outputs["fraud_logits"].squeeze(-1), targets["is_fraud"]
        )

        # Type classification loss
        losses["type_loss"] = self.type_loss_fn(
            outputs["type_logits"], targets["fraud_type"]
        )

        # Risk score loss
        losses["score_loss"] = self.score_loss_fn(
            outputs["risk_score"].squeeze(-1), targets["risk_score"]
        )

        # MFA decision loss
        losses["mfa_loss"] = self.mfa_loss_fn(
            outputs["mfa_logits"], targets["mfa_decision"]
        )

        # Total loss (weighted sum)
        losses["total_loss"] = (
            1.0 * losses["fraud_loss"]
            + 0.5 * losses["type_loss"]
            + 0.3 * losses["score_loss"]
            + 0.5 * losses["mfa_loss"]
        )

        return losses


# =============================================================================
# MODEL FACTORY FUNCTION
# =============================================================================
def create_sentinel_model(config: dict) -> SentinelFraudModel:
    """
    Create model from config dictionary.
    """
    # Default categorical cardinalities (will be updated from data)
    categorical_cardinalities = {
        "merchant_category": 100,
        "device_type": 10,
        "card_type": 5,
        "country": 250,
        "email_domain": 1000,
    }

    model = SentinelFraudModel(
        categorical_cardinalities=categorical_cardinalities,
        num_numerical_features=config.get("num_numerical_features", 45),
        sequence_feature_dim=config.get("sequence_feature_dim", 32),
        max_sequence_length=config.get("max_sequence_length", 50),
        graph_node_dim=config.get("graph_node_dim", 64),
        embedding_dim=config.get("embedding_dim", 128),
        fusion_dim=config.get("fusion_dim", 256),
        num_fraud_types=config.get("num_fraud_types", 5),
        dropout=config.get("dropout", 0.2),
    )

    return model


if __name__ == "__main__":
    # Quick test
    print("Testing SentinelFraudModel...")

    # Create model
    model = create_sentinel_model({})

    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)

    print(f"Total parameters: {total_params:,}")
    print(f"Trainable parameters: {trainable_params:,}")
    print(f"Model size: ~{total_params * 4 / 1024 / 1024:.1f} MB (float32)")

    print("\nModel created successfully!")

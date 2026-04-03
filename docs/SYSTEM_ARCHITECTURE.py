# ============================================================================
#  SENTINEL - FINANCIAL FRAUD INTELLIGENCE PLATFORM
#  COMPLETE SYSTEM ARCHITECTURE DOCUMENT
# ============================================================================
#  Version: 1.0
#  Last Updated: April 3, 2026
#  Team: You (ML/DL Lead) + Kumud (Frontend/Backend)
# ============================================================================

"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║   ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗                ║
║   ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║                ║
║   ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║                ║
║   ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║                ║
║   ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗           ║
║   ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝           ║
║                                                                              ║
║   COGNITIVE FRAUD INTELLIGENCE PLATFORM                                     ║
║   Real-Time • Adaptive • Explainable                                        ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ============================================================================
# TABLE OF CONTENTS
# ============================================================================
"""
1. EXECUTIVE SUMMARY
2. PROBLEM STATEMENT (Updated PS)
3. HIGH-LEVEL ARCHITECTURE DIAGRAM
4. DETAILED LAYER BREAKDOWN
   4.1 Data Ingestion Layer
   4.2 Feature Engineering Layer
   4.3 ML/DL Model Layer
   4.4 Decision Engine Layer
   4.5 Explainability Layer
   4.6 Frontend Visualization Layer
   4.7 Database Layer
5. DATA FLOW DIAGRAM
6. COMPONENT SPECIFICATIONS
7. TECHNOLOGY STACK MAPPING
8. TRAINING VS FINE-TUNING BREAKDOWN
9. TIME ESTIMATES
10. PHASE-WISE IMPLEMENTATION PLAN
11. WORK DIVISION (You vs Kumud)
12. X-FACTORS & DIFFERENTIATORS
"""


# ============================================================================
# 1. EXECUTIVE SUMMARY
# ============================================================================
"""
SENTINEL is a next-generation financial fraud detection platform that combines:

• Multi-Modal Deep Learning (Tabular + Sequential + Graph)
• Real-Time Fraud Chain Detection (ATO, Card Testing patterns)
• Graph Neural Networks for Fraud Ring Detection
• Reinforcement Learning for Adaptive Thresholds
• Explainable AI with Natural Language Reports (Mistral 7B)
• Interactive Attack Simulation for Demo

KEY METRICS WE TARGET:
├── Detection Accuracy: >95% (using multi-modal fusion)
├── False Positive Rate: <5% (using behavioral context)
├── Detection Latency: <100ms (optimized pipeline)
├── Adaptability: Real-time threshold adjustment (RL)
└── Explainability: Natural language + visual attribution
"""


# ============================================================================
# 2. PROBLEM STATEMENT (Updated PS - April 2026)
# ============================================================================
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  TOPIC 03: FINANCIAL FRAUD DETECTION SYSTEM (Elite Level)                   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  CHALLENGE: Design a system that can detect and prevent financial fraud     ║
║  BEFORE transactions are completed.                                         ║
║                                                                              ║
║  REQUIREMENTS:                                                               ║
║  ├── Build behavioral user profiles and anomaly detection                   ║
║  ├── Detect fraud chains (ATO → transaction abuse)                          ║
║  ├── Implement dynamic risk scoring with explanations                       ║
║  ├── Enable pre-transaction decisioning (approve/block/MFA)                 ║
║  ├── Support adaptive learning for evolving fraud                           ║
║  ├── Real-time fraud detection and scoring engine                           ║
║  ├── Decision system for transaction approval/intervention                  ║
║  └── Visualization/monitoring interface                                     ║
║                                                                              ║
║  BROWNIE POINTS:                                                             ║
║  ├── Graph-based detection of fraud rings                                   ║
║  ├── Synthetic identity detection                                           ║
║  └── Fraud simulation environment                                           ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

EVALUATION METRICS (What Judges Score):
┌─────────────────────┬────────────────────────────────────────────────────────┐
│ Metric              │ How We Address It                                      │
├─────────────────────┼────────────────────────────────────────────────────────┤
│ Innovation          │ Multi-modal fusion, GNN fraud rings, RL thresholds     │
│ Clarity             │ Explainable AI, natural language reports               │
│ Technical Execution │ Deep learning stack, proper training pipeline          │
│ Practicality        │ Industry-standard patterns, <100ms latency             │
└─────────────────────┴────────────────────────────────────────────────────────┘
"""


# ============================================================================
# 3. HIGH-LEVEL ARCHITECTURE DIAGRAM
# ============================================================================
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║                      SENTINEL SYSTEM ARCHITECTURE                            ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                        FRONTEND LAYER                                   │ ║
║  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ ║
║  │  │ Live Stream │  │   Graph     │  │ Investigation│ │   Attack    │    │ ║
║  │  │  Dashboard  │  │ Visualizer  │  │    Panel    │  │  Simulator  │    │ ║
║  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │ ║
║  │                    React + Tailwind + Cytoscape.js                      │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                    │                                         ║
║                                    │ WebSocket (Real-time)                   ║
║                                    ▼                                         ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                         BACKEND API LAYER                               │ ║
║  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ ║
║  │  │  FastAPI    │  │  WebSocket  │  │  Simulator  │  │   Redis     │    │ ║
║  │  │  Endpoints  │  │   Handler   │  │   Engine    │  │   Cache     │    │ ║
║  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                    │                                         ║
║                                    ▼                                         ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                      ML/DL INFERENCE LAYER                              │ ║
║  │                                                                         │ ║
║  │  ┌───────────────────────────────────────────────────────────────────┐ │ ║
║  │  │                    FEATURE EXTRACTION                             │ │ ║
║  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │ │ ║
║  │  │  │Behavioral│  │  Device  │  │ Network  │  │ Identity │          │ │ ║
║  │  │  │ Features │  │ Features │  │ Features │  │ Features │          │ │ ║
║  │  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │ │ ║
║  │  └───────────────────────────────────────────────────────────────────┘ │ ║
║  │                                    │                                   │ ║
║  │                                    ▼                                   │ ║
║  │  ┌───────────────────────────────────────────────────────────────────┐ │ ║
║  │  │                  MULTI-MODAL FUSION MODEL                         │ │ ║
║  │  │                                                                   │ │ ║
║  │  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐             │ │ ║
║  │  │  │   TABULAR   │   │ SEQUENTIAL  │   │    GRAPH    │             │ │ ║
║  │  │  │   ENCODER   │   │ TRANSFORMER │   │     GNN     │             │ │ ║
║  │  │  │  (128-dim)  │   │  (128-dim)  │   │  (128-dim)  │             │ │ ║
║  │  │  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘             │ │ ║
║  │  │         │                 │                 │                    │ │ ║
║  │  │         └─────────────────┼─────────────────┘                    │ │ ║
║  │  │                           │                                      │ │ ║
║  │  │                           ▼                                      │ │ ║
║  │  │              ┌─────────────────────────┐                         │ │ ║
║  │  │              │   CROSS-MODAL FUSION    │                         │ │ ║
║  │  │              │  (Cross-Attention 256d) │                         │ │ ║
║  │  │              └────────────┬────────────┘                         │ │ ║
║  │  │                           │                                      │ │ ║
║  │  │     ┌─────────────────────┼─────────────────────┐                │ │ ║
║  │  │     │           │         │         │           │                │ │ ║
║  │  │     ▼           ▼         ▼         ▼           ▼                │ │ ║
║  │  │ ┌───────┐  ┌────────┐ ┌───────┐ ┌───────┐ ┌──────────┐          │ │ ║
║  │  │ │ FRAUD │  │ FRAUD  │ │ RISK  │ │  MFA  │ │ EXPLAIN  │          │ │ ║
║  │  │ │ HEAD  │  │ TYPE   │ │ SCORE │ │ HEAD  │ │   HEAD   │          │ │ ║
║  │  │ │ (0/1) │  │ (5cls) │ │(0-100)│ │(3cls) │ │ (SHAP)   │          │ │ ║
║  │  │ └───────┘  └────────┘ └───────┘ └───────┘ └──────────┘          │ │ ║
║  │  └───────────────────────────────────────────────────────────────────┘ │ ║
║  │                                    │                                   │ ║
║  │                                    ▼                                   │ ║
║  │  ┌───────────────────────────────────────────────────────────────────┐ │ ║
║  │  │                    DECISION ENGINE                                │ │ ║
║  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │ │ ║
║  │  │  │  RL AGENT    │  │ RULE ENGINE  │  │ FRAUD CHAIN  │            │ │ ║
║  │  │  │ (Threshold)  │  │ (Prabhat's)  │  │  DETECTOR    │            │ │ ║
║  │  │  └──────────────┘  └──────────────┘  └──────────────┘            │ │ ║
║  │  │                         │                                        │ │ ║
║  │  │                         ▼                                        │ │ ║
║  │  │           ┌─────────────────────────────┐                        │ │ ║
║  │  │           │  DECISION: ALLOW │ MFA │ BLOCK  │                    │ │ ║
║  │  │           └─────────────────────────────┘                        │ │ ║
║  │  └───────────────────────────────────────────────────────────────────┘ │ ║
║  │                                    │                                   │ ║
║  │                                    ▼                                   │ ║
║  │  ┌───────────────────────────────────────────────────────────────────┐ │ ║
║  │  │                   EXPLAINABILITY ENGINE                           │ │ ║
║  │  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐            │ │ ║
║  │  │  │    SHAP      │  │  ATTENTION   │  │  MISTRAL 7B  │            │ │ ║
║  │  │  │   Values     │  │   Weights    │  │   Copilot    │            │ │ ║
║  │  │  └──────────────┘  └──────────────┘  └──────────────┘            │ │ ║
║  │  └───────────────────────────────────────────────────────────────────┘ │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                    │                                         ║
║                                    ▼                                         ║
║  ┌─────────────────────────────────────────────────────────────────────────┐ ║
║  │                        DATABASE LAYER                                   │ ║
║  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │ ║
║  │  │ PostgreSQL  │  │    Redis    │  │  ChromaDB   │  │   Neo4j     │    │ ║
║  │  │ (Transactions│  │   (Cache)   │  │  (Vectors)  │  │  (Graph)    │    │ ║
║  │  │  Users,Cases)│  │             │  │             │  │  Optional   │    │ ║
║  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │ ║
║  └─────────────────────────────────────────────────────────────────────────┘ ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""


# ============================================================================
# 4. DETAILED LAYER BREAKDOWN
# ============================================================================

# ──────────────────────────────────────────────────────────────────────────────
# 4.1 DATA INGESTION LAYER
# ──────────────────────────────────────────────────────────────────────────────
"""
PURPOSE: Accept transactions from payment gateways in real-time

COMPONENTS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ COMPONENT          │ TECHNOLOGY      │ FUNCTION                            │
├────────────────────┼─────────────────┼─────────────────────────────────────┤
│ API Gateway        │ FastAPI         │ REST endpoint for transactions      │
│ WebSocket Server   │ FastAPI WS      │ Real-time streaming to frontend     │
│ Message Queue      │ Redis Streams   │ Buffer for high-throughput          │
│ Schema Validation  │ Pydantic        │ Validate transaction format         │
└─────────────────────────────────────────────────────────────────────────────┘

INPUT FORMAT (What a transaction looks like):
{
    "transaction_id": "TXN-2026-04-03-12345",
    "user_id": "USER-001",
    "amount": 49990.00,
    "currency": "INR",
    "merchant_id": "MERCHANT-CRYPTO-001",
    "merchant_category": "6051",  // Crypto
    "timestamp": "2026-04-03T03:14:00Z",
    "device": {
        "device_id": "DEVICE-ABCD1234",
        "device_type": "mobile",
        "user_agent": "Mozilla/5.0 (Linux; Android 12)",
        "is_emulator": false
    },
    "network": {
        "ip_address": "45.33.32.156",
        "ip_country": "US",
        "is_vpn": true,
        "is_tor": false
    },
    "user_info": {
        "email": "user@tempmail.com",
        "phone": "+919876543210",
        "billing_country": "IN"
    },
    "card": {
        "card_last4": "1234",
        "card_type": "visa"
    }
}

LATENCY TARGET: <5ms for ingestion
"""

# ──────────────────────────────────────────────────────────────────────────────
# 4.2 FEATURE ENGINEERING LAYER
# ──────────────────────────────────────────────────────────────────────────────
"""
PURPOSE: Transform raw transaction into 50+ ML-ready features

FEATURE CATEGORIES:
┌─────────────────────────────────────────────────────────────────────────────┐
│ CATEGORY      │ COUNT │ EXAMPLES                      │ SOURCE             │
├───────────────┼───────┼───────────────────────────────┼────────────────────┤
│ Behavioral    │ 8     │ velocity, amount_zscore,      │ Redis (history)    │
│ (Prabhat's)   │       │ impossible_travel, dormant    │                    │
├───────────────┼───────┼───────────────────────────────┼────────────────────┤
│ Device        │ 5     │ is_new_device, device_sharing │ Transaction +      │
│               │       │ is_emulator, device_age       │ Device DB          │
├───────────────┼───────┼───────────────────────────────┼────────────────────┤
│ Network       │ 5     │ is_vpn, is_tor, ip_geo_mismatch│ IP Enrichment     │
│               │       │ ip_risk_score                 │                    │
├───────────────┼───────┼───────────────────────────────┼────────────────────┤
│ Identity      │ 8     │ account_age, recent_changes,  │ PostgreSQL         │
│               │       │ is_temp_email, is_voip        │                    │
├───────────────┼───────┼───────────────────────────────┼────────────────────┤
│ Transactional │ 8     │ amount_normalized, threshold  │ Transaction +      │
│               │       │ _evasion, card_testing_score  │ History            │
├───────────────┼───────┼───────────────────────────────┼────────────────────┤
│ Synthetic ID  │ 3     │ email_age_vs_account,         │ Identity Graph     │
│               │       │ identity_consistency          │                    │
├───────────────┼───────┼───────────────────────────────┼────────────────────┤
│ Time          │ 6     │ hour_sin/cos, is_weekend,     │ Timestamp          │
│               │       │ is_night                      │                    │
├───────────────┼───────┼───────────────────────────────┼────────────────────┤
│ Graph         │ 4     │ node_degree, cluster_coef,    │ GNN (computed)     │
│ (Computed)    │       │ fraud_neighbor_count          │                    │
├───────────────┼───────┼───────────────────────────────┼────────────────────┤
│ Categorical   │ 5     │ merchant_cat, device_type,    │ Transaction        │
│ (Embedded)    │       │ card_type, country, email     │                    │
└─────────────────────────────────────────────────────────────────────────────┘

TOTAL: 52 numerical features + 5 categorical features

TECHNOLOGY:
├── Python + NumPy + Pandas
├── Redis (for user history caching)
└── Custom feature functions

LATENCY TARGET: <10ms for feature extraction
"""

# ──────────────────────────────────────────────────────────────────────────────
# 4.3 ML/DL MODEL LAYER
# ──────────────────────────────────────────────────────────────────────────────
"""
PURPOSE: Score transactions using multi-modal deep learning

ARCHITECTURE OVERVIEW:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  INPUT: 52 numerical + 5 categorical + sequence(50 txns) + graph           │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                         BRANCH 1: TABULAR                             │ │
│  │                                                                       │ │
│  │  Categorical Features ──► Entity Embeddings (32-dim each)            │ │
│  │                                    │                                 │ │
│  │  Numerical Features ──► Batch Norm ──► Linear(64)                   │ │
│  │                                    │                                 │ │
│  │                          Concatenate                                 │ │
│  │                                    │                                 │ │
│  │                          MLP: 256 ──► 128 ──► 64                    │ │
│  │                                    │                                 │ │
│  │                          Output: 128-dim embedding                   │ │
│  │                                                                       │ │
│  │  TECH: PyTorch (nn.Embedding, nn.Linear, nn.BatchNorm1d)            │ │
│  │  TRAINING: From scratch on IEEE-CIS dataset                         │ │
│  │  TIME: 30-60 minutes                                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      BRANCH 2: SEQUENTIAL                             │ │
│  │                                                                       │ │
│  │  Last 50 transactions ──► Feature encoding (32-dim per txn)         │ │
│  │                                    │                                 │ │
│  │                          Positional Encoding                         │ │
│  │                                    │                                 │ │
│  │                          Transformer Encoder                         │ │
│  │                          ├── 6 layers                               │ │
│  │                          ├── 8 attention heads                      │ │
│  │                          └── 512 FFN dimension                      │ │
│  │                                    │                                 │ │
│  │                          Mean Pooling / [CLS] token                  │ │
│  │                                    │                                 │ │
│  │                          Output: 128-dim embedding                   │ │
│  │                                                                       │ │
│  │  TECH: PyTorch (nn.TransformerEncoder)                              │ │
│  │  TRAINING: From scratch on transaction sequences                    │ │
│  │  TIME: 2-4 hours                                                     │ │
│  │                                                                       │ │
│  │  WHAT IT LEARNS:                                                     │ │
│  │  • ATO Chain: login → pwd_change → card_add → transfer              │ │
│  │  • Card Testing: small → small → small → large                      │ │
│  │  • Behavioral Anomalies: daytime user → 3AM transaction             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        BRANCH 3: GRAPH                                │ │
│  │                                                                       │ │
│  │  Transaction Graph:                                                  │ │
│  │  ├── Nodes: Accounts, Devices, IPs, Cards, Phones                   │ │
│  │  └── Edges: Uses, Transacts, Shares                                 │ │
│  │                                    │                                 │ │
│  │                          Node Feature Encoding (64-dim)              │ │
│  │                                    │                                 │ │
│  │                          Graph Attention Network (GAT)               │ │
│  │                          ├── 3 layers                               │ │
│  │                          └── 4 attention heads                      │ │
│  │                                    │                                 │ │
│  │                          Target Node Embedding                       │ │
│  │                                    │                                 │ │
│  │                          Output: 128-dim embedding                   │ │
│  │                                                                       │ │
│  │  TECH: PyTorch Geometric (GATConv)                                  │ │
│  │  TRAINING: From scratch on transaction graph                        │ │
│  │  TIME: 1-2 hours                                                     │ │
│  │                                                                       │ │
│  │  WHAT IT LEARNS:                                                     │ │
│  │  • Device shared by 5 accounts → Suspicious                         │ │
│  │  • Account connected to flagged accounts → Higher risk              │ │
│  │  • Tight cluster of new accounts → Fraud ring                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      CROSS-MODAL FUSION                               │ │
│  │                                                                       │ │
│  │  3 × 128-dim embeddings ──► Stack [batch, 3, 128]                   │ │
│  │                                    │                                 │ │
│  │                          Multi-Head Cross-Attention                  │ │
│  │                          (8 heads, learns modality importance)       │ │
│  │                                    │                                 │ │
│  │                          Learnable Weighted Sum                      │ │
│  │                          (Like BiFPN weighted fusion)                │ │
│  │                                    │                                 │ │
│  │                          Output: 256-dim fused representation        │ │
│  │                                                                       │ │
│  │  TECH: PyTorch (nn.MultiheadAttention)                              │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      MULTI-TASK OUTPUT HEADS                          │ │
│  │                                                                       │ │
│  │  HEAD 1: FRAUD BINARY                                                │ │
│  │  ├── Linear(256, 64) → ReLU → Linear(64, 1) → Sigmoid               │ │
│  │  ├── Output: Fraud probability (0.0 - 1.0)                          │ │
│  │  └── Loss: Focal Loss (handles class imbalance)                     │ │
│  │                                                                       │ │
│  │  HEAD 2: FRAUD TYPE                                                  │ │
│  │  ├── Linear(256, 64) → ReLU → Linear(64, 5) → Softmax               │ │
│  │  ├── Classes: [ATO, Card_Theft, Synthetic_ID, Money_Mule, Legit]    │ │
│  │  └── Loss: Cross-Entropy                                            │ │
│  │                                                                       │ │
│  │  HEAD 3: RISK SCORE                                                  │ │
│  │  ├── Linear(256, 64) → ReLU → Linear(64, 1) → Sigmoid × 100         │ │
│  │  ├── Output: Risk score (0 - 100)                                   │ │
│  │  └── Loss: MSE + Calibration                                        │ │
│  │                                                                       │ │
│  │  HEAD 4: MFA DECISION                                                │ │
│  │  ├── Linear(256, 64) → ReLU → Linear(64, 3) → Softmax               │ │
│  │  ├── Classes: [Allow, Trigger_MFA, Block]                           │ │
│  │  └── Loss: Cross-Entropy                                            │ │
│  │                                                                       │ │
│  │  TRAINING: Joint multi-task learning                                 │ │
│  │  TOTAL LOSS = 1.0×fraud + 0.5×type + 0.3×score + 0.5×mfa           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

TOTAL MODEL PARAMETERS: ~15-20 million
INFERENCE TIME: <30ms on RTX 5050
"""

# ──────────────────────────────────────────────────────────────────────────────
# 4.4 DECISION ENGINE LAYER
# ──────────────────────────────────────────────────────────────────────────────
"""
PURPOSE: Make final decision using ML output + rules + RL

COMPONENTS:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     RL THRESHOLD AGENT                                │ │
│  │                                                                       │ │
│  │  Algorithm: Contextual Bandit (LinUCB)                               │ │
│  │                                                                       │ │
│  │  Context (State):                                                    │ │
│  │  ├── Current risk score                                              │ │
│  │  ├── Hour of day (cyclical)                                          │ │
│  │  ├── Recent fraud rate (last 1 hour)                                 │ │
│  │  ├── Recent false positive rate                                      │ │
│  │  └── User segment                                                    │ │
│  │                                                                       │ │
│  │  Actions (Threshold choices):                                        │ │
│  │  └── [0.3, 0.4, 0.5, 0.6, 0.7]                                      │ │
│  │                                                                       │ │
│  │  Reward Function:                                                    │ │
│  │  ├── True Positive (caught fraud): +10                               │ │
│  │  ├── True Negative (allowed legit): +1                               │ │
│  │  ├── False Positive (blocked legit): -5                              │ │
│  │  └── False Negative (missed fraud): -50                              │ │
│  │                                                                       │ │
│  │  TRAINING: Online learning during inference                          │ │
│  │  TECH: NumPy (no deep learning needed)                               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                      RULE ENGINE (Prabhat's)                          │ │
│  │                                                                       │ │
│  │  HARD BLOCK RULES:                                                   │ │
│  │  ├── IP in known fraud database → BLOCK                              │ │
│  │  ├── Device in fraud database → BLOCK                                │ │
│  │  └── Impossible travel detected → BLOCK                              │ │
│  │                                                                       │ │
│  │  RISK MULTIPLIERS:                                                   │ │
│  │  ├── VPN detected → risk × 1.2                                       │ │
│  │  ├── New device + high value → risk × 1.3                            │ │
│  │  └── Night transaction + anomaly → risk × 1.2                        │ │
│  │                                                                       │ │
│  │  TECH: Python if-else (simple, fast)                                 │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                   FRAUD CHAIN DETECTOR (NEW PS REQ)                   │ │
│  │                                                                       │ │
│  │  PATTERNS DETECTED:                                                  │ │
│  │                                                                       │ │
│  │  ATO CHAIN:                                                          │ │
│  │  login_new_device → password_change → add_card → high_transfer       │ │
│  │  (within 30 minutes)                                                 │ │
│  │                                                                       │ │
│  │  CARD TESTING:                                                       │ │
│  │  micro_txn ($1) → micro_txn ($2) → micro_txn ($1) → large_txn       │ │
│  │  (within 10 minutes)                                                 │ │
│  │                                                                       │ │
│  │  SYNTHETIC IDENTITY:                                                 │ │
│  │  account_creation → card_add → skip_verification → first_txn        │ │
│  │  (within 60 minutes)                                                 │ │
│  │                                                                       │ │
│  │  IMPLEMENTATION: Pattern matching on transaction sequence            │ │
│  │  (Also learned by Transformer, but explicit patterns help)           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  FINAL DECISION LOGIC:                                                      │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │  IF hard_block_rule_triggered:                                       │ │
│  │      return BLOCK                                                    │ │
│  │                                                                       │ │
│  │  IF fraud_chain_detected:                                            │ │
│  │      return BLOCK                                                    │ │
│  │                                                                       │ │
│  │  adjusted_score = ml_score × rule_multipliers                        │ │
│  │  threshold = rl_agent.get_threshold(context)                         │ │
│  │                                                                       │ │
│  │  IF adjusted_score < threshold × 0.5:                                │ │
│  │      return ALLOW                                                    │ │
│  │  ELIF adjusted_score < threshold:                                    │ │
│  │      return MFA  # Trigger 2FA                                       │ │
│  │  ELSE:                                                               │ │
│  │      return BLOCK                                                    │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""

# ──────────────────────────────────────────────────────────────────────────────
# 4.5 EXPLAINABILITY LAYER
# ──────────────────────────────────────────────────────────────────────────────
"""
PURPOSE: Explain WHY a transaction was flagged

COMPONENTS:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        SHAP VALUES                                    │ │
│  │                                                                       │ │
│  │  Purpose: Feature attribution for each prediction                    │ │
│  │                                                                       │ │
│  │  Output:                                                             │ │
│  │  {                                                                   │ │
│  │    "amount_zscore": +0.15,      // Contributed 15% to fraud score   │ │
│  │    "is_new_device": +0.18,      // New device added 18%             │ │
│  │    "device_sharing": +0.19,     // Shared device added 19%          │ │
│  │    "threshold_evasion": +0.12,  // Just below limit                 │ │
│  │    "is_vpn": +0.10,             // VPN detected                     │ │
│  │    ...                                                               │ │
│  │  }                                                                   │ │
│  │                                                                       │ │
│  │  TECH: SHAP library (TreeExplainer for XGBoost, DeepExplainer for DL)│ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                     ATTENTION WEIGHTS                                 │ │
│  │                                                                       │ │
│  │  From Transformer: Which past transactions mattered?                 │ │
│  │  From GAT: Which network neighbors influenced decision?              │ │
│  │  From Fusion: Which modality mattered most?                          │ │
│  │                                                                       │ │
│  │  Output (example):                                                   │ │
│  │  {                                                                   │ │
│  │    "modality_weights": {                                             │ │
│  │      "tabular": 0.15,                                                │ │
│  │      "sequential": 0.50,  // Behavioral pattern most important      │ │
│  │      "graph": 0.35        // Network connections also important     │ │
│  │    },                                                                │ │
│  │    "important_past_txns": [                                          │ │
│  │      {"idx": -1, "weight": 0.3, "event": "password_change"},        │ │
│  │      {"idx": -2, "weight": 0.25, "event": "card_added"},            │ │
│  │      {"idx": -3, "weight": 0.2, "event": "login_new_device"}        │ │
│  │    ]                                                                 │ │
│  │  }                                                                   │ │
│  │                                                                       │ │
│  │  TECH: PyTorch (extract attention weights from layers)               │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                    MISTRAL 7B COPILOT                                 │ │
│  │                                                                       │ │
│  │  Purpose: Generate natural language investigation reports            │ │
│  │                                                                       │ │
│  │  Input Context (fed to Mistral):                                     │ │
│  │  ├── Transaction details                                             │ │
│  │  ├── Risk score + fraud probability                                  │ │
│  │  ├── Top SHAP features                                               │ │
│  │  ├── Fraud type prediction                                           │ │
│  │  └── Similar historical cases (from RAG)                             │ │
│  │                                                                       │ │
│  │  Output:                                                             │ │
│  │  "This transaction was flagged as a potential Account Takeover.      │ │
│  │   Key indicators:                                                    │ │
│  │   1. New device detected (never seen for this account)               │ │
│  │   2. Password was changed 2 hours before this transaction            │ │
│  │   3. Transaction amount is 100x the user's average                   │ │
│  │   4. Device shared with 3 other recently flagged accounts            │ │
│  │                                                                       │ │
│  │   Similar case #4521 (94% match) was confirmed as ATO.               │ │
│  │   Recommendation: BLOCK and trigger account security review."        │ │
│  │                                                                       │ │
│  │  TECH: Mistral 7B (local) + LoRA fine-tuning                         │ │
│  │  FINE-TUNING: 500 fraud investigation QA pairs                       │ │
│  │  TIME: 2-4 hours                                                      │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        RAG (Similar Cases)                            │ │
│  │                                                                       │ │
│  │  Purpose: Retrieve similar historical fraud cases for context        │ │
│  │                                                                       │ │
│  │  How it works:                                                       │ │
│  │  1. Embed current transaction features using Sentence Transformers   │ │
│  │  2. Search ChromaDB for similar past cases                           │ │
│  │  3. Return top 5 matches with their outcomes                         │ │
│  │  4. Include in Mistral context for better report generation          │ │
│  │                                                                       │ │
│  │  TECH: ChromaDB + Sentence Transformers (all-MiniLM-L6-v2)           │ │
│  │  TRAINING: No training (pre-trained model)                           │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""

# ──────────────────────────────────────────────────────────────────────────────
# 4.6 FRONTEND VISUALIZATION LAYER
# ──────────────────────────────────────────────────────────────────────────────
"""
PURPOSE: Interactive dashboard for analysts and demo

COMPONENTS:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │              VIEW 1: LIVE TRANSACTION STREAM                          │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │ TXN-12345 │ $2,450 │ Amazon │ Risk: 23% │ ✓ ALLOW │ 12ms      │ │ │
│  │  │ TXN-12346 │ $49,990│ Crypto │ Risk: 94% │ ✗ BLOCK │ 47ms      │ │ │
│  │  │ TXN-12347 │ $150   │ Uber   │ Risk: 12% │ ✓ ALLOW │ 8ms       │ │ │
│  │  │ TXN-12348 │ $5,000 │ Transfer│ Risk: 67%│ ? MFA   │ 32ms      │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  Features:                                                           │ │
│  │  ├── Real-time WebSocket updates                                     │ │
│  │  ├── Color-coded by risk (green/yellow/red)                          │ │
│  │  ├── Click to expand for details                                     │ │
│  │  └── Infinite scroll                                                 │ │
│  │                                                                       │ │
│  │  TECH: React + WebSocket + Framer Motion                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │              VIEW 2: NETWORK GRAPH VISUALIZATION                      │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │                    (Interactive Graph)                          │ │ │
│  │  │                                                                 │ │ │
│  │  │      [ACC-001]────────[DEVICE-A]────────[ACC-002]              │ │ │
│  │  │          │                 │                │                  │ │ │
│  │  │          │            [IP-VPN-X]            │                  │ │ │
│  │  │          │                 │                │                  │ │ │
│  │  │      [CARD-1234]      [ACC-003]────────[ACC-004]              │ │ │
│  │  │                                                                 │ │ │
│  │  │      🔴 Fraud cluster detected (4 accounts, 1 device)         │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  Features:                                                           │ │
│  │  ├── Real-time graph updates as transactions flow                    │ │
│  │  ├── Fraud clusters highlighted in red                               │ │
│  │  ├── Hover for node details                                          │ │
│  │  ├── Click to investigate cluster                                    │ │
│  │  └── Zoom/pan/drag                                                   │ │
│  │                                                                       │ │
│  │  TECH: Cytoscape.js or react-force-graph                             │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │              VIEW 3: INVESTIGATION PANEL                              │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  TRANSACTION: TXN-12346                                        │ │ │
│  │  │  ─────────────────────────────────────────────────────────────│ │ │
│  │  │                                                                 │ │ │
│  │  │  DECISION: 🚫 BLOCK                    RISK SCORE: 94/100      │ │ │
│  │  │  FRAUD TYPE: Account Takeover          CONFIDENCE: 97%        │ │ │
│  │  │                                                                 │ │ │
│  │  │  TOP RISK FACTORS:                                             │ │ │
│  │  │  ████████████████████ Device Sharing    +19%                  │ │ │
│  │  │  ███████████████████  New Device        +18%                  │ │ │
│  │  │  ███████████████      Amount Anomaly    +15%                  │ │ │
│  │  │  ████████████         Threshold Evasion +12%                  │ │ │
│  │  │  ██████████           VPN Detected      +10%                  │ │ │
│  │  │                                                                 │ │ │
│  │  │  [🤖 Generate AI Report]   [📊 View History]   [⚠️ Flag]      │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  AI INVESTIGATION REPORT (Mistral 7B):                         │ │ │
│  │  │  ─────────────────────────────────────────────────────────────│ │ │
│  │  │  This transaction exhibits classic Account Takeover patterns:  │ │ │
│  │  │                                                                 │ │ │
│  │  │  1. New device (DEVICE-ABCD) never seen for this account       │ │ │
│  │  │  2. Password changed 2 hours ago (suspicious timing)           │ │ │
│  │  │  3. Amount (₹49,990) is 100x user's average (₹500)            │ │ │
│  │  │  4. Device shared with 3 accounts flagged in last 24 hours    │ │ │
│  │  │                                                                 │ │ │
│  │  │  Similar Case: #4521 (94% match) - Confirmed ATO               │ │ │
│  │  │  Recommendation: Block and trigger security review             │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │              VIEW 4: ATTACK SIMULATOR (Demo Feature)                  │ │
│  │                                                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │ │
│  │  │  ATTACK SCENARIOS:                                              │ │ │
│  │  │                                                                 │ │ │
│  │  │  [🎯 Credential Stuffing]  [💳 Card Testing]                   │ │ │
│  │  │  [🔗 Fraud Ring]           [🚨 Account Takeover]                │ │ │
│  │  │                                                                 │ │ │
│  │  │  SIMULATION CONTROLS:                                          │ │ │
│  │  │  ├── Transactions/sec: [▓▓▓▓▓░░░░░] 50/s                      │ │ │
│  │  │  └── Attack intensity: [▓▓▓▓▓▓▓░░░] High                       │ │ │
│  │  │                                                                 │ │ │
│  │  │  [▶️ START SIMULATION]  [⏹ STOP]  [🔄 RESET]                   │ │ │
│  │  └─────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                       │ │
│  │  What happens when "Fraud Ring" is clicked:                          │ │
│  │  1. Simulator generates 20 coordinated fake accounts                 │ │
│  │  2. All use same device fingerprint                                  │ │
│  │  3. Circular transfers between accounts                              │ │
│  │  4. Graph visualization lights up with new cluster                   │ │
│  │  5. System detects and blocks within seconds                         │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  TECH STACK:                                                                │
│  ├── React 19 + TypeScript                                                 │
│  ├── Tailwind CSS + shadcn/ui (or neo-brutalist theme revamp)              │
│  ├── Cytoscape.js (graph visualization)                                    │
│  ├── Recharts (charts and metrics)                                         │
│  ├── Framer Motion (animations)                                            │
│  └── WebSocket (real-time updates)                                         │
│                                                                             │
│  THEME RECOMMENDATION:                                                      │
│  ├── Keep neo-brutalist for bold visual impact                             │
│  ├── Change color scheme:                                                  │ 
│  │   ├── Primary: Deep red (#DC2626) for danger/fraud                      │
│  │   ├── Secondary: Cyan (#06B6D4) for safe/allow                          │
│  │   └── Accent: Yellow (#FACC15) for warning/MFA                          │
│  └── Add "cybersecurity" feel (dark mode, terminal-like fonts)             │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""

# ──────────────────────────────────────────────────────────────────────────────
# 4.7 DATABASE LAYER
# ──────────────────────────────────────────────────────────────────────────────
"""
PURPOSE: Persistent storage for transactions, users, models, cases

DATABASES:
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                       POSTGRESQL                                      │ │
│  │                                                                       │ │
│  │  TABLES:                                                              │ │
│  │  ├── transactions (id, user_id, amount, merchant, timestamp, ...)    │ │
│  │  ├── users (id, email, phone, account_created, ...)                  │ │
│  │  ├── devices (id, fingerprint, first_seen, account_count, ...)       │ │
│  │  ├── fraud_indicators (id, type, value, risk_score, ...)             │ │
│  │  ├── cases (id, transaction_id, decision, analyst_notes, ...)        │ │
│  │  └── user_history (user_id, avg_amount, typical_hours, ...)          │ │
│  │                                                                       │ │
│  │  USE CASE: Primary data store, historical queries                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                          REDIS                                        │ │
│  │                                                                       │ │
│  │  DATA STRUCTURES:                                                     │ │
│  │  ├── user:{id}:history (Hash - last 50 txns, velocities)             │ │
│  │  ├── user:{id}:devices (Set - known devices)                         │ │
│  │  ├── device:{id}:accounts (Set - accounts using device)              │ │
│  │  ├── fraud_indicators (Set - blocked IPs, devices)                   │ │
│  │  ├── stream:transactions (Stream - real-time txn queue)              │ │
│  │  └── rl_policy (Hash - RL agent state)                               │ │
│  │                                                                       │ │
│  │  USE CASE: Real-time cache, user history, WebSocket pub/sub          │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                        CHROMADB                                       │ │
│  │                                                                       │ │
│  │  COLLECTIONS:                                                         │ │
│  │  └── fraud_cases (embeddings of historical cases for RAG)            │ │
│  │                                                                       │ │
│  │  USE CASE: Semantic search for similar past cases                    │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# 5. DATA FLOW DIAGRAM
# ============================================================================
"""
COMPLETE DATA FLOW (End-to-End):

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  STEP 1: TRANSACTION ARRIVES                                                │
│  ───────────────────────────────────────────────────────────────────────   │
│                                                                             │
│  Payment Gateway ──POST /api/transaction──► FastAPI                        │
│                                                │                           │
│                                                ▼                           │
│                                         Pydantic Validation                │
│                                                │                           │
│                                         (5ms)  │                           │
│                                                ▼                           │
│                                                                             │
│  STEP 2: ENRICH WITH HISTORY                                                │
│  ───────────────────────────────────────────────────────────────────────   │
│                                                                             │
│                    ┌─────────────────────────────────────────┐             │
│                    │              PARALLEL FETCH              │             │
│                    │                                          │             │
│                    │  Redis ──► User History (last 50 txns)  │             │
│                    │  Redis ──► Known Devices                │             │
│                    │  Redis ──► Velocity Counters            │             │
│                    │  PostgreSQL ──► Account Info            │             │
│                    │                                          │             │
│                    └─────────────────────────────────────────┘             │
│                                                │                           │
│                                         (10ms) │                           │
│                                                ▼                           │
│                                                                             │
│  STEP 3: FEATURE EXTRACTION                                                 │
│  ───────────────────────────────────────────────────────────────────────   │
│                                                                             │
│                    ┌─────────────────────────────────────────┐             │
│                    │         FeatureExtractor.extract()      │             │
│                    │                                          │             │
│                    │  52 numerical features + 5 categorical  │             │
│                    │                                          │             │
│                    │  Behavioral: velocity, impossible_travel │             │
│                    │  Device: is_new, device_sharing          │             │
│                    │  Network: is_vpn, ip_geo_mismatch        │             │
│                    │  Identity: account_age, recent_changes   │             │
│                    │  Transactional: threshold_evasion        │             │
│                    └─────────────────────────────────────────┘             │
│                                                │                           │
│                                         (10ms) │                           │
│                                                ▼                           │
│                                                                             │
│  STEP 4: BUILD SEQUENCE & GRAPH                                             │
│  ───────────────────────────────────────────────────────────────────────   │
│                                                                             │
│         Transaction Sequence                  Transaction Graph            │
│    ┌─────────────────────────┐          ┌─────────────────────────┐       │
│    │ [txn_-50, txn_-49, ...  │          │ Nodes: ACC, DEV, IP     │       │
│    │  txn_-2, txn_-1, txn_0] │          │ Edges: uses, transacts  │       │
│    │                         │          │                         │       │
│    │ Shape: [1, 50, 32]      │          │ Subgraph around user    │       │
│    └─────────────────────────┘          └─────────────────────────┘       │
│                                                │                           │
│                                         (5ms)  │                           │
│                                                ▼                           │
│                                                                             │
│  STEP 5: MODEL INFERENCE (GPU)                                              │
│  ───────────────────────────────────────────────────────────────────────   │
│                                                                             │
│         ┌─────────┐        ┌─────────┐        ┌─────────┐                 │
│         │ TABULAR │        │SEQUENCE │        │  GRAPH  │                 │
│         │ ENCODER │        │TRANSFORM│        │   GNN   │                 │
│         └────┬────┘        └────┬────┘        └────┬────┘                 │
│              │                  │                  │                       │
│              │    128-dim       │    128-dim       │    128-dim           │
│              │                  │                  │                       │
│              └──────────────────┼──────────────────┘                       │
│                                 │                                          │
│                                 ▼                                          │
│                    ┌─────────────────────────────┐                         │
│                    │     CROSS-MODAL FUSION      │                         │
│                    │        (256-dim)            │                         │
│                    └─────────────┬───────────────┘                         │
│                                  │                                          │
│              ┌───────────────────┼───────────────────┐                     │
│              │           │       │       │           │                     │
│              ▼           ▼       ▼       ▼           ▼                     │
│         ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐            │
│         │ FRAUD  │ │ TYPE   │ │ SCORE  │ │  MFA   │ │EXPLAIN │            │
│         │ 0.94   │ │  ATO   │ │  91    │ │ BLOCK  │ │ SHAP   │            │
│         └────────┘ └────────┘ └────────┘ └────────┘ └────────┘            │
│                                                │                           │
│                                         (20ms) │                           │
│                                                ▼                           │
│                                                                             │
│  STEP 6: DECISION ENGINE                                                    │
│  ───────────────────────────────────────────────────────────────────────   │
│                                                                             │
│                    ┌─────────────────────────────────────────┐             │
│                    │  Rule Engine: Check fraud_db, patterns  │             │
│                    │  RL Agent: Get adaptive threshold       │             │
│                    │  Fraud Chain: Check ATO/card testing    │             │
│                    │                                          │             │
│                    │  FINAL: adjusted_score (91) > threshold │             │
│                    │         → DECISION: BLOCK               │             │
│                    └─────────────────────────────────────────┘             │
│                                                │                           │
│                                         (5ms)  │                           │
│                                                ▼                           │
│                                                                             │
│  STEP 7: RESPONSE                                                           │
│  ───────────────────────────────────────────────────────────────────────   │
│                                                                             │
│                    {                                                        │
│                      "transaction_id": "TXN-12346",                        │
│                      "decision": "BLOCK",                                  │
│                      "risk_score": 91,                                     │
│                      "fraud_probability": 0.94,                            │
│                      "fraud_type": "ACCOUNT_TAKEOVER",                     │
│                      "explanation": {                                      │
│                        "top_factors": [                                    │
│                          {"feature": "device_sharing", "impact": 0.19},   │
│                          {"feature": "new_device", "impact": 0.18},       │
│                          {"feature": "amount_anomaly", "impact": 0.15}    │
│                        ]                                                   │
│                      },                                                    │
│                      "processing_time_ms": 55                              │
│                    }                                                        │
│                                                │                           │
│                                                ▼                           │
│                                                                             │
│  STEP 8: POST-PROCESSING (Async)                                            │
│  ───────────────────────────────────────────────────────────────────────   │
│                                                                             │
│                    ┌─────────────────────────────────────────┐             │
│                    │  • Update Redis (user history, velocity) │             │
│                    │  • Store in PostgreSQL                   │             │
│                    │  • Update graph (new edges)              │             │
│                    │  • WebSocket push to dashboard           │             │
│                    │  • If blocked: add to fraud_indicators  │             │
│                    │  • Update RL agent with feedback         │             │
│                    └─────────────────────────────────────────┘             │
│                                                                             │
│  TOTAL LATENCY: ~55ms (Target: <100ms) ✓                                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# 6. COMPONENT SPECIFICATIONS
# ============================================================================
"""
See detailed specifications in training/configs/training_config.yaml
"""


# ============================================================================
# 7. TECHNOLOGY STACK MAPPING
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────────────┐
│ LAYER              │ TECHNOLOGY              │ PURPOSE                     │
├────────────────────┼─────────────────────────┼─────────────────────────────┤
│ Frontend           │ React 19 + TypeScript   │ Dashboard UI                │
│                    │ Tailwind CSS            │ Styling (neo-brutalist)     │
│                    │ Cytoscape.js            │ Graph visualization         │
│                    │ Recharts                │ Charts and metrics          │
│                    │ Framer Motion           │ Animations                  │
│                    │ WebSocket               │ Real-time updates           │
├────────────────────┼─────────────────────────┼─────────────────────────────┤
│ Backend API        │ FastAPI                 │ REST + WebSocket server     │
│                    │ Pydantic                │ Schema validation           │
│                    │ Uvicorn                 │ ASGI server                 │
├────────────────────┼─────────────────────────┼─────────────────────────────┤
│ ML Framework       │ PyTorch                 │ Deep learning               │
│                    │ PyTorch Geometric       │ Graph neural networks       │
│                    │ XGBoost                 │ Gradient boosting baseline  │
│                    │ SHAP                    │ Feature attribution         │
│                    │ scikit-learn            │ Preprocessing               │
├────────────────────┼─────────────────────────┼─────────────────────────────┤
│ LLM                │ Mistral 7B (local)      │ Investigation reports       │
│                    │ PEFT (LoRA)             │ Fine-tuning                 │
│                    │ Sentence Transformers   │ Embeddings for RAG          │
├────────────────────┼─────────────────────────┼─────────────────────────────┤
│ Database           │ PostgreSQL              │ Primary data store          │
│                    │ Redis                   │ Cache, real-time            │
│                    │ ChromaDB                │ Vector store for RAG        │
├────────────────────┼─────────────────────────┼─────────────────────────────┤
│ ML Ops             │ Weights & Biases        │ Experiment tracking         │
├────────────────────┼─────────────────────────┼─────────────────────────────┤
│ Data Generation    │ Faker                   │ Synthetic transactions      │
│                    │ IEEE-CIS Dataset        │ Training data               │
│                    │ PaySim Dataset          │ Training data               │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# 8. TRAINING VS FINE-TUNING BREAKDOWN
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────────────┐
│ COMPONENT              │ TRAINING TYPE      │ DATASET         │ TIME      │
├────────────────────────┼────────────────────┼─────────────────┼───────────┤
│ XGBoost Baseline       │ TRAIN FROM SCRATCH │ IEEE-CIS+PaySim │ 5-10 min  │
│ Tabular Encoder        │ TRAIN FROM SCRATCH │ Same            │ 30-60 min │
│ Sequence Transformer   │ TRAIN FROM SCRATCH │ Txn sequences   │ 2-4 hours │
│ Graph Attention (GAT)  │ TRAIN FROM SCRATCH │ Txn graph       │ 1-2 hours │
│ Multi-Modal Fusion     │ TRAIN FROM SCRATCH │ All combined    │ 2-3 hours │
│ RL Threshold Agent     │ ONLINE LEARNING    │ During inference│ N/A       │
├────────────────────────┼────────────────────┼─────────────────┼───────────┤
│ Mistral 7B             │ FINE-TUNE (LoRA)   │ 500 QA pairs    │ 2-4 hours │
├────────────────────────┼────────────────────┼─────────────────┼───────────┤
│ Sentence Transformers  │ PRE-TRAINED (none) │ N/A             │ N/A       │
└─────────────────────────────────────────────────────────────────────────────┘

TOTAL TRAINING TIME: ~8-14 hours (run overnight on RTX 5050)

WHAT "TRAINING FROM SCRATCH" MEANS:
- Initialize random weights
- Feed dataset through model
- Compute loss, backpropagate gradients
- Update weights
- Repeat for many epochs until convergence
- Save trained model weights to .pt file

WHAT "FINE-TUNING (LoRA)" MEANS:
- Load pre-trained Mistral 7B weights
- Freeze most parameters
- Add small trainable adapters (LoRA: Low-Rank Adaptation)
- Train only adapters on fraud-specific data
- Result: Domain-specific LLM with minimal training
"""


# ============================================================================
# 9. TIME ESTIMATES
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────────────┐
│ PHASE                              │ TIME ESTIMATE  │ WHO                   │
├────────────────────────────────────┼────────────────┼───────────────────────┤
│ PHASE 1: SETUP                     │                │                       │
│ ├── Environment setup              │ 30 min         │ You                   │
│ ├── Download datasets              │ 30 min         │ You                   │
│ └── Database setup                 │ 30 min         │ Kumud                 │
│                                    │                │                       │
│ PHASE 2: TRAINING (Overnight)      │                │                       │
│ ├── XGBoost baseline               │ 10 min         │ GPU (auto)            │
│ ├── Tabular encoder                │ 60 min         │ GPU (auto)            │
│ ├── Sequence transformer           │ 3 hours        │ GPU (auto)            │
│ ├── Graph model                    │ 2 hours        │ GPU (auto)            │
│ ├── Fusion model                   │ 2 hours        │ GPU (auto)            │
│ └── Mistral fine-tuning            │ 3 hours        │ GPU (auto)            │
│                                    │ TOTAL: ~10 hrs │ (Run overnight)       │
│                                    │                │                       │
│ PHASE 3: BACKEND                   │                │                       │
│ ├── FastAPI endpoints              │ 2 hours        │ Kumud                 │
│ ├── WebSocket handler              │ 1 hour         │ Kumud                 │
│ ├── Feature extraction pipeline    │ 2 hours        │ You                   │
│ ├── Model inference pipeline       │ 2 hours        │ You                   │
│ └── Simulator engine               │ 2 hours        │ You                   │
│                                    │                │                       │
│ PHASE 4: FRONTEND                  │                │                       │
│ ├── Dashboard layout revamp        │ 2 hours        │ Kumud                 │
│ ├── Transaction stream             │ 2 hours        │ Kumud                 │
│ ├── Graph visualization            │ 3 hours        │ Kumud                 │
│ ├── Investigation panel            │ 2 hours        │ Kumud                 │
│ └── Attack simulator UI            │ 1 hour         │ Kumud                 │
│                                    │                │                       │
│ PHASE 5: INTEGRATION               │                │                       │
│ ├── Connect frontend to backend    │ 2 hours        │ Both                  │
│ ├── Test all flows                 │ 2 hours        │ Both                  │
│ └── Bug fixes                      │ 2 hours        │ Both                  │
│                                    │                │                       │
│ PHASE 6: DEMO PREP                 │                │                       │
│ ├── Demo script                    │ 1 hour         │ You                   │
│ └── PPT slides                     │ 1 hour         │ Kumud                 │
├────────────────────────────────────┼────────────────┼───────────────────────┤
│ TOTAL (Excluding overnight train)  │ ~24 hours      │                       │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# 10. PHASE-WISE IMPLEMENTATION PLAN
# ============================================================================
"""
═══════════════════════════════════════════════════════════════════════════════
PHASE 1: SETUP (Hour 0-1)
═══════════════════════════════════════════════════════════════════════════════

OBJECTIVE: Get environment ready, download data

TASKS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ TASK                           │ COMMAND/ACTION                             │
├────────────────────────────────┼────────────────────────────────────────────┤
│ Create Python venv             │ python -m venv sentinel_env               │
│ Install dependencies           │ pip install -r requirements.txt           │
│ Download IEEE-CIS dataset      │ kaggle datasets download ieee-fraud       │
│ Download PaySim dataset        │ kaggle datasets download paysim          │
│ Setup PostgreSQL               │ docker run postgres                       │
│ Setup Redis                    │ docker run redis                          │
│ Verify GPU access              │ python -c "import torch; print(torch...)" │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
PHASE 2: DATA PREPARATION (Hour 1-2)
═══════════════════════════════════════════════════════════════════════════════

OBJECTIVE: Prepare datasets for training

TASKS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ TASK                           │ FILE                                       │
├────────────────────────────────┼────────────────────────────────────────────┤
│ Load and merge datasets        │ training/scripts/prepare_data.py          │
│ Create transaction sequences   │ training/scripts/create_sequences.py      │
│ Build transaction graph        │ training/scripts/build_graph.py           │
│ Split train/val/test           │ training/scripts/split_data.py            │
│ Create Mistral fine-tune data  │ training/scripts/create_qa_pairs.py       │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
PHASE 3: MODEL TRAINING (Hour 2-12, Overnight)
═══════════════════════════════════════════════════════════════════════════════

OBJECTIVE: Train all models

TASKS (Run Sequentially):
┌─────────────────────────────────────────────────────────────────────────────┐
│ STEP │ SCRIPT                          │ TIME   │ OUTPUT                   │
├──────┼─────────────────────────────────┼────────┼──────────────────────────┤
│ 1    │ train_xgboost.py               │ 10 min │ xgboost_baseline.json    │
│ 2    │ train_tabular_encoder.py       │ 1 hr   │ tabular_encoder.pt       │
│ 3    │ train_sequence_transformer.py  │ 3 hrs  │ sequence_transformer.pt  │
│ 4    │ train_gnn.py                   │ 2 hrs  │ graph_model.pt           │
│ 5    │ train_fusion.py                │ 2 hrs  │ fusion_model.pt          │
│ 6    │ finetune_mistral.py            │ 3 hrs  │ mistral_fraud_adapter/   │
└─────────────────────────────────────────────────────────────────────────────┘

MONITORING: Weights & Biases dashboard
COMMAND: python training/scripts/train_all.py (runs all in sequence)


═══════════════════════════════════════════════════════════════════════════════
PHASE 4: BACKEND DEVELOPMENT (Hour 4-10, Parallel with Training)
═══════════════════════════════════════════════════════════════════════════════

OBJECTIVE: Build FastAPI backend

YOUR TASKS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ FILE                                  │ CONTENT                             │
├───────────────────────────────────────┼─────────────────────────────────────┤
│ backend/ml_pipeline/feature_extractor.py │ Feature extraction (DONE)       │
│ backend/ml_pipeline/model_inference.py│ Load models, run inference         │
│ backend/ml_pipeline/graph_builder.py  │ Build/update transaction graph     │
│ simulator/data_generator.py           │ Generate fake transactions         │
│ simulator/attack_scenarios.py         │ Attack injection logic             │
└─────────────────────────────────────────────────────────────────────────────┘

KUMUD'S TASKS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ FILE                                  │ CONTENT                             │
├───────────────────────────────────────┼─────────────────────────────────────┤
│ backend/main.py                       │ FastAPI app setup                   │
│ backend/api/routes.py                 │ REST endpoints                      │
│ backend/api/websocket.py              │ WebSocket handler                   │
│ backend/utils/database.py             │ PostgreSQL + Redis connections      │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
PHASE 5: FRONTEND DEVELOPMENT (Hour 4-14, Parallel)
═══════════════════════════════════════════════════════════════════════════════

OBJECTIVE: Revamp existing frontend for fraud detection

KUMUD'S TASKS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ COMPONENT                             │ BASED ON                            │
├───────────────────────────────────────┼─────────────────────────────────────┤
│ Dashboard layout                      │ Existing cognistream dashboard      │
│ TransactionStream.tsx                 │ Similar to patient list             │
│ NetworkGraph.tsx                      │ New (Cytoscape.js)                  │
│ InvestigationPanel.tsx                │ Similar to patient detail           │
│ AttackSimulator.tsx                   │ New component                       │
│ MetricsPanel.tsx                      │ Similar to stats cards              │
│ Theme colors                          │ Update tailwind.config.js           │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
PHASE 6: INTEGRATION (Hour 14-20)
═══════════════════════════════════════════════════════════════════════════════

OBJECTIVE: Connect everything together

TASKS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ TASK                                  │ WHO                                 │
├───────────────────────────────────────┼─────────────────────────────────────┤
│ Load trained models into inference    │ You                                 │
│ Connect frontend WebSocket to backend │ Kumud                               │
│ Test transaction flow end-to-end      │ Both                                │
│ Test attack simulation                │ Both                                │
│ Test Mistral report generation        │ You                                 │
│ Fix bugs                              │ Both                                │
└─────────────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════
PHASE 7: DEMO PREPARATION (Hour 20-24)
═══════════════════════════════════════════════════════════════════════════════

OBJECTIVE: Prepare for presentation

TASKS:
┌─────────────────────────────────────────────────────────────────────────────┐
│ TASK                                  │ WHO                                 │
├───────────────────────────────────────┼─────────────────────────────────────┤
│ Write demo script (5-min flow)        │ You                                 │
│ Create PPT slides (7 slides)          │ Kumud                               │
│ Practice demo                         │ Both                                │
│ Backup plan if something breaks       │ Both                                │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# 11. WORK DIVISION (You vs Kumud)
# ============================================================================
"""
┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║                         YOUR TASKS (ML/DL Lead)                       ║ │
│  ╠═══════════════════════════════════════════════════════════════════════╣ │
│  ║                                                                       ║ │
│  ║  PHASE 1: Setup                                                       ║ │
│  ║  ├── Python environment setup                                         ║ │
│  ║  ├── Download and prepare datasets                                    ║ │
│  ║  └── Verify GPU training works                                        ║ │
│  ║                                                                       ║ │
│  ║  PHASE 2: Training (Overnight)                                        ║ │
│  ║  ├── Write all training scripts                                       ║ │
│  ║  ├── Configure Weights & Biases                                       ║ │
│  ║  ├── Start training, monitor                                          ║ │
│  ║  └── Fine-tune Mistral 7B                                             ║ │
│  ║                                                                       ║ │
│  ║  PHASE 3: ML Pipeline                                                 ║ │
│  ║  ├── Feature extraction pipeline (DONE)                               ║ │
│  ║  ├── Model inference pipeline                                         ║ │
│  ║  ├── Graph building/updating                                          ║ │
│  ║  ├── SHAP explainability                                              ║ │
│  ║  └── Mistral integration for reports                                  ║ │
│  ║                                                                       ║ │
│  ║  PHASE 4: Simulator                                                   ║ │
│  ║  ├── Transaction generator                                            ║ │
│  ║  └── Attack scenario injection                                        ║ │
│  ║                                                                       ║ │
│  ║  PHASE 5: Demo                                                        ║ │
│  ║  └── Demo script and presentation                                     ║ │
│  ║                                                                       ║ │
│  ╚═══════════════════════════════════════════════════════════════════════╝ │
│                                                                             │
│  ╔═══════════════════════════════════════════════════════════════════════╗ │
│  ║                      KUMUD'S TASKS (Frontend/Backend)                 ║ │
│  ╠═══════════════════════════════════════════════════════════════════════╣ │
│  ║                                                                       ║ │
│  ║  PHASE 1: Setup                                                       ║ │
│  ║  ├── Docker setup (PostgreSQL, Redis)                                 ║ │
│  ║  └── Database schema creation                                         ║ │
│  ║                                                                       ║ │
│  ║  PHASE 2: Backend API                                                 ║ │
│  ║  ├── FastAPI main.py setup                                            ║ │
│  ║  ├── REST endpoints (routes.py)                                       ║ │
│  ║  ├── WebSocket handler                                                ║ │
│  ║  └── Database utilities                                               ║ │
│  ║                                                                       ║ │
│  ║  PHASE 3: Frontend                                                    ║ │
│  ║  ├── Revamp cognistream for fraud theme                               ║ │
│  ║  ├── TransactionStream component                                      ║ │
│  ║  ├── NetworkGraph component (Cytoscape)                               ║ │
│  ║  ├── InvestigationPanel component                                     ║ │
│  ║  ├── AttackSimulator component                                        ║ │
│  ║  └── Color scheme updates                                             ║ │
│  ║                                                                       ║ │
│  ║  PHASE 4: Integration                                                 ║ │
│  ║  └── Connect frontend to backend WebSocket                            ║ │
│  ║                                                                       ║ │
│  ║  PHASE 5: Demo                                                        ║ │
│  ║  └── PPT slides                                                       ║ │
│  ║                                                                       ║ │
│  ╚═══════════════════════════════════════════════════════════════════════╝ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# 12. X-FACTORS & DIFFERENTIATORS
# ============================================================================
"""
What makes SENTINEL different from what other teams will build:

┌─────────────────────────────────────────────────────────────────────────────┐
│                                                                             │
│  X-FACTOR 1: FRAUD CHAIN DETECTION                                         │
│  ─────────────────────────────────────────────────────────────────────────│
│  Others: Look at individual transactions in isolation                      │
│  Us: Detect SEQUENCES (ATO: login → pwd change → card add → transfer)     │
│  Tech: Transformer learns temporal attack patterns                         │
│                                                                             │
│  X-FACTOR 2: REAL-TIME GRAPH EVOLUTION                                     │
│  ─────────────────────────────────────────────────────────────────────────│
│  Others: Static graph snapshot (if they even have graph)                   │
│  Us: Graph updates LIVE during demo, fraud clusters light up in red       │
│  Tech: Graph Neural Network + Real-time visualization                      │
│                                                                             │
│  X-FACTOR 3: THREE-TIER DECISION (Not Binary)                              │
│  ─────────────────────────────────────────────────────────────────────────│
│  Others: Block or Allow (binary)                                           │
│  Us: Allow / Trigger MFA / Block (three tiers with RL-learned thresholds) │
│  Tech: Reinforcement Learning (Contextual Bandit)                          │
│                                                                             │
│  X-FACTOR 4: LOCAL LLM (Not API)                                           │
│  ─────────────────────────────────────────────────────────────────────────│
│  Others: ChatGPT API wrapper (if they have LLM at all)                     │
│  Us: Local Mistral 7B, fine-tuned on fraud terminology                     │
│  Tech: LoRA fine-tuning, no API dependency                                 │
│                                                                             │
│  X-FACTOR 5: ATTACK SIMULATION (Demo Killer)                               │
│  ─────────────────────────────────────────────────────────────────────────│
│  Others: Show static pre-recorded results                                  │
│  Us: Judge clicks "Inject Fraud Ring" → System catches in real-time       │
│  Tech: Simulator engine with multiple attack scenarios                     │
│                                                                             │
│  X-FACTOR 6: PRODUCTION-GRADE ARCHITECTURE                                 │
│  ─────────────────────────────────────────────────────────────────────────│
│  Others: Single XGBoost model                                              │
│  Us: Multi-modal fusion, multi-task learning, modular design              │
│  Tech: Industry patterns (Stripe Radar, Feedzai inspired)                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
"""


# ============================================================================
# END OF SYSTEM ARCHITECTURE DOCUMENT
# ============================================================================

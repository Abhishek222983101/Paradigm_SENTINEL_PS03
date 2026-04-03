# 🛡️ Team Paradigm SENTINEL - PS03

> **Built during HackUp Hackathon @ A.C. Patil College of Engineering**

## 🎯 The New PS Requirements (Updated)

Here is exactly what the updated Problem Statement (PS) asks vs what we're building:

| PS Requirement | What We Build | Tech Used | Why This Tech |
| :--- | :--- | :--- | :--- |
| **"Build behavioral user profiles"** | User History tracking + Sequential Transformer | Transformer (DL) | Learns temporal patterns in user behavior |
| **"Detect fraud chains (ATO → transaction abuse)"** | Fraud Chain Detector module | Transformer + Pattern Matching | ATO is a SEQUENCE: login → pwd change → card add → transfer |
| **"Dynamic risk scoring with explanations"** | Multi-task Fusion Model + SHAP | DL + SHAP (ML) | Multiple heads output: fraud prob, type, score, explanation |
| **"Pre-transaction decisioning (approve/block/MFA)"** | RL Threshold Agent + Decision Engine | RL (ML) | Learns optimal thresholds, 3 outputs: Allow/MFA/Block |
| **"Adaptive learning for evolving fraud"** | Online RL + Continuous training hooks | RL (ML) | Agent updates policy based on feedback |
| **"Real-time fraud detection engine"** | FastAPI + WebSocket + Redis | Backend | <100ms latency requirement |
| **"Visualization/monitoring interface"** | React Dashboard | Frontend | Live stream + graph + metrics |
| **BROWNIE:** "Graph-based fraud rings" | Graph Attention Network | GNN (DL) | Detects coordinated attacks, device sharing |
| **BROWNIE:** "Synthetic identity detection" | Synthetic ID Module | ML | Detects fake identities from stolen data |
| **BROWNIE:** "Fraud simulation environment" | Attack Simulator | Backend | Inject attack scenarios in demo |

---

## 🔄 Complete Data Flow (Step by Step)

Here is exactly what happens from a transaction arriving to a decision being made:

### STEP 1: Transaction Arrives (5ms)
Payment Gateway sends a POST request to our API:
```json
{
  "transaction_id": "TXN-12345",
  "user_id": "USER-001",
  "amount": 49990,           // ← Just below ₹50,000 threshold (suspicious!)
  "merchant_category": "6051", // ← Crypto (high risk!)
  "device_id": "DEVICE-NEW",   // ← Never seen before
  "ip_address": "45.33.xx.xx", // ← VPN IP
  "timestamp": "2026-04-03T03:14:00Z" // ← 3AM (unusual hour)
}
```

### STEP 2: Feature Extraction (10ms)
Our FeatureExtractor pulls data from multiple sources:
- **FROM TRANSACTION (Direct):** `amount = 49990`, `merchant_category = "6051"`, `hour = 3`, `ip = VPN`
- **FROM REDIS CACHE (User History):** `last_txn = 5m ago (Mumbai)`, `avg_amount = ₹500 (100x spike!)`, `known_devices = ["DEVICE-OLD"]`
- **FROM DATABASE (Account Info):** `account_age = 2 days`, `password_changed = 2h ago`, `card_added = 1h ago`
- **FROM GRAPH (Network):** `device_account_count = 5`, `fraud_neighbor_count = 2`

*Output: 50+ numerical features + 5 categorical features*

### STEP 3: Model Inference (20ms)
Three branches process in parallel:

```text
┌─────────────────────────────────────────────────────────────────┐
│                     PARALLEL PROCESSING                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  BRANCH 1: TABULAR (5ms)                                        │
│  Input: 50 features + 5 categorical                             │
│  Process: Entity Embeddings → MLP                               │
│  Output: 128-dim vector                                         │
│  Learns: "This amount is 100x user's average"                   │
│                                                                 │
│  BRANCH 2: SEQUENTIAL (10ms)                                    │
│  Input: User's last 50 transactions                             │
│  Process: Transformer Encoder (6 layers, 8 heads)               │
│  Output: 128-dim vector                                         │
│  Learns: "Last 2 hours: pwd change → card add → high value"     │
│                                                                 │
│  BRANCH 3: GRAPH (15ms)                                         │
│  Input: Graph with this user's connections                      │
│  Process: 3-layer Graph Attention Network                       │
│  Output: 128-dim vector                                         │
│  Learns: "Device is shared by 5 accounts, 2 are flagged"        │
└─────────────────────────────────────────────────────────────────┘
```

### STEP 4: Fusion (5ms)
Cross-Attention merges 3 × 128-dim vectors into a 256-dim fused vector. It learns dynamic weighting (e.g., heavily weighting the Sequential branch because an ATO chain pattern was detected).

### STEP 5: Multi-Task Prediction (5ms)
- **HEAD 1 (Binary):** Is Fraud? → `0.94 probability`
- **HEAD 2 (Type):** Fraud Type → `[ATO: 0.78, Card: 0.12, ...]` (Account Takeover)
- **HEAD 3 (Risk):** Risk Score → `91/100`
- **HEAD 4 (Decision):** MFA Decision → `[Allow: 0.02, MFA: 0.08, Block: 0.90]`

### STEP 6: RL Threshold Check (2ms)
The RL Agent sets aggressive thresholds dynamically (e.g., `0.6` due to elevated night-time fraud rates).
*Decision:* Current risk score (`0.94`) > Threshold (`0.6`) → **BLOCK**

### STEP 7: Explainability Generation (10ms)
SHAP Analysis generates top contributing factors:
1. Fraud Chain Detected (ATO)  `+0.25` 
2. Device shared with 5 accounts `+0.19`
3. Amount 100x user average `+0.15`

### STEP 8: Response to Gateway (<100ms total)
```json
{
  "transaction_id": "TXN-12345",
  "decision": "BLOCK",
  "risk_score": 91,
  "fraud_probability": 0.94,
  "fraud_type": "ACCOUNT_TAKEOVER",
  "explanation": {
    "summary": "High-risk ATO pattern detected",
    "top_factors": [
      {"feature": "fraud_chain_ato", "impact": 0.25},
      {"feature": "device_sharing", "impact": 0.19}
    ]
  },
  "processing_time_ms": 47
}
```

---

## 🧠 Where Training Happens (Teaching the Model)

| Model | What It Learns | Training Dataset |
| :--- | :--- | :--- |
| **XGBoost** | "These 50 features → fraud/not fraud" | IEEE-CIS (590K transactions, labeled) |
| **Tabular Encoder** | "Merchant 'Amazon' and 'Flipkart' are similar" | Same dataset |
| **Sequence Transformer** | "pwd_change → card_add → transfer = ATO" | Transaction sequences from dataset |
| **Graph Network** | "Device shared by 5 accounts = suspicious" | Graph built from transactions |
| **Fusion Model** | "For ATO, trust sequence more than tabular" | All of above |

### Fine-Tuning = Adapting Pre-trained Model
| Model Base | What We Teach It |
| :--- | :--- |
| **Mistral 7B** (General LM) | "When you see these features, generate this investigation report" |

*Method:* 500 examples generated → Fine-tune with LoRA (only trains 0.1% of parameters, 2-4 hours).

---

## 🚀 The X-Factors Explained

**X-Factor 1: Fraud Chain Detection**
*   Other teams detect *individual* transactions. We detect **SEQUENCES**.
*   Our detection: "Login → Password Change → Card Add → High Transfer in 30 minutes" = **ATO CHAIN → BLOCK**. (Learned by Transformer).

**X-Factor 2: Real-Time Graph Evolution**
*   Other teams: Static graph snapshot.
*   Us: Graph updates **LIVE** as transactions flow. During the demo: Attack injected → Multiple red edges appear → Cluster forms → "FRAUD RING DETECTED" alert.

**X-Factor 3: Three-Tier Decision (Allow/MFA/Block)**
*   Other teams: Binary (Allow/Block).
*   Us: Three options with RL-learned thresholds.
    *   Risk < 30% → **ALLOW** (no friction)
    *   Risk 30-70% → **MFA** (trigger 2FA)
    *   Risk > 70% → **BLOCK** (immediate)

**X-Factor 4: Solana Integration (The Secret Weapon)**
*   Other teams: Mock data only.
*   Us: Real blockchain transactions flowing through our system. Shows production readiness & Web3/DeFi future-proofing.

---

## ⏱️ 24-Hour Timeline

Given the 24 hours of the hackathon and complex architecture, here's the realistic plan:

| Hour | Task | Who |
| :--- | :--- | :--- |
| **0-1** | Understand architecture fully (THIS) | You |
| **1-2** | Setup environment, download datasets | You |
| **2-4** | Write training scripts, start training | You |
| **4-8** | Training runs (overnight) | GPU |
| **4-8** | Backend API + WebSocket | Your teammate |
| **8-12** | Model inference pipeline, integrate trained models | You |
| **8-12** | Frontend dashboard (basic version) | Your teammate |
| **12-16** | Simulator + attack injection | You |
| **12-16** | Frontend graph visualization | Your teammate |
| **16-20** | Integration + testing | Both |
| **20-22** | Mistral integration (if time) | You |
| **22-24** | Demo polish + PPT | Both |




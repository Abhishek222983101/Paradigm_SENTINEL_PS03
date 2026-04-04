# ═══════════════════════════════════════════════════════════════════════════
# SENTINEL MOCK DATA GENERATOR
# Financial Fraud Intelligence Platform - Faker-based Mock Data Generation
# ═══════════════════════════════════════════════════════════════════════════

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from faker import Faker

# Initialize Faker with multiple locales for realistic international data
fake = Faker(['en_US', 'en_GB', 'de_DE', 'fr_FR', 'ja_JP', 'zh_CN', 'ar_AE'])


# ═══════════════════════════════════════════════════════════════════════════
# CONSTANTS & CONFIGURATIONS
# ═══════════════════════════════════════════════════════════════════════════

FRAUD_TYPES = [
    "ACCOUNT_TAKEOVER",
    "CARD_TESTING",
    "FRAUD_RING",
    "SYNTHETIC_IDENTITY",
    "MONEY_MULE",
    "LEGITIMATE"
]

ACTION_TYPES = ["ALLOW", "BLOCK", "MFA", "REVIEW"]

MERCHANTS = [
    # Tech & Electronics
    "TechStore Inc", "Apple Store", "Best Buy", "Amazon Prime", "Newegg",
    # Crypto & Finance
    "Coinbase Pro", "Binance", "Kraken", "PayPal Transfer", "Wise Transfer",
    # Retail
    "Walmart", "Target", "Costco", "IKEA", "H&M Online",
    # Travel
    "Emirates Airlines", "Booking.com", "Airbnb", "Uber", "Lyft",
    # Food & Entertainment
    "DoorDash", "Netflix", "Spotify", "Steam Games", "PlayStation Store",
    # Suspicious categories
    "Quick Cash Loans", "Gift Cards Direct", "Luxury Watches Ltd", "Gold Exchange"
]

LOCATIONS = [
    "New York, USA", "Los Angeles, USA", "London, UK", "Dubai, UAE",
    "Singapore", "Tokyo, Japan", "Berlin, Germany", "Paris, France",
    "Mumbai, India", "Sydney, Australia", "Toronto, Canada", "Sao Paulo, Brazil",
    # Suspicious locations
    "Lagos, Nigeria", "Kiev, Ukraine", "Minsk, Belarus"
]

SHAP_FEATURES = [
    "amount", "velocity", "device_age", "location_mismatch", "merchant_risk",
    "time_of_day", "device_fingerprint", "ip_reputation", "account_age",
    "transaction_frequency", "geo_distance", "card_testing_score"
]


# ═══════════════════════════════════════════════════════════════════════════
# DATA GENERATION FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════

def generate_user_id() -> str:
    """Generate a realistic user ID."""
    return f"USR-{random.randint(1000, 9999)}"


def generate_txn_id() -> str:
    """Generate a unique transaction ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    suffix = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=6))
    return f"TXN-{timestamp}-{suffix}"


def generate_device_id() -> str:
    """Generate a device fingerprint."""
    device_types = ["IPHONE", "ANDROID", "DESKTOP", "TABLET", "EMULATOR"]
    return f"DEV-{random.randint(100, 999)}-{random.choice(device_types)}"


def generate_shap_values(is_fraud: bool, fraud_type: str) -> Dict[str, float]:
    """
    Generate realistic SHAP values for explainability.
    Fraudulent transactions have stronger feature contributions.
    """
    shap_values = {}
    
    if is_fraud:
        # High-impact features for fraud
        primary_features = random.sample(SHAP_FEATURES, 4)
        for i, feature in enumerate(primary_features):
            # Primary features get higher values (0.15-0.45)
            shap_values[feature] = round(random.uniform(0.15, 0.45), 2)
        
        # Secondary features
        for feature in SHAP_FEATURES:
            if feature not in shap_values:
                shap_values[feature] = round(random.uniform(-0.08, 0.12), 2)
        
        # Fraud type specific boosting
        if fraud_type == "ACCOUNT_TAKEOVER":
            shap_values["device_fingerprint"] = round(random.uniform(0.25, 0.40), 2)
            shap_values["location_mismatch"] = round(random.uniform(0.20, 0.35), 2)
        elif fraud_type == "CARD_TESTING":
            shap_values["amount"] = round(random.uniform(0.30, 0.45), 2)
            shap_values["velocity"] = round(random.uniform(0.25, 0.40), 2)
        elif fraud_type == "FRAUD_RING":
            shap_values["device_fingerprint"] = round(random.uniform(0.20, 0.35), 2)
            shap_values["transaction_frequency"] = round(random.uniform(0.25, 0.40), 2)
    else:
        # Legitimate transactions have low, balanced SHAP values
        for feature in SHAP_FEATURES:
            shap_values[feature] = round(random.uniform(-0.05, 0.08), 2)
    
    return shap_values


def generate_transaction(
    user_id: Optional[str] = None,
    is_fraud: Optional[bool] = None,
    fraud_type: Optional[str] = None
) -> Dict:
    """
    Generate a single mock transaction with optional fraud parameters.
    
    Args:
        user_id: Optional fixed user ID (for generating user history)
        is_fraud: Force fraud status (True/False/None for random)
        fraud_type: Force fraud type if is_fraud is True
    
    Returns:
        Transaction dictionary matching the frontend schema
    """
    # Generate IDs
    txn_id = generate_txn_id()
    user_id = user_id or generate_user_id()
    device_id = generate_device_id()
    
    # Determine fraud status
    if is_fraud is None:
        # ~5% fraud rate for realistic distribution
        is_fraud = random.random() < 0.05
    
    # Generate amount based on fraud status
    if is_fraud:
        # Fraudulent transactions: bimodal distribution
        # Either very small (card testing) or very large
        if random.random() < 0.3:
            amount = round(random.uniform(0.50, 5.00), 2)  # Card testing
        else:
            amount = round(random.uniform(5000, 75000), 2)  # Large fraud
    else:
        # Normal transactions: typical distribution
        amount = round(random.uniform(10, 2500), 2)
    
    # Select location
    if is_fraud and random.random() < 0.4:
        # Fraudulent transactions more likely from suspicious locations
        location = random.choice(LOCATIONS[-3:] + LOCATIONS[:5])
    else:
        location = random.choice(LOCATIONS)
    
    # Select merchant
    if is_fraud and random.random() < 0.5:
        # Fraudulent transactions more likely to suspicious merchants
        merchant = random.choice(MERCHANTS[-4:] + MERCHANTS[:8])
    else:
        merchant = random.choice(MERCHANTS)
    
    # Generate timestamp (last 24 hours)
    timestamp = datetime.now() - timedelta(
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59)
    )
    
    # Determine fraud type and action
    if is_fraud:
        fraud_type = fraud_type or random.choice(FRAUD_TYPES[:-1])  # Exclude LEGITIMATE
        risk_score = round(random.uniform(70, 98), 1)
        
        if risk_score >= 85:
            action = "BLOCK"
        elif risk_score >= 70:
            action = random.choice(["BLOCK", "MFA"])
        else:
            action = "MFA"
    else:
        fraud_type = "LEGITIMATE"
        risk_score = round(random.uniform(2, 35), 1)
        
        if risk_score <= 20:
            action = "ALLOW"
        else:
            action = random.choice(["ALLOW", "REVIEW"])
    
    # Generate processing time (realistic ML inference latency)
    processing_time = round(random.uniform(18, 65), 1)
    
    return {
        # Transaction data
        "txn_id": txn_id,
        "timestamp": timestamp.isoformat() + "Z",
        "amount": amount,
        "currency": random.choice(["USD", "EUR", "GBP", "AED", "INR"]),
        "merchant": merchant,
        "user_id": user_id,
        "location": location,
        "device_id": device_id,
        # Prediction data
        "is_fraud": is_fraud,
        "risk_score": risk_score,
        "fraud_type": fraud_type,
        "action_taken": action,
        "shap_values": generate_shap_values(is_fraud, fraud_type),
        "processing_time_ms": processing_time
    }


def generate_transactions_batch(
    count: int = 100,
    fraud_ratio: float = 0.05
) -> List[Dict]:
    """
    Generate a batch of transactions with specified fraud ratio.
    
    Args:
        count: Number of transactions to generate
        fraud_ratio: Percentage of fraudulent transactions (0.0 to 1.0)
    
    Returns:
        List of transaction dictionaries
    """
    transactions = []
    fraud_count = int(count * fraud_ratio)
    
    # Generate fraudulent transactions
    for _ in range(fraud_count):
        txn = generate_transaction(is_fraud=True)
        transactions.append(txn)
    
    # Generate legitimate transactions
    for _ in range(count - fraud_count):
        txn = generate_transaction(is_fraud=False)
        transactions.append(txn)
    
    # Shuffle to mix fraud and legitimate
    random.shuffle(transactions)
    
    return transactions


def generate_alert_from_transaction(txn: Dict) -> Dict:
    """
    Generate a fraud alert from a flagged transaction.
    """
    return {
        "id": f"ALERT-{uuid.uuid4().hex[:8].upper()}",
        "txn_id": txn["txn_id"],
        "timestamp": txn["timestamp"],
        "risk_score": txn["risk_score"],
        "fraud_type": txn["fraud_type"],
        "user_id": txn["user_id"],
        "amount": txn["amount"],
        "currency": txn["currency"],
        "status": random.choice(["pending", "investigating"])
    }


def generate_dashboard_stats(
    total_transactions: int = 10000,
    fraud_count: int = 500
) -> Dict:
    """
    Generate mock dashboard statistics.
    """
    return {
        "total_transactions": total_transactions,
        "total_fraud_detected": fraud_count,
        "avg_latency_ms": round(random.uniform(35, 55), 1),
        "detection_rate": round((fraud_count / max(1, total_transactions)) * 100, 2),
        "false_positive_rate": round(random.uniform(1.5, 4.5), 2),
        "blocked_amount": round(random.uniform(150000, 500000), 2)
    }


# ═══════════════════════════════════════════════════════════════════════════
# ATTACK SCENARIO GENERATORS
# ═══════════════════════════════════════════════════════════════════════════

def generate_account_takeover_burst(count: int = 5) -> List[Dict]:
    """
    Generate an Account Takeover attack sequence.
    Characteristics: New device, new location, high-value transactions.
    """
    user_id = generate_user_id()
    device_id = generate_device_id().replace("IPHONE", "EMULATOR")
    suspicious_locations = ["Lagos, Nigeria", "Kiev, Ukraine", "Minsk, Belarus"]
    
    transactions = []
    base_time = datetime.now()
    
    for i in range(count):
        txn = generate_transaction(user_id=user_id, is_fraud=True, fraud_type="ACCOUNT_TAKEOVER")
        txn["device_id"] = device_id
        txn["location"] = random.choice(suspicious_locations)
        txn["amount"] = round(random.uniform(10000, 50000), 2)
        txn["risk_score"] = round(random.uniform(85, 98), 1)
        txn["action_taken"] = "BLOCK"
        txn["timestamp"] = (base_time + timedelta(minutes=i * 2)).isoformat() + "Z"
        
        # Boost relevant SHAP values
        txn["shap_values"]["device_fingerprint"] = round(random.uniform(0.30, 0.45), 2)
        txn["shap_values"]["location_mismatch"] = round(random.uniform(0.25, 0.40), 2)
        
        transactions.append(txn)
    
    return transactions


def generate_card_testing_burst(count: int = 10) -> List[Dict]:
    """
    Generate a Card Testing attack sequence.
    Characteristics: Many small transactions in quick succession.
    """
    user_id = generate_user_id()
    transactions = []
    base_time = datetime.now()
    
    for i in range(count):
        txn = generate_transaction(user_id=user_id, is_fraud=True, fraud_type="CARD_TESTING")
        txn["amount"] = round(random.uniform(0.50, 5.00), 2)
        txn["merchant"] = "Gift Cards Direct"
        txn["risk_score"] = round(random.uniform(75, 92), 1)
        txn["timestamp"] = (base_time + timedelta(seconds=i * 15)).isoformat() + "Z"
        
        # Boost relevant SHAP values
        txn["shap_values"]["velocity"] = round(random.uniform(0.35, 0.50), 2)
        txn["shap_values"]["amount"] = round(random.uniform(0.20, 0.35), 2)
        
        if i >= 7:
            txn["action_taken"] = "BLOCK"
        else:
            txn["action_taken"] = "MFA"
        
        transactions.append(txn)
    
    return transactions


def generate_fraud_ring_burst(account_count: int = 5) -> List[Dict]:
    """
    Generate a Fraud Ring attack.
    Characteristics: Multiple accounts sharing devices, circular transfers.
    """
    shared_device = generate_device_id()
    user_ids = [generate_user_id() for _ in range(account_count)]
    transactions = []
    base_time = datetime.now()
    
    # Generate circular transfers
    for i, user_id in enumerate(user_ids):
        next_user = user_ids[(i + 1) % account_count]
        
        txn = generate_transaction(user_id=user_id, is_fraud=True, fraud_type="FRAUD_RING")
        txn["device_id"] = shared_device
        txn["merchant"] = f"Transfer to {next_user}"
        txn["amount"] = round(random.uniform(2000, 8000), 2)
        txn["risk_score"] = round(random.uniform(80, 95), 1)
        txn["timestamp"] = (base_time + timedelta(minutes=i * 5)).isoformat() + "Z"
        
        # Boost relevant SHAP values
        txn["shap_values"]["device_fingerprint"] = round(random.uniform(0.30, 0.45), 2)
        txn["shap_values"]["transaction_frequency"] = round(random.uniform(0.25, 0.40), 2)
        
        transactions.append(txn)
    
    return transactions


def generate_synthetic_identity_burst(count: int = 3) -> List[Dict]:
    """
    Generate a Synthetic Identity fraud attempt.
    Characteristics: New accounts with inconsistent information.
    """
    transactions = []
    base_time = datetime.now()
    
    for i in range(count):
        user_id = generate_user_id()
        txn = generate_transaction(user_id=user_id, is_fraud=True, fraud_type="SYNTHETIC_IDENTITY")
        txn["amount"] = round(random.uniform(3000, 15000), 2)
        txn["merchant"] = random.choice(["Quick Cash Loans", "Luxury Watches Ltd", "Gold Exchange"])
        txn["risk_score"] = round(random.uniform(78, 93), 1)
        txn["timestamp"] = (base_time + timedelta(hours=i)).isoformat() + "Z"
        
        transactions.append(txn)
    
    return transactions


def inject_attack_scenario(
    scenario: str,
    intensity: str = "medium"
) -> Tuple[List[Dict], List[Dict]]:
    """
    Generate attack transactions based on scenario type.
    
    Args:
        scenario: Type of attack (account_takeover, card_testing, etc.)
        intensity: Attack intensity (low, medium, high)
    
    Returns:
        Tuple of (transactions, alerts)
    """
    intensity_multiplier = {"low": 0.5, "medium": 1.0, "high": 2.0}
    multiplier = intensity_multiplier.get(intensity, 1.0)
    
    if scenario == "account_takeover":
        txns = generate_account_takeover_burst(int(5 * multiplier))
    elif scenario == "card_testing":
        txns = generate_card_testing_burst(int(10 * multiplier))
    elif scenario == "fraud_ring":
        txns = generate_fraud_ring_burst(int(5 * multiplier))
    elif scenario == "synthetic_identity":
        txns = generate_synthetic_identity_burst(int(3 * multiplier))
    else:  # normal
        txns = generate_transactions_batch(int(10 * multiplier), fraud_ratio=0.05)
    
    # Generate alerts for high-risk transactions
    alerts = [
        generate_alert_from_transaction(txn)
        for txn in txns
        if txn.get("risk_score", 0) >= 70
    ]
    
    return txns, alerts


# ═══════════════════════════════════════════════════════════════════════════
# GRAPH DATA GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def generate_fraud_ring_graph(ring_size: int = 5) -> Dict:
    """
    Generate graph data for a fraud ring visualization.
    """
    nodes = []
    edges = []
    
    shared_device = f"DEV-{random.randint(100, 999)}-EMULATOR"
    shared_ip = f"{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}.{random.randint(1, 255)}"
    
    # Create shared device node
    nodes.append({
        "id": shared_device,
        "type": "device",
        "label": shared_device,
        "risk_score": 95,
        "is_fraud": True
    })
    
    # Create shared IP node
    nodes.append({
        "id": shared_ip,
        "type": "ip",
        "label": shared_ip,
        "risk_score": 88,
        "is_fraud": True
    })
    
    # Create user nodes and edges
    user_ids = []
    for i in range(ring_size):
        user_id = f"USR-{random.randint(1000, 9999)}"
        user_ids.append(user_id)
        
        nodes.append({
            "id": user_id,
            "type": "user",
            "label": f"Account {i + 1}",
            "risk_score": round(random.uniform(75, 95), 1),
            "is_fraud": True
        })
        
        # Connect to shared device
        edges.append({
            "id": f"edge-{user_id}-{shared_device}",
            "source": user_id,
            "target": shared_device,
            "type": "shared_device",
            "weight": 1.0
        })
        
        # Connect to shared IP
        edges.append({
            "id": f"edge-{user_id}-{shared_ip}",
            "source": user_id,
            "target": shared_ip,
            "type": "shared_ip",
            "weight": 1.0
        })
    
    # Create circular transfer edges
    for i, user_id in enumerate(user_ids):
        next_user = user_ids[(i + 1) % ring_size]
        edges.append({
            "id": f"edge-transfer-{user_id}-{next_user}",
            "source": user_id,
            "target": next_user,
            "type": "transfer",
            "weight": round(random.uniform(2000, 8000), 2)
        })
    
    return {"nodes": nodes, "edges": edges}


# ═══════════════════════════════════════════════════════════════════════════
# INVESTIGATION REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════════

def generate_mock_investigation_report(txn: Dict) -> Dict:
    """
    Generate a mock Mistral investigation report.
    In production, this would be generated by the LLM.
    """
    fraud_type = txn.get("fraud_type", "ACCOUNT_TAKEOVER")
    risk_score = txn.get("risk_score", 85)
    
    evidence_templates = {
        "ACCOUNT_TAKEOVER": [
            "New device detected (never seen for this account)",
            f"Location anomaly: Transaction from {txn.get('location', 'Unknown')} (typical: New York, USA)",
            "Password change detected 2 hours before transaction",
            f"Transaction amount (${txn.get('amount', 0):,.2f}) is 15x user's average",
        ],
        "CARD_TESTING": [
            "Multiple small transactions in rapid succession (15 txns in 3 minutes)",
            "Gift card merchant commonly associated with card testing",
            "IP address flagged in 12 previous fraud cases",
            "Transaction velocity 8x normal rate",
        ],
        "FRAUD_RING": [
            f"Device {txn.get('device_id', 'Unknown')} shared by 5 accounts",
            "Circular transfer pattern detected between connected accounts",
            "All linked accounts created within 48 hours",
            "Common IP address across all transactions",
        ],
        "SYNTHETIC_IDENTITY": [
            "Account information inconsistencies detected",
            "Email domain age: 3 days (suspicious)",
            "Phone number previously associated with fraud",
            "Address verification failed",
        ]
    }
    
    recommendation_templates = {
        "ACCOUNT_TAKEOVER": [
            "Block all pending transactions immediately",
            "Force password reset and MFA enrollment",
            "Contact customer via verified phone number",
            "Review last 30 days of account activity",
        ],
        "CARD_TESTING": [
            "Block card and issue replacement",
            "Add device to fraud blocklist",
            "Monitor linked accounts for 72 hours",
            "File SAR if total exposure exceeds $5,000",
        ],
        "FRAUD_RING": [
            "Freeze all connected accounts",
            "Escalate to Financial Crimes Unit",
            "Preserve all transaction records for investigation",
            "Report to FinCEN within 30 days",
        ],
        "SYNTHETIC_IDENTITY": [
            "Close account and reject all pending applications",
            "Add identity elements to blocklist",
            "Review credit bureau reports",
            "Report to FTC Identity Theft Resource Center",
        ]
    }
    
    return {
        "txn_id": txn.get("txn_id", "UNKNOWN"),
        "summary": f"This transaction exhibits characteristics of {fraud_type.replace('_', ' ').title()}. "
                   f"Risk score of {risk_score}/100 indicates a {('critical' if risk_score >= 85 else 'high')} threat level. "
                   f"Immediate action is recommended to prevent potential losses.",
        "evidence": evidence_templates.get(fraud_type, evidence_templates["ACCOUNT_TAKEOVER"]),
        "recommendations": recommendation_templates.get(fraud_type, recommendation_templates["ACCOUNT_TAKEOVER"]),
        "similar_cases": [
            f"Case #{random.randint(4000, 5000)} (92% match) - Confirmed {fraud_type.replace('_', ' ')}",
            f"Case #{random.randint(3000, 4000)} (87% match) - Under investigation",
            f"Case #{random.randint(2000, 3000)} (81% match) - Resolved as fraud",
        ],
        "confidence": round(random.uniform(0.85, 0.97), 2),
        "generated_at": datetime.now().isoformat() + "Z"
    }

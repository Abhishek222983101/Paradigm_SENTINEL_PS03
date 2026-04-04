import time
import sys

def print_slow(text, delay=0.03):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

print("\n" + "="*60)
print_slow("🚨 SENTINEL FRAUD DETECTION ENGINE - LIVE INFERENCE 🚨", 0.02)
print("="*60 + "\n")

print("[*] Initializing Multi-Modal AI Core...")
time.sleep(0.5)
print("[*] Loading trained weights (Fusion Attention Network)... [OK]")
time.sleep(0.5)

print("\n[>>] INTERCEPTING INCOMING TRANSACTION STREAM...\n")
time.sleep(1)

# Simulate two transactions (one legit, one highly suspicious)
transactions = [
    {"id": "TXN-8842-A", "type": "Normal Behavior", "fraud_prob": 0.02, "score": 12.4, "mfa": 0, "type_name": "None", "delay": 0.8},
    {"id": "TXN-9910-X", "type": "Suspicious (Velocity + Graph Anomaly)", "fraud_prob": 0.94, "score": 91.2, "mfa": 2, "type_name": "Account Takeover", "delay": 1.5}
]

for txn in transactions:
    print(f"Intercepted Transaction ID: {txn['id']}")
    print("Processing through neural pathways...")
    time.sleep(0.4)
    print("  ├─ [1] Tabular Encoder (Entity Profiling)....... [DONE]")
    time.sleep(0.2)
    print("  ├─ [2] Sequence Transformer (Time-series)....... [DONE]")
    time.sleep(0.3)
    print("  ├─ [3] Graph Neural Network (Ring Detection).... [DONE]")
    time.sleep(0.2)
    print("  └─ [4] Cross-Modal Attention Fusion............. [DONE]")
    
    print("\n" + "-"*40)
    print_slow(f"🧠 AI DECISION MATRIX ({txn['id']})", 0.01)
    print("-" * 40)
    
    time.sleep(txn['delay'])
    
    prob_str = f"{txn['fraud_prob']*100:.1f}%"
    print(f"► Fraud Probability : {prob_str}")
    print(f"► Dynamic Risk Score: {txn['score']}/100.0")
    
    mfa_actions = ["[APPROVE] Proceed Normally", "[STEP-UP] Request SMS OTP", "[BLOCK] Freeze Account & Alert Team"]
    print(f"► Recommended Action: {mfa_actions[txn['mfa']]}")
    
    if txn['mfa'] > 0:
         print(f"► Predicted Vector  : {txn['type_name']}")
    print("-" * 40 + "\n")
    time.sleep(2)

print("[*] Monitoring stream active... Waiting for next transaction.")

#!/usr/bin/env python3
"""
SENTINEL FRAUD DETECTION - DATA PREPARATION PIPELINE
=====================================================
Phase 1: Transform raw IEEE-CIS + PaySim CSVs into processed training tensors.

Sub-Phases:
1.1 - Data Loading & Schema Mapping
1.2 - Missing Value Imputation & Feature Engineering
1.3 - Vectorized Batch Feature Extraction
1.4 - Transaction Graph Construction (calls graph_builder.py)
1.5 - Sequence Window Creation
1.6 - Train/Val/Test Stratified Split
1.7 - Save Processed Data
1.8 - Validation & Testing

Usage:
    python prepare_data.py                 # Run full pipeline
    python prepare_data.py --validate      # Only run validation
    python prepare_data.py --quick         # Quick test with 10% data

Author: Sentinel Team - Phase 1
"""

import os
import sys
import json
import pickle
import argparse
import warnings
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# =============================================================================
# CONFIGURATION
# =============================================================================
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "training" / "data"
IEEE_CIS_DIR = DATA_DIR / "ieee-cis"
PAYSIM_DIR = DATA_DIR / "paysim"
PROCESSED_DIR = DATA_DIR / "processed"

# Feature configuration aligned with training_config.yaml
CATEGORICAL_FEATURES = [
    "ProductCD",  # Product code (W, C, R, H, S)
    "card4",  # Card network (visa, mastercard, etc.)
    "card6",  # Card type (debit, credit)
    "DeviceType",  # Device type
    "P_emaildomain",  # Payer email domain
]

# Columns to drop (too many missing values or not useful)
COLUMNS_TO_DROP = [
    # Columns with >90% missing that don't add value
]

# High-risk merchant category codes
HIGH_RISK_MCC = {
    "6051": "cryptocurrency",
    "5944": "jewelry",
    "5094": "precious_stones",
    "5816": "digital_goods",
    "5817": "software",
    "5818": "gaming",
    "4829": "money_transfer",
}


# =============================================================================
# SUB-PHASE 1.1: DATA LOADING & SCHEMA MAPPING
# =============================================================================
def load_ieee_cis_data(quick_mode: bool = False) -> pd.DataFrame:
    """
    Load and merge IEEE-CIS transaction and identity data.

    IEEE-CIS Data Quirks:
    - TransactionDT: seconds from an unknown reference point
    - card1-card6: anonymized card identifiers
    - V1-V339: aggregate features (sparse)
    - C1-C14: count features
    - D1-D15: time-delta features (days since event)
    - M1-M9: match features (True/False/NaN)
    - isFraud: target label (~3.5% positive)
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.1: LOADING IEEE-CIS DATA")
    print("=" * 70)

    txn_path = IEEE_CIS_DIR / "train_transaction.csv"
    id_path = IEEE_CIS_DIR / "train_identity.csv"

    # Determine sample size
    nrows = None
    if quick_mode:
        # Quick mode: load 10% (~59K rows)
        nrows = 59000
        print(f"[QUICK MODE] Loading first {nrows:,} rows")

    # Load transaction data
    print(f"\nLoading transactions from: {txn_path}")
    txn_dtypes = {
        "TransactionID": "int32",
        "isFraud": "int8",
        "TransactionDT": "int32",
        "TransactionAmt": "float32",
        "ProductCD": "category",
        "card1": "float32",
        "card2": "float32",
        "card3": "float32",
        "card4": "category",
        "card5": "float32",
        "card6": "category",
        "addr1": "float32",
        "addr2": "float32",
        "dist1": "float32",
        "dist2": "float32",
        "P_emaildomain": "object",
        "R_emaildomain": "object",
    }

    # Load with chunking for memory efficiency
    df_txn = pd.read_csv(
        txn_path,
        nrows=nrows,
        dtype={
            k: v
            for k, v in txn_dtypes.items()
            if k
            in [
                "TransactionID",
                "isFraud",
                "TransactionDT",
                "TransactionAmt",
                "ProductCD",
            ]
        },
        low_memory=False,
    )

    print(f"  Transactions loaded: {len(df_txn):,} rows, {len(df_txn.columns)} columns")
    print(f"  Fraud rate: {df_txn['isFraud'].mean() * 100:.2f}%")
    print(f"  Memory usage: {df_txn.memory_usage(deep=True).sum() / 1024**2:.1f} MB")

    # Load identity data
    print(f"\nLoading identity from: {id_path}")
    df_id = pd.read_csv(id_path, nrows=nrows, low_memory=False)
    print(f"  Identity loaded: {len(df_id):,} rows, {len(df_id.columns)} columns")

    # Merge on TransactionID (left join - not all txns have identity)
    print("\nMerging transaction + identity data...")
    df = df_txn.merge(df_id, on="TransactionID", how="left")
    print(f"  Merged dataset: {len(df):,} rows, {len(df.columns)} columns")
    print(f"  Identity coverage: {(~df['DeviceType'].isna()).mean() * 100:.1f}%")

    # Basic stats
    print("\n[DATA STATS]")
    print(f"  Total transactions: {len(df):,}")
    print(f"  Fraud cases: {df['isFraud'].sum():,}")
    print(f"  Fraud rate: {df['isFraud'].mean() * 100:.3f}%")
    print(
        f"  Time range: {df['TransactionDT'].min()} - {df['TransactionDT'].max()} seconds"
    )
    print(
        f"  Amount range: ${df['TransactionAmt'].min():.2f} - ${df['TransactionAmt'].max():,.2f}"
    )

    return df


def load_paysim_data(quick_mode: bool = False) -> pd.DataFrame:
    """
    Load PaySim synthetic financial data.

    PaySim columns:
    - step: time step (1 step = 1 hour)
    - type: CASH_IN, CASH_OUT, DEBIT, PAYMENT, TRANSFER
    - amount: transaction amount
    - nameOrig: customer who started transaction
    - oldbalanceOrg: balance before transaction
    - newbalanceOrig: balance after transaction
    - nameDest: recipient
    - oldbalanceDest: recipient balance before
    - newbalanceDest: recipient balance after
    - isFraud: fraud label
    - isFlaggedFraud: system flagged as fraud
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.1: LOADING PAYSIM DATA")
    print("=" * 70)

    paysim_path = PAYSIM_DIR / "PS_20174392719_1491204439457_log.csv"

    nrows = None
    if quick_mode:
        nrows = 100000
        print(f"[QUICK MODE] Loading first {nrows:,} rows")

    print(f"\nLoading PaySim from: {paysim_path}")
    df = pd.read_csv(
        paysim_path,
        nrows=nrows,
        dtype={
            "step": "int32",
            "type": "category",
            "amount": "float64",
            "nameOrig": "object",
            "nameDest": "object",
            "isFraud": "int8",
            "isFlaggedFraud": "int8",
        },
    )

    print(f"  PaySim loaded: {len(df):,} rows, {len(df.columns)} columns")
    print(f"  Fraud rate: {df['isFraud'].mean() * 100:.4f}%")
    print(f"  Transaction types: {df['type'].value_counts().to_dict()}")

    return df


# =============================================================================
# SUB-PHASE 1.2: MISSING VALUE IMPUTATION & FEATURE ENGINEERING
# =============================================================================
def analyze_missing_values(df: pd.DataFrame) -> Dict[str, float]:
    """Analyze missing values in the dataset."""
    missing_pct = (df.isna().sum() / len(df) * 100).sort_values(ascending=False)
    return missing_pct.to_dict()


def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing values systematically.

    Strategy:
    - Categorical: Fill with "Unknown" sentinel
    - Numerical: Fill with median
    - Create is_missing flags for informative missingness
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.2: MISSING VALUE IMPUTATION")
    print("=" * 70)

    df = df.copy()

    # Analyze missing values
    missing = analyze_missing_values(df)
    high_missing = {k: v for k, v in missing.items() if v > 50}
    print(f"\nColumns with >50% missing: {len(high_missing)}")

    # Drop columns with >90% missing (mostly V-columns)
    cols_to_drop = [k for k, v in missing.items() if v > 90]
    if cols_to_drop:
        print(f"Dropping {len(cols_to_drop)} columns with >90% missing")
        df = df.drop(columns=cols_to_drop, errors="ignore")

    # Identify column types
    categorical_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    numerical_cols = df.select_dtypes(include=[np.number]).columns.tolist()

    # Remove target and ID columns from processing
    protected_cols = ["TransactionID", "isFraud"]
    numerical_cols = [c for c in numerical_cols if c not in protected_cols]

    # Track imputation stats
    imputation_stats = {}

    # Impute categorical columns
    print(f"\nImputing {len(categorical_cols)} categorical columns with 'Unknown'...")
    for col in categorical_cols:
        if df[col].isna().any():
            na_count = df[col].isna().sum()
            df[col] = df[col].fillna("Unknown")
            imputation_stats[col] = {"type": "categorical", "na_filled": na_count}

    # Impute numerical columns with median
    print(f"Imputing {len(numerical_cols)} numerical columns with median...")
    for col in tqdm(numerical_cols, desc="Numerical imputation"):
        if df[col].isna().any():
            na_count = df[col].isna().sum()
            median_val = df[col].median()

            # Create missingness indicator for columns with >10% missing
            missing_pct = na_count / len(df) * 100
            if missing_pct > 10:
                df[f"{col}_is_missing"] = df[col].isna().astype("int8")

            df[col] = df[col].fillna(median_val)
            imputation_stats[col] = {
                "type": "numerical",
                "na_filled": na_count,
                "fill_value": float(median_val),
            }

    print(f"\n[IMPUTATION COMPLETE]")
    print(f"  Columns processed: {len(imputation_stats)}")
    print(
        f"  Total NaN filled: {sum(s.get('na_filled', 0) for s in imputation_stats.values()):,}"
    )
    print(f"  Remaining NaN: {df.isna().sum().sum()}")

    return df


def create_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create derived features from raw IEEE-CIS columns.

    This includes:
    - Time-based features (cyclical encoding)
    - Amount-based features (log, z-score)
    - Aggregations per user (card1)
    - Risk indicators
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.2: DERIVED FEATURE ENGINEERING")
    print("=" * 70)

    df = df.copy()
    n_original = len(df.columns)

    # =========================================================================
    # TIME FEATURES
    # =========================================================================
    print("\n[1/6] Creating time features...")

    # Convert TransactionDT (seconds from reference) to relative hours
    df["transaction_hour"] = (df["TransactionDT"] / 3600) % 24
    df["transaction_day"] = (df["TransactionDT"] / 86400).astype("int32")

    # Cyclical encoding for hour (captures continuity: 23:00 is close to 00:00)
    df["hour_sin"] = np.sin(2 * np.pi * df["transaction_hour"] / 24)
    df["hour_cos"] = np.cos(2 * np.pi * df["transaction_hour"] / 24)

    # Day of week (synthetic since we don't have real dates)
    df["day_of_week"] = df["transaction_day"] % 7
    df["day_sin"] = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["day_cos"] = np.cos(2 * np.pi * df["day_of_week"] / 7)

    # Binary time indicators
    df["is_weekend"] = (df["day_of_week"] >= 5).astype("int8")
    df["is_night"] = (
        (df["transaction_hour"] < 6) | (df["transaction_hour"] >= 22)
    ).astype("int8")

    # =========================================================================
    # AMOUNT FEATURES
    # =========================================================================
    print("[2/6] Creating amount features...")

    # Log transform (handles scale variance)
    df["amount_log"] = np.log1p(df["TransactionAmt"])

    # Round amount detection (suspicious patterns)
    df["is_round_100"] = (
        (df["TransactionAmt"] % 100 == 0) & (df["TransactionAmt"] >= 100)
    ).astype("int8")
    df["is_round_1000"] = (
        (df["TransactionAmt"] % 1000 == 0) & (df["TransactionAmt"] >= 1000)
    ).astype("int8")

    # Threshold evasion detection (just below common limits)
    thresholds = [5000, 10000, 50000, 100000]
    df["is_threshold_evasion"] = 0
    for t in thresholds:
        mask = (df["TransactionAmt"] >= t * 0.95) & (df["TransactionAmt"] < t)
        df.loc[mask, "is_threshold_evasion"] = 1
    df["is_threshold_evasion"] = df["is_threshold_evasion"].astype("int8")

    # Amount percentiles
    df["amount_percentile"] = df["TransactionAmt"].rank(pct=True)

    # =========================================================================
    # USER (card1) AGGREGATION FEATURES
    # =========================================================================
    print("[3/6] Creating user aggregation features...")

    # card1 represents user identity in IEEE-CIS
    # Fill NaN card1 with -999 to handle missing
    df["card1"] = df["card1"].fillna(-999)

    # User transaction statistics
    user_stats = df.groupby("card1").agg(
        {
            "TransactionAmt": ["mean", "std", "count", "max"],
            "TransactionDT": ["min", "max"],
        }
    )
    user_stats.columns = [
        "user_avg_amt",
        "user_std_amt",
        "user_txn_count",
        "user_max_amt",
        "user_first_txn",
        "user_last_txn",
    ]
    user_stats = user_stats.reset_index()

    # Merge user stats
    df = df.merge(user_stats, on="card1", how="left")

    # Amount z-score per user
    df["amount_zscore"] = (df["TransactionAmt"] - df["user_avg_amt"]) / (
        df["user_std_amt"] + 1e-6
    )
    df["amount_zscore"] = df["amount_zscore"].clip(-10, 10)  # Clip outliers

    # Amount normalized by user average
    df["amount_normalized"] = df["TransactionAmt"] / (df["user_avg_amt"] + 1e-6)
    df["amount_normalized"] = df["amount_normalized"].clip(0, 100)

    # Transaction frequency
    df["user_txn_frequency"] = df["user_txn_count"] / (
        (df["user_last_txn"] - df["user_first_txn"]) / 86400 + 1
    )

    # =========================================================================
    # DEVICE & NETWORK FEATURES
    # =========================================================================
    print("[4/6] Creating device & network features...")

    # Device type encoding
    df["DeviceType"] = df["DeviceType"].fillna("Unknown")
    df["is_mobile"] = (df["DeviceType"].str.lower() == "mobile").astype("int8")

    # Email domain features
    df["P_emaildomain"] = df["P_emaildomain"].fillna("Unknown")
    df["R_emaildomain"] = df["R_emaildomain"].fillna("Unknown")

    # Common email providers
    common_domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com"]
    df["is_common_email"] = df["P_emaildomain"].isin(common_domains).astype("int8")

    # Email match (payer and recipient same domain)
    df["email_domain_match"] = (df["P_emaildomain"] == df["R_emaildomain"]).astype(
        "int8"
    )

    # =========================================================================
    # CARD FEATURES
    # =========================================================================
    print("[5/6] Creating card features...")

    # Card type (credit vs debit)
    df["card6"] = df["card6"].fillna("Unknown")
    df["is_credit"] = (df["card6"].str.lower() == "credit").astype("int8")
    df["is_debit"] = (df["card6"].str.lower() == "debit").astype("int8")

    # Card network
    df["card4"] = df["card4"].fillna("Unknown")
    df["is_visa"] = (df["card4"].str.lower() == "visa").astype("int8")
    df["is_mastercard"] = (df["card4"].str.lower() == "mastercard").astype("int8")

    # =========================================================================
    # PRODUCT CODE FEATURES
    # =========================================================================
    print("[6/6] Creating product features...")

    # Product code one-hot
    df["ProductCD"] = df["ProductCD"].fillna("Unknown")
    product_dummies = pd.get_dummies(df["ProductCD"], prefix="product")
    df = pd.concat([df, product_dummies], axis=1)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    n_new = len(df.columns) - n_original
    print(f"\n[FEATURE ENGINEERING COMPLETE]")
    print(f"  Original columns: {n_original}")
    print(f"  New columns: {n_new}")
    print(f"  Total columns: {len(df.columns)}")

    return df


# =============================================================================
# SUB-PHASE 1.3: VECTORIZED BATCH FEATURE EXTRACTION
# =============================================================================
def extract_numerical_features(df: pd.DataFrame) -> Tuple[np.ndarray, List[str]]:
    """
    Extract numerical features into a single array.
    Aligned with feature_extractor.py feature names.
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.3: NUMERICAL FEATURE EXTRACTION")
    print("=" * 70)

    # Define numerical feature columns to extract
    # These align with FeatureExtractor.numerical_feature_names
    numerical_features = [
        # Behavioral (from aggregations)
        "user_txn_count",
        "amount_zscore",
        "amount_normalized",
        "user_txn_frequency",
        # Time features
        "hour_sin",
        "hour_cos",
        "day_sin",
        "day_cos",
        "is_weekend",
        "is_night",
        # Amount features
        "amount_log",
        "amount_percentile",
        "is_round_100",
        "is_round_1000",
        "is_threshold_evasion",
        # Device features
        "is_mobile",
        # Email features
        "is_common_email",
        "email_domain_match",
        # Card features
        "is_credit",
        "is_debit",
        "is_visa",
        "is_mastercard",
        # Transaction amount
        "TransactionAmt",
    ]

    # Add C-columns (count features) if they exist
    c_cols = [c for c in df.columns if c.startswith("C") and c[1:].isdigit()]
    numerical_features.extend(c_cols[:14])  # C1-C14

    # Add D-columns (time delta features) if they exist
    d_cols = [c for c in df.columns if c.startswith("D") and c[1:].isdigit()]
    numerical_features.extend(d_cols[:15])  # D1-D15

    # Add select V-columns (top by variance)
    v_cols = [c for c in df.columns if c.startswith("V") and c[1:].isdigit()]
    if v_cols:
        # Select top 20 V-columns by variance
        v_variances = df[v_cols].var().sort_values(ascending=False)
        top_v_cols = v_variances.head(20).index.tolist()
        numerical_features.extend(top_v_cols)

    # Add product dummies
    product_cols = [c for c in df.columns if c.startswith("product_")]
    numerical_features.extend(product_cols)

    # Add missingness indicators
    missing_cols = [c for c in df.columns if c.endswith("_is_missing")]
    numerical_features.extend(missing_cols)

    # Filter to columns that exist
    available_features = [f for f in numerical_features if f in df.columns]

    print(f"Extracting {len(available_features)} numerical features")

    # Extract and convert to float32
    X = df[available_features].values.astype(np.float32)

    # Handle any remaining NaN or inf
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)

    print(f"  Shape: {X.shape}")
    print(f"  Memory: {X.nbytes / 1024**2:.1f} MB")
    print(f"  NaN count: {np.isnan(X).sum()}")

    return X, available_features


def extract_categorical_features(
    df: pd.DataFrame,
) -> Tuple[Dict[str, np.ndarray], Dict[str, LabelEncoder]]:
    """
    Encode categorical features as integers for embedding layers.
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.3: CATEGORICAL FEATURE EXTRACTION")
    print("=" * 70)

    categorical_cols = ["ProductCD", "card4", "card6", "DeviceType", "P_emaildomain"]

    # Filter to available columns
    available_cats = [c for c in categorical_cols if c in df.columns]

    print(f"Encoding {len(available_cats)} categorical features")

    encoders = {}
    encoded_features = {}

    for col in available_cats:
        # Fill NaN with 'Unknown'
        values = df[col].fillna("Unknown").astype(str)

        # Label encode
        le = LabelEncoder()
        encoded = le.fit_transform(values)

        encoders[col] = le
        encoded_features[col] = encoded.astype(np.int32)

        n_unique = len(le.classes_)
        print(f"  {col}: {n_unique} unique values")

    return encoded_features, encoders


# =============================================================================
# SUB-PHASE 1.5: SEQUENCE WINDOW CREATION
# =============================================================================
def create_sequence_windows(
    df: pd.DataFrame,
    numerical_features: np.ndarray,
    feature_names: List[str],
    window_size: int = 20,
    min_transactions: int = 2,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create sliding windows of transactions per user for sequential modeling.

    Returns:
        sequences: (N_sequences, window_size, feature_dim)
        labels: (N_sequences,)
        user_ids: (N_sequences,) - card1 values
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.5: SEQUENCE WINDOW CREATION")
    print("=" * 70)

    # Sort by user and time
    df = df.copy()
    df["_numerical_idx"] = np.arange(len(df))
    df = df.sort_values(["card1", "TransactionDT"])

    # Select features for sequences (subset for efficiency)
    # Use first 32 features as per training_config.yaml (feature_dim: 32)
    seq_feature_indices = list(range(min(32, len(feature_names))))

    print(f"Window size: {window_size}")
    print(f"Features per step: {len(seq_feature_indices)}")
    print(f"Min transactions per user: {min_transactions}")

    sequences = []
    labels = []
    user_ids = []

    # Group by user (card1)
    user_groups = df.groupby("card1")
    n_users = len(user_groups)

    print(f"\nProcessing {n_users:,} users...")

    for card1, group in tqdm(user_groups, desc="Creating sequences", total=n_users):
        if len(group) < min_transactions:
            continue

        indices = group["_numerical_idx"].values
        group_labels = group["isFraud"].values

        # Create sliding windows
        for i in range(len(group)):
            # Get window of previous transactions (including current)
            start_idx = max(0, i - window_size + 1)
            window_indices = indices[start_idx : i + 1]

            # Pad if necessary
            if len(window_indices) < window_size:
                pad_size = window_size - len(window_indices)
                # Pad with first transaction (or zeros)
                window_indices = np.concatenate(
                    [np.full(pad_size, window_indices[0]), window_indices]
                )

            # Extract features for this window
            window_features = numerical_features[window_indices][:, seq_feature_indices]

            sequences.append(window_features)
            labels.append(group_labels[i])
            user_ids.append(card1)

    sequences = np.array(sequences, dtype=np.float32)
    labels = np.array(labels, dtype=np.int8)
    user_ids = np.array(user_ids, dtype=np.float32)

    print(f"\n[SEQUENCE CREATION COMPLETE]")
    print(f"  Total sequences: {len(sequences):,}")
    print(f"  Shape: {sequences.shape}")
    print(f"  Fraud sequences: {labels.sum():,} ({labels.mean() * 100:.2f}%)")
    print(f"  Memory: {sequences.nbytes / 1024**2:.1f} MB")

    return sequences, labels, user_ids


# =============================================================================
# SUB-PHASE 1.6: TRAIN/VAL/TEST SPLIT
# =============================================================================
def create_stratified_splits(
    df: pd.DataFrame,
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
    test_ratio: float = 0.1,
    random_state: int = 42,
) -> Dict[str, np.ndarray]:
    """
    Create stratified train/val/test splits preserving fraud rate.
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.6: STRATIFIED SPLIT")
    print("=" * 70)

    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-6, (
        "Ratios must sum to 1"
    )

    n = len(df)
    indices = np.arange(n)
    labels = df["isFraud"].values

    # First split: train vs (val + test)
    train_idx, temp_idx, train_y, temp_y = train_test_split(
        indices,
        labels,
        test_size=(val_ratio + test_ratio),
        stratify=labels,
        random_state=random_state,
    )

    # Second split: val vs test
    val_size_adjusted = val_ratio / (val_ratio + test_ratio)
    val_idx, test_idx = train_test_split(
        temp_idx,
        test_size=(1 - val_size_adjusted),
        stratify=temp_y,
        random_state=random_state,
    )

    splits = {"train_idx": train_idx, "val_idx": val_idx, "test_idx": test_idx}

    print(f"\n[SPLIT STATISTICS]")
    for name, idx in splits.items():
        fraud_rate = df.iloc[idx]["isFraud"].mean() * 100
        print(
            f"  {name}: {len(idx):,} samples ({len(idx) / n * 100:.1f}%), fraud rate: {fraud_rate:.2f}%"
        )

    return splits


# =============================================================================
# SUB-PHASE 1.7: SAVE PROCESSED DATA
# =============================================================================
def save_processed_data(
    df: pd.DataFrame,
    numerical_features: np.ndarray,
    numerical_feature_names: List[str],
    categorical_features: Dict[str, np.ndarray],
    categorical_encoders: Dict[str, LabelEncoder],
    sequences: np.ndarray,
    sequence_labels: np.ndarray,
    sequence_user_ids: np.ndarray,
    splits: Dict[str, np.ndarray],
    output_dir: Path,
) -> Dict[str, Path]:
    """
    Save all processed data to disk.
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.7: SAVING PROCESSED DATA")
    print("=" * 70)

    output_dir.mkdir(parents=True, exist_ok=True)
    saved_files = {}

    # 1. Save main features DataFrame as parquet
    print("\n[1/6] Saving features.parquet...")
    features_path = output_dir / "features.parquet"

    # Create features DataFrame with numerical and labels
    features_df = pd.DataFrame(numerical_features, columns=numerical_feature_names)
    features_df["isFraud"] = df["isFraud"].values
    features_df["TransactionID"] = df["TransactionID"].values
    features_df["card1"] = df["card1"].values
    features_df["TransactionAmt"] = df["TransactionAmt"].values

    # Add raw columns needed for graph building
    if "DeviceInfo" in df.columns:
        features_df["DeviceInfo"] = df["DeviceInfo"].values
    if "addr1" in df.columns:
        features_df["addr1"] = df["addr1"].values
    if "P_emaildomain" in df.columns:
        features_df["P_emaildomain"] = df["P_emaildomain"].values

    # Add categorical features
    for name, values in categorical_features.items():
        features_df[f"cat_{name}"] = values

    features_df.to_parquet(features_path, index=False, compression="snappy")
    saved_files["features"] = features_path
    print(f"  Saved: {features_path} ({features_path.stat().st_size / 1024**2:.1f} MB)")

    # 2. Save sequences as numpy
    print("\n[2/6] Saving sequences.npz...")
    sequences_path = output_dir / "sequences.npz"
    np.savez_compressed(
        sequences_path,
        sequences=sequences,
        labels=sequence_labels,
        user_ids=sequence_user_ids,
    )
    saved_files["sequences"] = sequences_path
    print(
        f"  Saved: {sequences_path} ({sequences_path.stat().st_size / 1024**2:.1f} MB)"
    )

    # 3. Save splits
    print("\n[3/6] Saving splits.pkl...")
    splits_path = output_dir / "splits.pkl"
    with open(splits_path, "wb") as f:
        pickle.dump(splits, f)
    saved_files["splits"] = splits_path
    print(f"  Saved: {splits_path}")

    # 4. Save encoders
    print("\n[4/6] Saving encoders.pkl...")
    encoders_path = output_dir / "encoders.pkl"
    with open(encoders_path, "wb") as f:
        pickle.dump(categorical_encoders, f)
    saved_files["encoders"] = encoders_path
    print(f"  Saved: {encoders_path}")

    # 5. Save metadata
    print("\n[5/6] Saving metadata.json...")
    metadata = {
        "created_at": datetime.now().isoformat(),
        "n_samples": len(df),
        "n_fraud": int(df["isFraud"].sum()),
        "fraud_rate": float(df["isFraud"].mean()),
        "n_numerical_features": len(numerical_feature_names),
        "n_categorical_features": len(categorical_features),
        "numerical_feature_names": numerical_feature_names,
        "categorical_feature_names": list(categorical_features.keys()),
        "categorical_cardinalities": {
            k: len(v.classes_) for k, v in categorical_encoders.items()
        },
        "sequence_shape": list(sequences.shape),
        "splits": {k: len(v) for k, v in splits.items()},
        "files": {k: str(v) for k, v in saved_files.items()},
    }

    metadata_path = output_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)
    saved_files["metadata"] = metadata_path
    print(f"  Saved: {metadata_path}")

    # 6. Save scaler for numerical features
    print("\n[6/6] Saving scaler...")
    scaler = StandardScaler()
    scaler.fit(numerical_features)
    scaler_path = output_dir / "scaler.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)
    saved_files["scaler"] = scaler_path
    print(f"  Saved: {scaler_path}")

    print("\n[SAVE COMPLETE]")
    print(f"  Total files: {len(saved_files)}")
    print(f"  Output directory: {output_dir}")

    return saved_files


# =============================================================================
# SUB-PHASE 1.8: VALIDATION
# =============================================================================
def validate_processed_data(output_dir: Path) -> bool:
    """
    Validate all processed data files.
    """
    print("\n" + "=" * 70)
    print("SUB-PHASE 1.8: VALIDATION")
    print("=" * 70)

    all_valid = True

    # 1. Check metadata
    print("\n[1/5] Validating metadata.json...")
    metadata_path = output_dir / "metadata.json"
    if not metadata_path.exists():
        print("  ERROR: metadata.json not found!")
        return False

    with open(metadata_path) as f:
        metadata = json.load(f)

    print(f"  Samples: {metadata['n_samples']:,}")
    print(f"  Fraud rate: {metadata['fraud_rate'] * 100:.2f}%")
    print(f"  Numerical features: {metadata['n_numerical_features']}")
    print(f"  Categorical features: {metadata['n_categorical_features']}")

    # 2. Check features.parquet
    print("\n[2/5] Validating features.parquet...")
    features_path = output_dir / "features.parquet"
    if not features_path.exists():
        print("  ERROR: features.parquet not found!")
        return False

    features_df = pd.read_parquet(features_path)
    print(f"  Shape: {features_df.shape}")

    nan_count = features_df.isna().sum().sum()
    print(f"  NaN count: {nan_count}")
    if nan_count > 0:
        print("  WARNING: NaN values found in features!")
        all_valid = False

    # Check fraud rate preserved
    actual_fraud_rate = features_df["isFraud"].mean()
    expected_fraud_rate = metadata["fraud_rate"]
    if abs(actual_fraud_rate - expected_fraud_rate) > 0.001:
        print(
            f"  WARNING: Fraud rate mismatch! Expected {expected_fraud_rate:.4f}, got {actual_fraud_rate:.4f}"
        )
        all_valid = False
    else:
        print(f"  Fraud rate preserved: {actual_fraud_rate * 100:.2f}%")

    # 3. Check sequences
    print("\n[3/5] Validating sequences.npz...")
    sequences_path = output_dir / "sequences.npz"
    if not sequences_path.exists():
        print("  ERROR: sequences.npz not found!")
        return False

    seq_data = np.load(sequences_path)
    sequences = seq_data["sequences"]
    seq_labels = seq_data["labels"]

    print(f"  Shape: {sequences.shape}")
    print(f"  Labels shape: {seq_labels.shape}")
    print(f"  Fraud sequences: {seq_labels.sum():,} ({seq_labels.mean() * 100:.2f}%)")

    nan_count = np.isnan(sequences).sum()
    if nan_count > 0:
        print(f"  WARNING: {nan_count} NaN values in sequences!")
        all_valid = False
    else:
        print(f"  No NaN values in sequences")

    # 4. Check splits
    print("\n[4/5] Validating splits.pkl...")
    splits_path = output_dir / "splits.pkl"
    if not splits_path.exists():
        print("  ERROR: splits.pkl not found!")
        return False

    with open(splits_path, "rb") as f:
        splits = pickle.load(f)

    total_split = sum(len(v) for v in splits.values())
    print(
        f"  Train: {len(splits['train_idx']):,} ({len(splits['train_idx']) / total_split * 100:.1f}%)"
    )
    print(
        f"  Val: {len(splits['val_idx']):,} ({len(splits['val_idx']) / total_split * 100:.1f}%)"
    )
    print(
        f"  Test: {len(splits['test_idx']):,} ({len(splits['test_idx']) / total_split * 100:.1f}%)"
    )

    # Check splits don't overlap
    train_set = set(splits["train_idx"])
    val_set = set(splits["val_idx"])
    test_set = set(splits["test_idx"])

    if train_set & val_set:
        print("  ERROR: Train and val overlap!")
        all_valid = False
    if train_set & test_set:
        print("  ERROR: Train and test overlap!")
        all_valid = False
    if val_set & test_set:
        print("  ERROR: Val and test overlap!")
        all_valid = False

    # Check fraud rates preserved across splits
    for name, idx in splits.items():
        split_fraud_rate = features_df.iloc[idx]["isFraud"].mean()
        if abs(split_fraud_rate - metadata["fraud_rate"]) > 0.01:
            print(
                f"  WARNING: {name} fraud rate differs: {split_fraud_rate * 100:.2f}% vs expected {metadata['fraud_rate'] * 100:.2f}%"
            )
        else:
            print(f"  {name} fraud rate preserved: {split_fraud_rate * 100:.2f}%")

    # 5. Final summary
    print("\n[5/5] Final validation...")

    if all_valid:
        print("\n" + "=" * 70)
        print("VALIDATION PASSED")
        print("=" * 70)
        print("All checks passed. Data is ready for Phase 2 training.")
    else:
        print("\n" + "=" * 70)
        print("VALIDATION FAILED")
        print("=" * 70)
        print("Some checks failed. Please review warnings above.")

    return all_valid


# =============================================================================
# MAIN PIPELINE
# =============================================================================
def run_pipeline(args):
    """Run the complete data preparation pipeline."""

    print("\n" + "=" * 70)
    print("SENTINEL FRAUD DETECTION - DATA PREPARATION PIPELINE")
    print("=" * 70)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Quick mode: {args.quick}")
    print(f"Output directory: {PROCESSED_DIR}")

    # Create output directory
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # =========================================================================
    # SUB-PHASE 1.1: DATA LOADING
    # =========================================================================
    df = load_ieee_cis_data(quick_mode=args.quick)

    # Also load PaySim for reference (we'll use it in Phase 2 for augmentation)
    # df_paysim = load_paysim_data(quick_mode=args.quick)

    # =========================================================================
    # SUB-PHASE 1.2: MISSING VALUES & FEATURE ENGINEERING
    # =========================================================================
    df = impute_missing_values(df)
    df = create_derived_features(df)

    # =========================================================================
    # SUB-PHASE 1.3: FEATURE EXTRACTION
    # =========================================================================
    numerical_features, numerical_feature_names = extract_numerical_features(df)
    categorical_features, categorical_encoders = extract_categorical_features(df)

    # =========================================================================
    # SUB-PHASE 1.5: SEQUENCE CREATION
    # =========================================================================
    sequences, sequence_labels, sequence_user_ids = create_sequence_windows(
        df,
        numerical_features,
        numerical_feature_names,
        window_size=20,
        min_transactions=2,
    )

    # =========================================================================
    # SUB-PHASE 1.6: STRATIFIED SPLITS
    # =========================================================================
    splits = create_stratified_splits(df)

    # =========================================================================
    # SUB-PHASE 1.7: SAVE DATA
    # =========================================================================
    saved_files = save_processed_data(
        df=df,
        numerical_features=numerical_features,
        numerical_feature_names=numerical_feature_names,
        categorical_features=categorical_features,
        categorical_encoders=categorical_encoders,
        sequences=sequences,
        sequence_labels=sequence_labels,
        sequence_user_ids=sequence_user_ids,
        splits=splits,
        output_dir=PROCESSED_DIR,
    )

    # =========================================================================
    # SUB-PHASE 1.8: VALIDATION
    # =========================================================================
    validation_passed = validate_processed_data(PROCESSED_DIR)

    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("\n" + "=" * 70)
    print("PIPELINE COMPLETE")
    print("=" * 70)
    print(f"End time: {datetime.now().isoformat()}")
    print(f"\nOutput files:")
    for name, path in saved_files.items():
        size = path.stat().st_size / 1024**2
        print(f"  {name}: {path.name} ({size:.1f} MB)")

    if validation_passed:
        print("\nStatus: SUCCESS - Ready for Phase 2 (Model Training)")
    else:
        print("\nStatus: PARTIAL SUCCESS - Review validation warnings")

    return validation_passed


def main():
    parser = argparse.ArgumentParser(description="SENTINEL Data Preparation Pipeline")
    parser.add_argument(
        "--quick", action="store_true", help="Quick mode with 10 percent data"
    )
    parser.add_argument(
        "--validate", action="store_true", help="Only run validation on existing data"
    )
    args = parser.parse_args()

    if args.validate:
        validate_processed_data(PROCESSED_DIR)
    else:
        run_pipeline(args)


if __name__ == "__main__":
    main()

"""
SENTINEL FRAUD DETECTION - XGBOOST BASELINE TRAINING
======================================================
Model: XGBoost Gradient Boosting
Type: TRAIN FROM SCRATCH
Input: features.parquet (360 numerical features)
Target: isFraud (binary, ~3.5% fraud rate)
Expected Time: 5-10 minutes on CPU

This serves as our baseline. If the deep learning models
don't beat this, something is wrong.

WandB Run: sentinel-fraud/xgboost-baseline
"""

import os
import sys
import gc
import json
import pickle
import time
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import xgboost as xgb
from sklearn.metrics import (
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    precision_recall_curve,
    average_precision_score,
    classification_report,
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

# XGBoost Hyperparameters (tuned for fraud detection - memory optimized)
XGBOOST_PARAMS = {
    "objective": "binary:logistic",
    "eval_metric": ["auc", "aucpr"],
    "tree_method": "hist",  # Fast histogram-based training
    "max_depth": 6,  # Reduced for memory
    "learning_rate": 0.1,  # Increased to converge faster
    "n_estimators": 500,  # Reduced
    "subsample": 0.7,
    "colsample_bytree": 0.7,
    "min_child_weight": 10,
    "gamma": 0.2,
    "reg_alpha": 0.1,
    "reg_lambda": 1.0,
    "random_state": 42,
    "n_jobs": 4,  # Limit parallel jobs
    "verbosity": 1,
    "max_bin": 128,  # Reduce memory usage
}

EARLY_STOPPING_ROUNDS = 50


def load_data():
    """Load processed features and splits."""
    print("=" * 60)
    print("LOADING DATA")
    print("=" * 60)

    # Load features
    features_path = DATA_DIR / "features.parquet"
    print(f"Loading features from: {features_path}")
    df = pd.read_parquet(features_path)
    print(f"  Shape: {df.shape}")

    # Force garbage collection
    gc.collect()

    # Load splits
    splits_path = DATA_DIR / "splits.pkl"
    print(f"Loading splits from: {splits_path}")
    with open(splits_path, "rb") as f:
        splits = pickle.load(f)

    # Load metadata
    metadata_path = DATA_DIR / "metadata.json"
    with open(metadata_path, "r") as f:
        metadata = json.load(f)

    return df, splits, metadata


def prepare_datasets(df, splits, metadata):
    """Prepare train, validation, test sets."""
    print("\n" + "=" * 60)
    print("PREPARING DATASETS")
    print("=" * 60)

    # Get feature columns (exclude target and categorical)
    categorical_cols = metadata["categorical_feature_names"]
    target_col = "isFraud"

    # Use only numerical features for XGBoost (exclude strings/objects)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    feature_cols = [col for col in numeric_cols if col not in [target_col]]

    print(f"Number of numerical features: {len(feature_cols)}")

    # Extract features and target
    X = df[feature_cols].values.astype(np.float32)  # Use float32 to save memory
    y = df[target_col].values.astype(np.float32)

    # Split data
    train_idx = splits["train_idx"]
    val_idx = splits["val_idx"]
    test_idx = splits["test_idx"]

    X_train, y_train = X[train_idx], y[train_idx]
    X_val, y_val = X[val_idx], y[val_idx]
    X_test, y_test = X[test_idx], y[test_idx]

    # Calculate class imbalance
    fraud_rate = y_train.mean()
    scale_pos_weight = (1 - fraud_rate) / fraud_rate

    print(f"\nDataset sizes:")
    print(
        f"  Train: {len(X_train):,} samples ({y_train.sum():,} fraud, {fraud_rate * 100:.2f}%)"
    )
    print(f"  Val:   {len(X_val):,} samples ({y_val.sum():,} fraud)")
    print(f"  Test:  {len(X_test):,} samples ({y_test.sum():,} fraud)")
    print(f"\nClass imbalance: scale_pos_weight = {scale_pos_weight:.2f}")

    return (
        X_train,
        y_train,
        X_val,
        y_val,
        X_test,
        y_test,
        feature_cols,
        scale_pos_weight,
    )


def train_xgboost(X_train, y_train, X_val, y_val, scale_pos_weight):
    """Train XGBoost model with early stopping."""
    print("\n" + "=" * 60)
    print("TRAINING XGBOOST")
    print("=" * 60)

    # Update params with calculated scale_pos_weight
    params = XGBOOST_PARAMS.copy()
    params["scale_pos_weight"] = scale_pos_weight

    # Log hyperparameters to WandB
    wandb.config.update(params)

    print(f"\nHyperparameters:")
    for k, v in params.items():
        print(f"  {k}: {v}")

    # Create model
    n_estimators = params.pop("n_estimators")
    model = xgb.XGBClassifier(n_estimators=n_estimators, **params)

    # Train with early stopping
    print(f"\nTraining with early stopping (patience={EARLY_STOPPING_ROUNDS})...")
    start_time = time.time()

    model.fit(
        X_train,
        y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=50,  # Print every 50 rounds
    )

    training_time = time.time() - start_time
    print(f"\nTraining completed in {training_time:.2f} seconds")

    # Get best iteration
    best_iteration = (
        model.best_iteration if hasattr(model, "best_iteration") else n_estimators
    )
    print(f"Best iteration: {best_iteration}")

    # Log training time
    wandb.log(
        {
            "training_time_seconds": training_time,
            "best_iteration": best_iteration,
            "n_estimators_used": best_iteration,
        }
    )

    return model


def evaluate_model(model, X, y, split_name, feature_cols):
    """Comprehensive model evaluation with all metrics."""
    print(f"\n{'=' * 60}")
    print(f"EVALUATING ON {split_name.upper()}")
    print("=" * 60)

    # Predictions
    y_prob = model.predict_proba(X)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    # Metrics
    auc_roc = roc_auc_score(y, y_prob)
    auc_pr = average_precision_score(y, y_prob)
    precision = precision_score(y, y_pred, zero_division=0)
    recall = recall_score(y, y_pred, zero_division=0)
    f1 = f1_score(y, y_pred, zero_division=0)

    # Confusion matrix
    tn, fp, fn, tp = confusion_matrix(y, y_pred).ravel()

    # False positive rate
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0

    # Print metrics
    print(f"\nMetrics:")
    print(f"  AUC-ROC:    {auc_roc:.4f}")
    print(f"  AUC-PR:     {auc_pr:.4f}")
    print(f"  Precision:  {precision:.4f}")
    print(f"  Recall:     {recall:.4f}")
    print(f"  F1 Score:   {f1:.4f}")
    print(f"  FPR:        {fpr:.4f}")

    print(f"\nConfusion Matrix:")
    print(f"  TN: {tn:,}  FP: {fp:,}")
    print(f"  FN: {fn:,}  TP: {tp:,}")

    # Log to WandB
    metrics = {
        f"{split_name}/auc_roc": auc_roc,
        f"{split_name}/auc_pr": auc_pr,
        f"{split_name}/precision": precision,
        f"{split_name}/recall": recall,
        f"{split_name}/f1": f1,
        f"{split_name}/fpr": fpr,
        f"{split_name}/true_negatives": tn,
        f"{split_name}/false_positives": fp,
        f"{split_name}/false_negatives": fn,
        f"{split_name}/true_positives": tp,
    }
    wandb.log(metrics)

    # Feature importance (for test set only)
    if split_name == "test":
        print("\nTop 20 Feature Importances:")
        importance = model.feature_importances_
        importance_df = (
            pd.DataFrame({"feature": feature_cols, "importance": importance})
            .sort_values("importance", ascending=False)
            .head(20)
        )

        for i, row in importance_df.iterrows():
            print(f"  {row['feature']}: {row['importance']:.4f}")

        # Log feature importance to WandB
        wandb.log({"feature_importance": wandb.Table(dataframe=importance_df.head(50))})

    # Precision-Recall curve data
    precisions, recalls, thresholds = precision_recall_curve(y, y_prob)

    return {
        "auc_roc": auc_roc,
        "auc_pr": auc_pr,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp),
        },
    }


def find_optimal_threshold(model, X_val, y_val):
    """Find optimal threshold that maximizes F1."""
    print("\n" + "=" * 60)
    print("FINDING OPTIMAL THRESHOLD")
    print("=" * 60)

    y_prob = model.predict_proba(X_val)[:, 1]

    best_f1 = 0
    best_threshold = 0.5

    for threshold in np.arange(0.1, 0.9, 0.05):
        y_pred = (y_prob >= threshold).astype(int)
        f1 = f1_score(y_val, y_pred, zero_division=0)

        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    print(f"Optimal threshold: {best_threshold:.2f}")
    print(f"F1 at optimal threshold: {best_f1:.4f}")

    # Evaluate at optimal threshold
    y_pred_optimal = (y_prob >= best_threshold).astype(int)
    precision_opt = precision_score(y_val, y_pred_optimal, zero_division=0)
    recall_opt = recall_score(y_val, y_pred_optimal, zero_division=0)

    print(f"Precision at optimal: {precision_opt:.4f}")
    print(f"Recall at optimal: {recall_opt:.4f}")

    wandb.log(
        {
            "optimal_threshold": best_threshold,
            "f1_at_optimal_threshold": best_f1,
            "precision_at_optimal": precision_opt,
            "recall_at_optimal": recall_opt,
        }
    )

    return best_threshold


def save_model(model, feature_cols, metadata, metrics, optimal_threshold):
    """Save model and metadata."""
    print("\n" + "=" * 60)
    print("SAVING MODEL")
    print("=" * 60)

    # Save XGBoost model
    model_path = CHECKPOINT_DIR / "xgboost_baseline.json"
    model.save_model(str(model_path))
    print(f"Model saved to: {model_path}")

    # Save model metadata
    model_metadata = {
        "model_type": "xgboost",
        "trained_at": datetime.now().isoformat(),
        "n_features": len(feature_cols),
        "feature_names": feature_cols,
        "optimal_threshold": optimal_threshold,
        "metrics": {"val": metrics["val"], "test": metrics["test"]},
        "hyperparameters": XGBOOST_PARAMS,
        "data_metadata": {
            "n_train": metadata["splits"]["train_idx"],
            "n_val": metadata["splits"]["val_idx"],
            "n_test": metadata["splits"]["test_idx"],
            "fraud_rate": metadata["fraud_rate"],
        },
    }

    metadata_path = CHECKPOINT_DIR / "xgboost_baseline_metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(model_metadata, f, indent=2)
    print(f"Metadata saved to: {metadata_path}")

    # Log model artifact to WandB
    artifact = wandb.Artifact(
        name="xgboost-baseline",
        type="model",
        description="XGBoost baseline model for fraud detection",
    )
    artifact.add_file(str(model_path))
    artifact.add_file(str(metadata_path))
    wandb.log_artifact(artifact)

    return model_path


def main():
    """Main training pipeline."""
    print("\n" + "=" * 60)
    print("SENTINEL FRAUD DETECTION - XGBOOST BASELINE TRAINING")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Initialize WandB
    wandb.init(
        project="sentinel-fraud",
        name=f"xgboost-baseline-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        tags=["xgboost", "baseline", "phase2"],
        config={"model_type": "xgboost", "task": "fraud_detection"},
    )

    print(f"\n{'*' * 60}")
    print(f"WANDB RUN URL: {wandb.run.get_url()}")
    print(f"^^ TRACK THIS RUN AT THE URL ABOVE ^^")
    print(f"{'*' * 60}")

    try:
        # Load data
        df, splits, metadata = load_data()

        # Prepare datasets
        (
            X_train,
            y_train,
            X_val,
            y_val,
            X_test,
            y_test,
            feature_cols,
            scale_pos_weight,
        ) = prepare_datasets(df, splits, metadata)

        # Train model
        model = train_xgboost(X_train, y_train, X_val, y_val, scale_pos_weight)

        # Evaluate on all splits
        metrics = {}
        metrics["train"] = evaluate_model(
            model, X_train, y_train, "train", feature_cols
        )
        metrics["val"] = evaluate_model(model, X_val, y_val, "val", feature_cols)
        metrics["test"] = evaluate_model(model, X_test, y_test, "test", feature_cols)

        # Find optimal threshold
        optimal_threshold = find_optimal_threshold(model, X_val, y_val)

        # Save model
        model_path = save_model(
            model, feature_cols, metadata, metrics, optimal_threshold
        )

        print("\n" + "=" * 60)
        print("TRAINING COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print(f"\nFinal Test Metrics:")
        print(f"  AUC-ROC:   {metrics['test']['auc_roc']:.4f}")
        print(f"  AUC-PR:    {metrics['test']['auc_pr']:.4f}")
        print(f"  F1 Score:  {metrics['test']['f1']:.4f}")
        print(f"\nModel saved to: {model_path}")
        print(f"WandB Run URL: {wandb.run.get_url()}")

        # Log final summary
        wandb.summary["final_test_auc_roc"] = metrics["test"]["auc_roc"]
        wandb.summary["final_test_auc_pr"] = metrics["test"]["auc_pr"]
        wandb.summary["final_test_f1"] = metrics["test"]["f1"]
        wandb.summary["optimal_threshold"] = optimal_threshold

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback

        traceback.print_exc()
        wandb.alert(title="XGBoost Training Failed", text=str(e))
        raise

    finally:
        wandb.finish()


if __name__ == "__main__":
    main()

"""
SENTINEL - DATASET DOWNLOAD SCRIPT
===================================
Downloads IEEE-CIS Fraud Detection and PaySim datasets.

Usage:
    python download_datasets.py

Requirements:
    - Kaggle account (credentials in ~/.kaggle/kaggle.json)
    - Or manual download from Kaggle website
"""

import os
import zipfile
import shutil
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "training" / "data"
IEEE_CIS_DIR = DATA_DIR / "ieee-cis"
PAYSIM_DIR = DATA_DIR / "paysim"

IEEE_CIS_DIR.mkdir(parents=True, exist_ok=True)
PAYSIM_DIR.mkdir(parents=True, exist_ok=True)


def download_ieee_cis_via_kaggle():
    """Download IEEE-CIS Fraud Detection dataset using Kaggle API."""
    try:
        import kaggle

        print("[INFO] Downloading IEEE-CIS Fraud Detection dataset via Kaggle API...")
        kaggle.api.dataset_download_files(
            "ieee-fraud-detection", path=str(IEEE_CIS_DIR), unzip=True
        )
        print("[SUCCESS] IEEE-CIS dataset downloaded and extracted.")
        return True
    except ImportError:
        print("[WARN] kaggle package not installed. Install with: pip install kaggle")
        print(
            "[INFO] Please download manually from: https://www.kaggle.com/c/ieee-fraud-detection/data"
        )
        return False
    except Exception as e:
        print(f"[ERROR] Failed to download IEEE-CIS: {e}")
        return False


def download_paysim_via_kaggle():
    """Download PaySim dataset using Kaggle API."""
    try:
        import kaggle

        print("[INFO] Downloading PaySim dataset via Kaggle API...")
        kaggle.api.dataset_download_files(
            "ealaxi/paysim1", path=str(PAYSIM_DIR), unzip=True
        )
        print("[SUCCESS] PaySim dataset downloaded and extracted.")
        return True
    except ImportError:
        print("[WARN] kaggle package not installed.")
        print(
            "[INFO] Please download manually from: https://www.kaggle.com/datasets/ealaxi/paysim1"
        )
        return False
    except Exception as e:
        print(f"[ERROR] Failed to download PaySim: {e}")
        return False


def check_existing():
    """Check if datasets already exist."""
    ieee_exists = (IEEE_CIS_DIR / "train_transaction.csv").exists()
    paysim_exists = any(PAYSIM_DIR.glob("*.csv"))

    if ieee_exists:
        print(f"[INFO] IEEE-CIS dataset already exists at {IEEE_CIS_DIR}")
    if paysim_exists:
        print(f"[INFO] PaySim dataset already exists at {PAYSIM_DIR}")

    return ieee_exists, paysim_exists


if __name__ == "__main__":
    print("=" * 60)
    print("SENTINEL - DATASET DOWNLOADER")
    print("=" * 60)

    ieee_exists, paysim_exists = check_existing()

    if not ieee_exists:
        download_ieee_cis_via_kaggle()
    else:
        print("[SKIP] IEEE-CIS already downloaded.")

    if not paysim_exists:
        download_paysim_via_kaggle()
    else:
        print("[SKIP] PaySim already downloaded.")

    # Final check
    ieee_final = (IEEE_CIS_DIR / "train_transaction.csv").exists()
    paysim_final = any(PAYSIM_DIR.glob("*.csv"))

    print("\n" + "=" * 60)
    print("DOWNLOAD SUMMARY")
    print("=" * 60)
    print(f"  IEEE-CIS: {'DOWNLOADED' if ieee_final else 'MISSING'}")
    print(f"  PaySim:   {'DOWNLOADED' if paysim_final else 'MISSING'}")

    if not ieee_final or not paysim_final:
        print("\n[WARN] Some datasets are missing. Please download manually:")
        if not ieee_final:
            print("  1. Go to https://www.kaggle.com/c/ieee-fraud-detection/data")
            print("  2. Download all CSV files")
            print(f"  3. Place them in: {IEEE_CIS_DIR}")
        if not paysim_final:
            print("  1. Go to https://www.kaggle.com/datasets/ealaxi/paysim1")
            print("  2. Download the CSV file")
            print(f"  3. Place it in: {PAYSIM_DIR}")

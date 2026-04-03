"""
SENTINEL FRAUD DETECTION - FEATURE EXTRACTION PIPELINE
=======================================================
Extracts 50+ features from raw transaction data.

Feature Categories:
1. Behavioral (Prabhat's) - velocity, time patterns, impossible travel
2. Device - fingerprint, sharing, emulation
3. Network - VPN/Tor, IP reputation, geo mismatch
4. Identity - account age, prior fraud, synthetic identity signals
5. Transactional - amount patterns, threshold evasion
6. Graph - computed from GNN (separate module)

This runs in REAL-TIME (<50ms per transaction)
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import hashlib
import math


# =============================================================================
# DATA CLASSES FOR TYPE SAFETY
# =============================================================================
@dataclass
class Transaction:
    """Raw transaction data from payment gateway."""

    transaction_id: str
    user_id: str
    amount: float
    currency: str
    merchant_id: str
    merchant_category: str
    timestamp: datetime

    # Device info
    device_id: str
    device_type: str
    user_agent: str

    # Network info
    ip_address: str
    ip_country: str
    ip_city: str

    # User info
    card_last4: str
    card_type: str
    billing_country: str
    email: str
    phone: str

    # Optional enrichment
    is_vpn: Optional[bool] = None
    is_tor: Optional[bool] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass
class UserHistory:
    """User's historical data for behavioral analysis."""

    user_id: str
    account_created_at: datetime

    # Transaction history
    transaction_count_total: int
    transaction_count_30d: int
    avg_transaction_amount: float
    std_transaction_amount: float

    # Time patterns
    typical_transaction_hours: List[int]
    typical_transaction_days: List[int]

    # Last transaction
    last_transaction_time: Optional[datetime]
    last_transaction_amount: Optional[float]
    last_transaction_geo: Optional[Tuple[float, float]]

    # Recent velocity
    transactions_last_1h: int
    transactions_last_24h: int
    amount_last_24h: float

    # Account changes
    password_changed_at: Optional[datetime]
    email_changed_at: Optional[datetime]
    card_added_at: Optional[datetime]

    # Device/network history
    known_devices: List[str]
    known_ips: List[str]

    # Risk history
    flagged_transactions_count: int
    confirmed_fraud_count: int


@dataclass
class ExtractedFeatures:
    """All extracted features ready for ML model."""

    # Categorical features (for embedding)
    categorical: Dict[str, int]

    # Numerical features (for normalization)
    numerical: np.ndarray

    # Feature names for explainability
    feature_names: List[str]

    # Raw values for logging
    raw_features: Dict[str, Any]


# =============================================================================
# FEATURE EXTRACTOR CLASS
# =============================================================================
class FeatureExtractor:
    """
    Extracts all features from a transaction in real-time.

    Design principles:
    - Fast (<50ms)
    - Stateless (all state in Redis/DB)
    - Explainable (stores raw values)
    """

    # High-risk merchant categories
    HIGH_RISK_MCC = {
        "6051": "cryptocurrency",
        "5944": "jewelry",
        "5094": "precious_stones",
        "5816": "digital_goods",
        "5817": "software",
        "5818": "gaming",
        "4829": "money_transfer",
        "5172": "petroleum_products",
        "5921": "alcohol",
        "5993": "tobacco",
    }

    # Temporary email domains
    TEMP_EMAIL_DOMAINS = {
        "tempmail.com",
        "temp-mail.org",
        "guerrillamail.com",
        "throwaway.email",
        "fakeinbox.com",
        "mailinator.com",
        "yopmail.com",
        "10minutemail.com",
        "trashmail.com",
    }

    # VoIP indicators (simplified)
    VOIP_INDICATORS = {"google", "skype", "vonage", "bandwidth", "twilio"}

    def __init__(
        self,
        velocity_window_1h: int = 3600,
        velocity_window_24h: int = 86400,
        dormant_threshold_days: int = 30,
        impossible_travel_speed_kmh: float = 1000.0,
    ):
        self.velocity_window_1h = velocity_window_1h
        self.velocity_window_24h = velocity_window_24h
        self.dormant_threshold_days = dormant_threshold_days
        self.impossible_travel_speed = impossible_travel_speed_kmh

        # Feature names for documentation
        self.numerical_feature_names = self._get_numerical_feature_names()

    def _get_numerical_feature_names(self) -> List[str]:
        """Returns ordered list of numerical feature names."""
        return [
            # Behavioral
            "velocity_1h",
            "velocity_24h",
            "amount_zscore",
            "time_deviation",
            "days_since_last",
            "dormant_to_active",
            "impossible_travel",
            "amount_velocity_24h",
            # Device
            "device_age_days",
            "is_new_device",
            "device_account_count",
            "is_emulator",
            "is_rooted",
            # Network
            "is_vpn",
            "is_tor",
            "is_proxy",
            "ip_geo_mismatch",
            "ip_risk_score",
            # Identity
            "account_age_days",
            "days_since_pwd_change",
            "days_since_card_added",
            "days_since_email_change",
            "is_temp_email",
            "is_voip_phone",
            "identity_mismatch_score",
            "recent_account_changes",
            # Transactional
            "amount_normalized",
            "merchant_risk",
            "is_threshold_evasion",
            "is_round_amount",
            "card_testing_score",
            "amount_log",
            # Risk history
            "prior_flags_count",
            "prior_fraud_count",
            "risk_history_score",
            # Synthetic identity signals
            "email_age_vs_account",
            "phone_carrier_mismatch",
            "identity_consistency_score",
            # Time features
            "hour_sin",
            "hour_cos",
            "day_of_week_sin",
            "day_of_week_cos",
            "is_weekend",
            "is_night",
            # Amount features
            "amount_percentile",
            "amount_vs_median",
            "amount_vs_max",
        ]

    def extract(
        self,
        transaction: Transaction,
        user_history: UserHistory,
        device_info: Optional[Dict] = None,
        ip_info: Optional[Dict] = None,
    ) -> ExtractedFeatures:
        """
        Extract all features from a transaction.

        Args:
            transaction: Current transaction
            user_history: User's historical data
            device_info: Device enrichment data
            ip_info: IP enrichment data

        Returns:
            ExtractedFeatures with categorical and numerical features
        """
        raw_features = {}

        # === BEHAVIORAL FEATURES ===
        behavioral = self._extract_behavioral_features(transaction, user_history)
        raw_features.update(behavioral)

        # === DEVICE FEATURES ===
        device = self._extract_device_features(transaction, user_history, device_info)
        raw_features.update(device)

        # === NETWORK FEATURES ===
        network = self._extract_network_features(transaction, ip_info)
        raw_features.update(network)

        # === IDENTITY FEATURES ===
        identity = self._extract_identity_features(transaction, user_history)
        raw_features.update(identity)

        # === TRANSACTIONAL FEATURES ===
        transactional = self._extract_transactional_features(transaction, user_history)
        raw_features.update(transactional)

        # === SYNTHETIC IDENTITY FEATURES ===
        synthetic = self._extract_synthetic_identity_features(transaction, user_history)
        raw_features.update(synthetic)

        # === TIME FEATURES ===
        time_features = self._extract_time_features(transaction)
        raw_features.update(time_features)

        # === CATEGORICAL ENCODING ===
        categorical = self._encode_categorical_features(transaction)

        # === NUMERICAL ARRAY ===
        numerical = self._create_numerical_array(raw_features)

        return ExtractedFeatures(
            categorical=categorical,
            numerical=numerical,
            feature_names=self.numerical_feature_names,
            raw_features=raw_features,
        )

    # =========================================================================
    # BEHAVIORAL FEATURES (Prabhat's Suggestions)
    # =========================================================================
    def _extract_behavioral_features(
        self, txn: Transaction, history: UserHistory
    ) -> Dict[str, float]:
        """
        Behavioral analysis based on user's historical patterns.
        """
        features = {}

        # Velocity: Transactions per time window
        features["velocity_1h"] = float(history.transactions_last_1h)
        features["velocity_24h"] = float(history.transactions_last_24h)

        # Amount anomaly: Z-score of current amount
        if history.std_transaction_amount > 0:
            features["amount_zscore"] = (
                txn.amount - history.avg_transaction_amount
            ) / history.std_transaction_amount
        else:
            features["amount_zscore"] = 0.0

        # Time deviation: Is this an unusual hour for this user?
        current_hour = txn.timestamp.hour
        if history.typical_transaction_hours:
            min_deviation = min(
                abs(current_hour - h) for h in history.typical_transaction_hours
            )
            features["time_deviation"] = float(min_deviation)
        else:
            features["time_deviation"] = 0.0

        # Days since last transaction
        if history.last_transaction_time:
            delta = txn.timestamp - history.last_transaction_time
            features["days_since_last"] = delta.total_seconds() / 86400
        else:
            features["days_since_last"] = 365.0  # New user

        # Dormant to active: Was account dormant, now suddenly active?
        features["dormant_to_active"] = float(
            features["days_since_last"] > self.dormant_threshold_days
            and history.transactions_last_24h > 3
        )

        # Impossible travel detection
        features["impossible_travel"] = self._check_impossible_travel(txn, history)

        # Amount velocity (total spent in 24h)
        features["amount_velocity_24h"] = history.amount_last_24h

        return features

    def _check_impossible_travel(self, txn: Transaction, history: UserHistory) -> float:
        """
        Check if user could physically travel between locations.

        Example: Transaction in Mumbai, then Delhi 5 minutes later
        = impossible at 1000 km/h
        """
        if not txn.latitude or not txn.longitude:
            return 0.0

        if not history.last_transaction_geo:
            return 0.0

        if not history.last_transaction_time:
            return 0.0

        # Calculate distance (Haversine formula)
        lat1, lon1 = history.last_transaction_geo
        lat2, lon2 = txn.latitude, txn.longitude

        distance_km = self._haversine(lat1, lon1, lat2, lon2)

        # Calculate time difference in hours
        time_diff = txn.timestamp - history.last_transaction_time
        hours = time_diff.total_seconds() / 3600

        if hours <= 0:
            return 1.0 if distance_km > 10 else 0.0

        # Calculate required speed
        required_speed = distance_km / hours

        # Is it impossible?
        if required_speed > self.impossible_travel_speed:
            return 1.0

        # Return normalized score (0-1)
        return min(required_speed / self.impossible_travel_speed, 1.0)

    @staticmethod
    def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two points on Earth in km."""
        R = 6371  # Earth's radius in km

        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        return R * c

    # =========================================================================
    # DEVICE FEATURES
    # =========================================================================
    def _extract_device_features(
        self, txn: Transaction, history: UserHistory, device_info: Optional[Dict]
    ) -> Dict[str, float]:
        """
        Device fingerprint analysis.
        """
        features = {}

        # Is this a new device?
        features["is_new_device"] = float(txn.device_id not in history.known_devices)

        # Device age (days since first seen)
        if device_info and "first_seen" in device_info:
            delta = txn.timestamp - device_info["first_seen"]
            features["device_age_days"] = delta.days
        else:
            features["device_age_days"] = 0.0

        # How many accounts use this device?
        if device_info and "account_count" in device_info:
            features["device_account_count"] = float(device_info["account_count"])
        else:
            features["device_account_count"] = 1.0

        # Emulator detection (from user agent)
        features["is_emulator"] = float(self._detect_emulator(txn.user_agent))

        # Rooted/jailbroken detection
        features["is_rooted"] = float(
            device_info.get("is_rooted", False) if device_info else False
        )

        return features

    @staticmethod
    def _detect_emulator(user_agent: str) -> bool:
        """Detect if device is an emulator."""
        emulator_indicators = [
            "bluestacks",
            "nox",
            "genymotion",
            "android sdk",
            "goldfish",
            "sdk_google",
            "vbox",
            "virtualbox",
        ]
        ua_lower = user_agent.lower()
        return any(indicator in ua_lower for indicator in emulator_indicators)

    # =========================================================================
    # NETWORK FEATURES
    # =========================================================================
    def _extract_network_features(
        self, txn: Transaction, ip_info: Optional[Dict]
    ) -> Dict[str, float]:
        """
        Network/IP analysis.
        """
        features = {}

        # VPN/Tor/Proxy detection
        features["is_vpn"] = float(
            txn.is_vpn or (ip_info and ip_info.get("is_vpn", False))
        )
        features["is_tor"] = float(
            txn.is_tor or (ip_info and ip_info.get("is_tor", False))
        )
        features["is_proxy"] = float(
            ip_info.get("is_proxy", False) if ip_info else False
        )

        # IP-Geo mismatch
        features["ip_geo_mismatch"] = float(txn.ip_country != txn.billing_country)

        # IP risk score (from threat intel)
        features["ip_risk_score"] = (
            float(ip_info.get("risk_score", 0) if ip_info else 0) / 100.0
        )  # Normalize to 0-1

        return features

    # =========================================================================
    # IDENTITY FEATURES
    # =========================================================================
    def _extract_identity_features(
        self, txn: Transaction, history: UserHistory
    ) -> Dict[str, float]:
        """
        Identity and account analysis.
        """
        features = {}

        # Account age
        account_age = txn.timestamp - history.account_created_at
        features["account_age_days"] = account_age.days

        # Recent account changes
        if history.password_changed_at:
            delta = txn.timestamp - history.password_changed_at
            features["days_since_pwd_change"] = delta.days
        else:
            features["days_since_pwd_change"] = 365.0

        if history.card_added_at:
            delta = txn.timestamp - history.card_added_at
            features["days_since_card_added"] = delta.days
        else:
            features["days_since_card_added"] = 365.0

        if history.email_changed_at:
            delta = txn.timestamp - history.email_changed_at
            features["days_since_email_change"] = delta.days
        else:
            features["days_since_email_change"] = 365.0

        # Temporary email detection
        email_domain = txn.email.split("@")[-1].lower()
        features["is_temp_email"] = float(email_domain in self.TEMP_EMAIL_DOMAINS)

        # VoIP phone detection (simplified)
        features["is_voip_phone"] = float(
            any(ind in txn.phone.lower() for ind in self.VOIP_INDICATORS)
        )

        # Identity mismatch score (simplified)
        # Would use fuzzy matching in production
        features["identity_mismatch_score"] = 0.0

        # Count of recent changes
        recent_changes = sum(
            [
                features["days_since_pwd_change"] < 1,
                features["days_since_card_added"] < 1,
                features["days_since_email_change"] < 1,
            ]
        )
        features["recent_account_changes"] = float(recent_changes)

        return features

    # =========================================================================
    # TRANSACTIONAL FEATURES
    # =========================================================================
    def _extract_transactional_features(
        self, txn: Transaction, history: UserHistory
    ) -> Dict[str, float]:
        """
        Transaction pattern analysis.
        """
        features = {}

        # Normalized amount
        if history.avg_transaction_amount > 0:
            features["amount_normalized"] = txn.amount / history.avg_transaction_amount
        else:
            features["amount_normalized"] = 1.0

        # Merchant risk
        features["merchant_risk"] = float(txn.merchant_category in self.HIGH_RISK_MCC)

        # Threshold evasion detection
        thresholds = [5000, 10000, 50000, 100000]
        features["is_threshold_evasion"] = float(
            any(0.95 * t <= txn.amount < t for t in thresholds)
        )

        # Round amount detection
        is_round = (txn.amount % 1000 == 0 and txn.amount >= 1000) or (
            txn.amount % 100 == 0 and txn.amount >= 100
        )
        features["is_round_amount"] = float(is_round)

        # Card testing pattern score
        # Requires sequence data - simplified here
        features["card_testing_score"] = 0.0

        # Log amount (for scale invariance)
        features["amount_log"] = math.log1p(txn.amount)

        # Risk history
        features["prior_flags_count"] = float(history.flagged_transactions_count)
        features["prior_fraud_count"] = float(history.confirmed_fraud_count)
        features["risk_history_score"] = min(
            (
                history.flagged_transactions_count * 0.1
                + history.confirmed_fraud_count * 0.5
            ),
            1.0,
        )

        return features

    # =========================================================================
    # SYNTHETIC IDENTITY FEATURES (NEW PS REQUIREMENT)
    # =========================================================================
    def _extract_synthetic_identity_features(
        self, txn: Transaction, history: UserHistory
    ) -> Dict[str, float]:
        """
        Detect synthetic identities created from stolen data.
        """
        features = {}

        # Email age vs account age
        # In production, would check email creation date
        features["email_age_vs_account"] = 0.0

        # Phone carrier region mismatch
        # Would check phone carrier region vs billing
        features["phone_carrier_mismatch"] = 0.0

        # Identity consistency score
        # Would check name-phone-email-address associations
        features["identity_consistency_score"] = 0.0

        return features

    # =========================================================================
    # TIME FEATURES
    # =========================================================================
    def _extract_time_features(self, txn: Transaction) -> Dict[str, float]:
        """
        Cyclical time encoding for temporal patterns.
        """
        features = {}

        hour = txn.timestamp.hour
        day_of_week = txn.timestamp.weekday()

        # Cyclical encoding (sin/cos for continuity)
        features["hour_sin"] = math.sin(2 * math.pi * hour / 24)
        features["hour_cos"] = math.cos(2 * math.pi * hour / 24)
        features["day_of_week_sin"] = math.sin(2 * math.pi * day_of_week / 7)
        features["day_of_week_cos"] = math.cos(2 * math.pi * day_of_week / 7)

        # Binary features
        features["is_weekend"] = float(day_of_week >= 5)
        features["is_night"] = float(hour < 6 or hour >= 22)

        # Amount percentile features (requires global stats)
        features["amount_percentile"] = 0.5  # Would compute from distribution
        features["amount_vs_median"] = 0.0
        features["amount_vs_max"] = 0.0

        return features

    # =========================================================================
    # ENCODING HELPERS
    # =========================================================================
    def _encode_categorical_features(self, txn: Transaction) -> Dict[str, int]:
        """
        Encode categorical features as integers for embedding layers.
        """

        # Simple hash-based encoding (production would use LabelEncoder)
        def hash_encode(value: str, max_val: int) -> int:
            return int(hashlib.md5(value.encode()).hexdigest(), 16) % max_val + 1

        return {
            "merchant_category": hash_encode(txn.merchant_category, 100),
            "device_type": hash_encode(txn.device_type, 10),
            "card_type": hash_encode(txn.card_type, 5),
            "country": hash_encode(txn.billing_country, 250),
            "email_domain": hash_encode(txn.email.split("@")[-1], 1000),
        }

    def _create_numerical_array(self, raw_features: Dict[str, float]) -> np.ndarray:
        """
        Create ordered numpy array from raw features.
        """
        return np.array(
            [raw_features.get(name, 0.0) for name in self.numerical_feature_names],
            dtype=np.float32,
        )


# =============================================================================
# BATCH FEATURE EXTRACTOR (For Training)
# =============================================================================
class BatchFeatureExtractor:
    """
    Batch feature extraction for training datasets.
    Processes entire DataFrames efficiently.
    """

    def __init__(self):
        self.extractor = FeatureExtractor()

    def extract_from_dataframe(
        self, df: pd.DataFrame, user_histories: Dict[str, UserHistory]
    ) -> Tuple[Dict[str, np.ndarray], np.ndarray]:
        """
        Extract features from a pandas DataFrame.

        Returns:
            categorical_features: Dict of arrays
            numerical_features: 2D array
        """
        categorical_results = {
            name: []
            for name in [
                "merchant_category",
                "device_type",
                "card_type",
                "country",
                "email_domain",
            ]
        }
        numerical_results = []

        for _, row in df.iterrows():
            txn = self._row_to_transaction(row)
            history = user_histories.get(
                txn.user_id, self._default_history(txn.user_id)
            )

            features = self.extractor.extract(txn, history)

            for name, value in features.categorical.items():
                categorical_results[name].append(value)

            numerical_results.append(features.numerical)

        return (
            {name: np.array(values) for name, values in categorical_results.items()},
            np.stack(numerical_results),
        )

    @staticmethod
    def _row_to_transaction(row: pd.Series) -> Transaction:
        """Convert DataFrame row to Transaction object."""
        return Transaction(
            transaction_id=str(row.get("TransactionID", "")),
            user_id=str(row.get("user_id", "")),
            amount=float(row.get("TransactionAmt", 0)),
            currency=str(row.get("currency", "USD")),
            merchant_id=str(row.get("merchant_id", "")),
            merchant_category=str(row.get("ProductCD", "W")),
            timestamp=pd.to_datetime(row.get("TransactionDT", 0), unit="s"),
            device_id=str(row.get("DeviceInfo", "")),
            device_type=str(row.get("DeviceType", "desktop")),
            user_agent=str(row.get("user_agent", "")),
            ip_address=str(row.get("ip_address", "")),
            ip_country=str(row.get("addr1", "")),
            ip_city=str(row.get("addr2", "")),
            card_last4=str(row.get("card1", ""))[-4:],
            card_type=str(row.get("card4", "visa")),
            billing_country=str(row.get("addr1", "")),
            email=str(row.get("P_emaildomain", "")),
            phone=str(row.get("phone", "")),
        )

    @staticmethod
    def _default_history(user_id: str) -> UserHistory:
        """Create default history for new users."""
        return UserHistory(
            user_id=user_id,
            account_created_at=datetime.now() - timedelta(days=30),
            transaction_count_total=0,
            transaction_count_30d=0,
            avg_transaction_amount=100.0,
            std_transaction_amount=50.0,
            typical_transaction_hours=[9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
            typical_transaction_days=[0, 1, 2, 3, 4],
            last_transaction_time=None,
            last_transaction_amount=None,
            last_transaction_geo=None,
            transactions_last_1h=0,
            transactions_last_24h=0,
            amount_last_24h=0.0,
            password_changed_at=None,
            email_changed_at=None,
            card_added_at=None,
            known_devices=[],
            known_ips=[],
            flagged_transactions_count=0,
            confirmed_fraud_count=0,
        )


if __name__ == "__main__":
    print("Feature Extractor Test")
    print("=" * 50)

    # Create test transaction
    test_txn = Transaction(
        transaction_id="TXN-12345",
        user_id="USER-001",
        amount=49990.0,  # Threshold evasion!
        currency="INR",
        merchant_id="MERCHANT-001",
        merchant_category="6051",  # Crypto - high risk!
        timestamp=datetime.now(),
        device_id="DEVICE-NEW",  # New device!
        device_type="mobile",
        user_agent="Mozilla/5.0 (Linux; Android)",
        ip_address="45.33.32.156",
        ip_country="US",
        ip_city="New York",
        card_last4="1234",
        card_type="visa",
        billing_country="IN",  # Geo mismatch!
        email="user@tempmail.com",  # Temp email!
        phone="+1234567890",
        is_vpn=True,  # VPN!
        latitude=40.7128,
        longitude=-74.0060,
    )

    # Create test history
    test_history = UserHistory(
        user_id="USER-001",
        account_created_at=datetime.now() - timedelta(days=2),  # New account!
        transaction_count_total=5,
        transaction_count_30d=5,
        avg_transaction_amount=500.0,
        std_transaction_amount=200.0,
        typical_transaction_hours=[10, 11, 12, 14, 15],
        typical_transaction_days=[0, 1, 2, 3, 4],
        last_transaction_time=datetime.now() - timedelta(minutes=5),
        last_transaction_amount=100.0,
        last_transaction_geo=(19.0760, 72.8777),  # Mumbai
        transactions_last_1h=3,
        transactions_last_24h=5,
        amount_last_24h=1500.0,
        password_changed_at=datetime.now() - timedelta(hours=2),  # Recent!
        email_changed_at=None,
        card_added_at=datetime.now() - timedelta(hours=1),  # Very recent!
        known_devices=["DEVICE-OLD"],
        known_ips=["192.168.1.1"],
        flagged_transactions_count=1,
        confirmed_fraud_count=0,
    )

    # Extract features
    extractor = FeatureExtractor()
    features = extractor.extract(test_txn, test_history)

    print("\n📊 EXTRACTED FEATURES:")
    print(f"\nCategorical ({len(features.categorical)}):")
    for name, value in features.categorical.items():
        print(f"  {name}: {value}")

    print(f"\nNumerical ({len(features.numerical)}):")
    for name, value in zip(features.feature_names, features.numerical):
        if value != 0:
            print(f"  {name}: {value:.4f}")

    print("\n🚨 HIGH RISK SIGNALS DETECTED:")
    for name, value in features.raw_features.items():
        if isinstance(value, (int, float)) and value > 0.5:
            print(f"  ⚠️ {name}: {value}")

import numpy as np
from datetime import datetime, timezone, timedelta
from typing import Optional
from sklearn.ensemble import IsolationForest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared import Metric, Alert
from .notifier import send_slack_alert


class AnomalyDetector:
    """Isolation Forest based anomaly detector for metrics."""

    def __init__(self, contamination: float = 0.05):
        """
        Initialize the detector.

        Args:
            contamination: Expected proportion of anomalies (default 5%)
        """
        self.model: Optional[IsolationForest] = None
        self.contamination = contamination
        self.feature_names = ["cpu_percent", "memory_percent", "disk_percent"]
        self.last_trained: Optional[datetime] = None
        self.min_samples = 50  # Minimum samples needed to train

    def _extract_features(self, metric: Metric) -> Optional[np.ndarray]:
        """Extract feature vector from a metric."""
        values = []
        for name in self.feature_names:
            val = getattr(metric, name)
            if val is None:
                return None  # Skip metrics with missing values
            values.append(val)
        return np.array(values)

    async def train(self, session: AsyncSession, host: str) -> bool:
        """
        Train the model on historical data for a specific host.

        Returns True if training was successful.
        """
        # Get last 24 hours of data
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await session.execute(
            select(Metric)
            .where(Metric.host == host)
            .where(Metric.timestamp >= since)
            .order_by(Metric.timestamp.desc())
        )
        metrics = result.scalars().all()

        # Extract features
        features = []
        for metric in metrics:
            feat = self._extract_features(metric)
            if feat is not None:
                features.append(feat)

        if len(features) < self.min_samples:
            return False  # Not enough data

        X = np.array(features)
        self.model = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_estimators=100,
        )
        self.model.fit(X)
        self.last_trained = datetime.now(timezone.utc)
        return True

    def predict(self, metric: Metric) -> Optional[bool]:
        """
        Predict if a metric is anomalous.

        Returns:
            True if anomalous, False if normal, None if can't predict
        """
        if self.model is None:
            return None

        features = self._extract_features(metric)
        if features is None:
            return None

        # Reshape for single sample prediction
        X = features.reshape(1, -1)
        prediction = self.model.predict(X)[0]

        # Isolation Forest returns -1 for anomalies, 1 for normal
        return prediction == -1

    def get_anomaly_score(self, metric: Metric) -> Optional[float]:
        """
        Get the anomaly score for a metric.

        Returns a score where lower (more negative) = more anomalous.
        """
        if self.model is None:
            return None

        features = self._extract_features(metric)
        if features is None:
            return None

        X = features.reshape(1, -1)
        return float(self.model.score_samples(X)[0])


# Global detector instances per host
_detectors: dict[str, AnomalyDetector] = {}


def get_detector(host: str) -> AnomalyDetector:
    """Get or create a detector for a host."""
    if host not in _detectors:
        _detectors[host] = AnomalyDetector()
    return _detectors[host]


async def check_ml_anomaly(metric: Metric, session: AsyncSession) -> Optional[Alert]:
    """
    Check if a metric is anomalous using ML.

    Returns an Alert if anomalous, None otherwise.
    """
    detector = get_detector(metric.host)

    # Retrain if needed (every hour or if never trained)
    should_train = (
        detector.last_trained is None or
        datetime.now(timezone.utc) - detector.last_trained > timedelta(hours=1)
    )

    if should_train:
        trained = await detector.train(session, metric.host)
        if not trained:
            return None  # Not enough data to detect anomalies

    # Check for anomaly
    is_anomaly = detector.predict(metric)
    if not is_anomaly:
        return None

    # Get anomaly score for context
    score = detector.get_anomaly_score(metric)
    score_str = f" (score: {score:.3f})" if score else ""

    message = (
        f"ML anomaly detected on {metric.host}: "
        f"cpu={metric.cpu_percent:.1f}%, "
        f"mem={metric.memory_percent:.1f}%, "
        f"disk={metric.disk_percent:.1f}%"
        f"{score_str}"
    )

    await send_slack_alert("warning", message)

    return Alert(
        timestamp=datetime.now(timezone.utc),
        host=metric.host,
        metric_type="ml_anomaly",
        severity="warning",
        message=message,
        status="pending",
    )

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
        self.model: Optional[IsolationForest] = None
        self.contamination = contamination
        self.feature_names = ["cpu_percent", "memory_percent", "disk_percent"]
        self.last_trained: Optional[datetime] = None
        self.min_samples = 50

    def _extract_features(self, metric: Metric) -> Optional[np.ndarray]:
        values = []
        for name in self.feature_names:
            prefix = name.split("_")[0]
            val = getattr(metric, f"{prefix}_max", None) or getattr(metric, name)
            if val is None:
                return None
            values.append(val)
        return np.array(values)

    async def train(self, session: AsyncSession, host: str) -> bool:
        since = datetime.now(timezone.utc) - timedelta(hours=24)
        result = await session.execute(
            select(Metric)
            .where(Metric.host == host)
            .where(Metric.timestamp >= since)
            .order_by(Metric.timestamp.desc())
        )
        metrics = result.scalars().all()

        features = []
        for metric in metrics:
            feat = self._extract_features(metric)
            if feat is not None:
                features.append(feat)

        if len(features) < self.min_samples:
            return False

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
        if self.model is None:
            return None

        features = self._extract_features(metric)
        if features is None:
            return None

        X = features.reshape(1, -1)
        prediction = self.model.predict(X)[0]
        return prediction == -1

    def get_anomaly_score(self, metric: Metric) -> Optional[float]:
        if self.model is None:
            return None

        features = self._extract_features(metric)
        if features is None:
            return None

        X = features.reshape(1, -1)
        return float(self.model.score_samples(X)[0])


_detectors: dict[str, AnomalyDetector] = {}


def get_detector(host: str) -> AnomalyDetector:
    if host not in _detectors:
        _detectors[host] = AnomalyDetector()
    return _detectors[host]


async def check_ml_anomaly(metric: Metric, session: AsyncSession) -> Optional[Alert]:
    detector = get_detector(metric.host)

    should_train = (
        detector.last_trained is None or
        datetime.now(timezone.utc) - detector.last_trained > timedelta(hours=1)
    )

    if should_train:
        trained = await detector.train(session, metric.host)
        if not trained:
            return None

    is_anomaly = detector.predict(metric)
    if not is_anomaly:
        return None

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

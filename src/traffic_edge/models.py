from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TrafficReading:
    junction_id: str
    timestamp: str
    vehicle_count: int
    avg_speed: float
    queue_length: int
    lane_occupancy: float
    waiting_time: float
    traffic_flow: float
    signal_state: str

    @classmethod
    def now(cls, junction_id: str, **values: Any) -> "TrafficReading":
        return cls(
            junction_id=junction_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            **values,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrafficResult:
    reading: TrafficReading
    congestion: str
    congestion_score: int
    status: str
    anomalies: tuple[str, ...]
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return {
            **self.reading.to_dict(),
            "congestion": self.congestion,
            "congestion_score": self.congestion_score,
            "status": self.status,
            "anomalies": list(self.anomalies),
            "recommendation": self.recommendation,
        }
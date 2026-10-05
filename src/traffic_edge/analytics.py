from collections.abc import Sequence

from .models import TrafficReading, TrafficResult

LEVELS = ("NORMAL", "MODERATE", "HIGH", "CRITICAL")


def _score(value: float, thresholds: tuple[float, float, float], inverse: bool = False) -> int:
    if inverse:
        return sum(value < threshold for threshold in thresholds)
    return sum(value >= threshold for threshold in thresholds)


def validate_reading(reading: TrafficReading) -> list[str]:
    errors: list[str] = []
    if not reading.junction_id:
        errors.append("junction_id is required")
    if reading.vehicle_count < 0:
        errors.append("vehicle_count must be non-negative")
    if reading.avg_speed < 0:
        errors.append("avg_speed must be non-negative")
    if reading.queue_length < 0:
        errors.append("queue_length must be non-negative")
    if not 0 <= reading.lane_occupancy <= 100:
        errors.append("lane_occupancy must be between 0 and 100")
    if reading.waiting_time < 0:
        errors.append("waiting_time must be non-negative")
    if reading.traffic_flow < 0:
        errors.append("traffic_flow must be non-negative")
    if reading.signal_state not in {"RED", "YELLOW", "GREEN"}:
        errors.append("signal_state must be RED, YELLOW, or GREEN")
    return errors


def classify_congestion(reading: TrafficReading) -> tuple[str, int]:
    score = (
        _score(reading.avg_speed, (20, 10, 5), inverse=True)
        + _score(reading.queue_length, (20, 40, 60))
        + _score(reading.lane_occupancy, (50, 70, 85))
        + _score(reading.waiting_time, (45, 90, 150))
    )
    level = min(score // 3, len(LEVELS) - 1)
    return LEVELS[level], score


def detect_anomalies(current: TrafficReading, history: Sequence[TrafficReading]) -> tuple[str, ...]:
    if not history:
        return ()
    previous = history[-1]
    anomalies: list[str] = []
    if current.vehicle_count > max(previous.vehicle_count * 1.75, previous.vehicle_count + 20):
        anomalies.append("sudden vehicle-count increase")
    if previous.avg_speed - current.avg_speed >= 15:
        anomalies.append("sudden slowdown")
    if current.queue_length - previous.queue_length >= 30:
        anomalies.append("rapid queue growth")
    return tuple(anomalies)


def recommendation(reading: TrafficReading, congestion: str, propagated_from: str | None = None) -> str:
    if congestion == "CRITICAL":
        action = "Increase green duration and reduce unnecessary red time."
    elif congestion == "HIGH":
        action = "Prepare additional green time for the congested approach."
    elif congestion == "MODERATE":
        action = "Monitor queue growth and keep the current signal plan."
    else:
        action = "No signal adjustment required."
    if propagated_from:
        action += f" Propagation risk detected from {propagated_from}."
    return action


def analyze_reading(
    reading: TrafficReading,
    history: Sequence[TrafficReading] = (),
    propagated_from: str | None = None,
) -> TrafficResult:
    errors = validate_reading(reading)
    if errors:
        raise ValueError("Invalid traffic reading: " + "; ".join(errors))
    congestion, score = classify_congestion(reading)
    status = "OK" if congestion in {"NORMAL", "MODERATE"} else "WARNING"
    if congestion == "CRITICAL":
        status = "CRITICAL"
    return TrafficResult(
        reading=reading,
        congestion=congestion,
        congestion_score=score,
        status=status,
        anomalies=detect_anomalies(reading, history),
        recommendation=recommendation(reading, congestion, propagated_from),
    )
from collections import defaultdict, deque
from collections.abc import Iterable

from .analytics import analyze_reading, classify_congestion
from .models import TrafficReading, TrafficResult


class EdgePipeline:
    """Validate, analyze, and retain a small rolling history per junction."""

    def __init__(self, history_size: int = 5) -> None:
        self.history: dict[str, deque[TrafficReading]] = defaultdict(lambda: deque(maxlen=history_size))
        self.latest: dict[str, TrafficResult] = {}

    def process(self, reading: TrafficReading) -> TrafficResult:
        propagated_from = self._propagation_source(reading)
        result = analyze_reading(reading, self.history[reading.junction_id], propagated_from)
        self.history[reading.junction_id].append(reading)
        self.latest[reading.junction_id] = result
        return result

    def process_many(self, readings: Iterable[TrafficReading]) -> list[TrafficResult]:
        return [self.process(reading) for reading in readings]

    def _propagation_source(self, reading: TrafficReading) -> str | None:
        junction_number = int(reading.junction_id.removeprefix("J"))
        neighbors = [f"J{junction_number - 1}", f"J{junction_number + 1}"]
        current_level, _ = classify_congestion(reading)
        if current_level not in {"HIGH", "CRITICAL"}:
            return None
        for neighbor in neighbors:
            neighbor_result = self.latest.get(neighbor)
            if neighbor_result and neighbor_result.congestion in {"HIGH", "CRITICAL"}:
                return neighbor
        return None
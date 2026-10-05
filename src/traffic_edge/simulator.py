import random
from collections.abc import Iterator

from .models import TrafficReading

SCENARIOS = {"live", "normal", "heavy", "congested", "abnormal"}


def generate_reading(junction_id: str, scenario: str = "normal", rng: random.Random | None = None) -> TrafficReading:
    if scenario not in SCENARIOS:
        raise ValueError(f"Unknown scenario: {scenario}")
    randomizer = rng or random
    scenario = "normal" if scenario == "live" else scenario
    ranges = {
        "normal": (20, 60, 35, 50, 15, 35, 45, 75),
        "heavy": (50, 100, 12, 28, 35, 65, 60, 120),
        "congested": (80, 140, 3, 14, 60, 95, 100, 220),
        "abnormal": (120, 220, 0, 8, 80, 100, 180, 400),
    }
    vehicles_low, vehicles_high, speed_low, speed_high, queue_low, queue_high, wait_low, wait_high = ranges[scenario]
    vehicles = randomizer.randint(vehicles_low, vehicles_high)
    return TrafficReading.now(
        junction_id,
        vehicle_count=vehicles,
        avg_speed=round(randomizer.uniform(speed_low, speed_high), 1),
        queue_length=randomizer.randint(queue_low, queue_high),
        lane_occupancy=round(randomizer.uniform(queue_low, queue_high), 1),
        waiting_time=round(randomizer.uniform(wait_low, wait_high), 1),
        traffic_flow=round(randomizer.uniform(20, 80), 1),
        signal_state=randomizer.choice(("RED", "GREEN", "YELLOW")),
    )


def stream_readings(
    scenarios: dict[str, str], count: int | None, seed: int | None = None
) -> Iterator[TrafficReading]:
    rng = random.Random(seed)
    junctions = tuple(scenarios)
    cycle = 0
    while count is None or cycle < count:
        for junction_id in junctions:
            yield generate_reading(junction_id, scenarios[junction_id], rng)
        cycle += 1
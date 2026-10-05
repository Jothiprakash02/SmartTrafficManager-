import random
import types

import pytest

from traffic_edge.analytics import analyze_reading, classify_congestion
from traffic_edge.models import TrafficReading
from traffic_edge.pipeline import EdgePipeline
from traffic_edge.simulator import generate_reading, stream_readings
from traffic_edge.mqtt_publisher import publish_readings


def reading(**overrides: object) -> TrafficReading:
    values = {
        "junction_id": "J1",
        "timestamp": "2026-10-05T10:25:01+00:00",
        "vehicle_count": 30,
        "avg_speed": 45.0,
        "queue_length": 10,
        "lane_occupancy": 35.0,
        "waiting_time": 20.0,
        "traffic_flow": 40.0,
        "signal_state": "GREEN",
    }
    values.update(overrides)
    return TrafficReading(**values)


def test_congested_reading_is_critical():
    result = analyze_reading(reading(avg_speed=5, queue_length=75, lane_occupancy=92, waiting_time=180))
    assert result.congestion == "CRITICAL"
    assert result.status == "CRITICAL"
    assert "green duration" in result.recommendation


def test_invalid_reading_is_rejected():
    with pytest.raises(ValueError, match="lane_occupancy"):
        analyze_reading(reading(lane_occupancy=101))


def test_anomalies_compare_with_previous_reading():
    previous = reading(vehicle_count=50, avg_speed=40, queue_length=10)
    current = reading(vehicle_count=120, avg_speed=20, queue_length=50)
    result = analyze_reading(current, [previous])
    assert set(result.anomalies) == {
        "sudden vehicle-count increase",
        "sudden slowdown",
        "rapid queue growth",
    }


def test_pipeline_detects_neighbor_propagation():
    pipeline = EdgePipeline()
    pipeline.process(reading(junction_id="J1", avg_speed=8, queue_length=70, lane_occupancy=90, waiting_time=180))
    result = pipeline.process(reading(junction_id="J2", avg_speed=8, queue_length=70, lane_occupancy=90, waiting_time=180))
    assert "J1" in result.recommendation


def test_simulator_is_seeded_and_supports_congestion():
    first = generate_reading("J1", "congested", random.Random(7))
    second = generate_reading("J1", "congested", random.Random(7))
    assert first.to_dict() | {"timestamp": ""} == second.to_dict() | {"timestamp": ""}
    assert classify_congestion(first)[0] in {"HIGH", "CRITICAL"}


def test_live_stream_covers_all_junctions_continuously():
    readings = list(stream_readings({"J1": "live", "J2": "live", "J3": "live"}, 2, seed=11))
    assert [reading.junction_id for reading in readings] == ["J1", "J2", "J3", "J1", "J2", "J3"]
    assert all(reading.vehicle_count >= 0 for reading in readings)


def test_mqtt_publisher_supports_opcua_topic_namespace(monkeypatch):
    published = []

    class FakeResult:
        def wait_for_publish(self):
            return None

    class FakeClient:
        def connect(self, *args):
            return None

        def loop_start(self):
            return None

        def loop_stop(self):
            return None

        def publish(self, topic, payload, qos):
            published.append((topic, payload, qos))
            return FakeResult()

        def disconnect(self):
            return None

    class FakeMqtt:
        CallbackAPIVersion = type("CallbackAPIVersion", (), {"VERSION2": 2})

        @staticmethod
        def Client(*args):
            return FakeClient()

    paho_mqtt = types.ModuleType("paho.mqtt")
    paho_mqtt.client = FakeMqtt
    monkeypatch.setitem(__import__("sys").modules, "paho.mqtt", paho_mqtt)
    monkeypatch.setitem(__import__("sys").modules, "paho.mqtt.client", FakeMqtt)
    publish_readings([reading(junction_id="J1")], topic_prefix="traffic/opcua/junction/")
    assert published[0][0] == "traffic/opcua/junction/J1"
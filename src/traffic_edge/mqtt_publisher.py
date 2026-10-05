import json
import time
from collections.abc import Iterable

from .models import TrafficReading


def publish_readings(
    readings: Iterable[TrafficReading],
    broker: str = "localhost",
    port: int = 1883,
    interval: float = 0.0,
) -> None:
    """Publish readings to traffic/junction/<id>; paho is an optional extra."""
    try:
        import paho.mqtt.client as mqtt
    except ImportError as error:
        raise RuntimeError("Install MQTT support with: pip install .[mqtt]") from error

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(broker, port, 60)
    client.loop_start()
    try:
        for reading in readings:
            topic = f"traffic/junction/{reading.junction_id}"
            result = client.publish(topic, json.dumps(reading.to_dict()), qos=1)
            result.wait_for_publish()
            if interval:
                time.sleep(interval)
    finally:
        client.loop_stop()
        client.disconnect()
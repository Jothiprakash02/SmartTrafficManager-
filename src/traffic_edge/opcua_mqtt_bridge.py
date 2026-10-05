"""Bridge OPC UA junction nodes into the application's MQTT topics."""

import asyncio
import os

from .mqtt_publisher import publish_readings
from .opcua_bridge import poll_readings


async def run_bridge(endpoint: str, broker: str, interval: float) -> None:
    while True:
        try:
            readings = poll_readings(endpoint, interval=interval)
            batch = []
            async for reading in readings:
                batch.append(reading)
                if len(batch) == 3:
                    publish_readings(batch, broker=broker, interval=0, topic_prefix="traffic/opcua/junction/")
                    batch.clear()
        except Exception as error:
            print(f"OPC UA bridge waiting for source: {error}", flush=True)
            await asyncio.sleep(3)


def main() -> None:
    asyncio.run(run_bridge(
        os.getenv("OPCUA_ENDPOINT", "opc.tcp://opcua-simulator:4840/traffic/"),
        os.getenv("MQTT_BROKER", "mosquitto"),
        float(os.getenv("INTERVAL", "1")),
    ))


if __name__ == "__main__":
    main()

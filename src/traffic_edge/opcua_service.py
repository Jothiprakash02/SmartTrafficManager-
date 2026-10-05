"""Runnable continuous OPC UA traffic simulator."""

import asyncio
import os

from .models import TrafficReading
from .simulator import generate_reading


async def run_live_server(endpoint: str, interval: float = 1.0) -> None:
    try:
        from asyncua import Server
    except ImportError as error:
        raise RuntimeError("Install OPC UA support with: pip install .[opcua]") from error

    server = Server()
    await server.init()
    server.set_endpoint(endpoint)
    namespace = await server.register_namespace("traffic-edge")
    junctions = await server.nodes.objects.add_object(namespace, "Junctions")
    nodes: dict[str, dict[str, object]] = {}
    for junction_id in ("J1", "J2", "J3"):
        junction = await junctions.add_object(namespace, junction_id)
        nodes[junction_id] = {
            "vehicle_count": await junction.add_variable(namespace, "VehicleCount", 0),
            "avg_speed": await junction.add_variable(namespace, "AverageSpeed", 0.0),
            "queue_length": await junction.add_variable(namespace, "QueueLength", 0),
            "lane_occupancy": await junction.add_variable(namespace, "LaneOccupancy", 0.0),
            "waiting_time": await junction.add_variable(namespace, "WaitingTime", 0.0),
            "traffic_flow": await junction.add_variable(namespace, "TrafficFlow", 0.0),
            "signal_state": await junction.add_variable(namespace, "SignalState", "RED"),
        }
    for junction_nodes in nodes.values():
        for node in junction_nodes.values():
            await node.set_writable()

    async with server:
        while True:
            for junction_id in nodes:
                reading = generate_reading(junction_id, "live")
                for field, node in nodes[junction_id].items():
                    await node.write_value(getattr(reading, field))
            await asyncio.sleep(interval)


def main() -> None:
    asyncio.run(run_live_server(os.getenv("OPCUA_ENDPOINT", "opc.tcp://0.0.0.0:4840/traffic/"), float(os.getenv("INTERVAL", "1"))))


if __name__ == "__main__":
    main()

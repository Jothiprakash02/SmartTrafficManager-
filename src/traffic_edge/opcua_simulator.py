"""Optional OPC UA traffic source for industrial-ingestion demonstrations."""

import asyncio
from collections.abc import Iterable

from .models import TrafficReading

NODE_FIELDS = (
    "vehicle_count",
    "avg_speed",
    "queue_length",
    "lane_occupancy",
    "waiting_time",
    "traffic_flow",
    "signal_state",
)


async def run_server(
    readings: Iterable[TrafficReading],
    endpoint: str = "opc.tcp://0.0.0.0:4840/traffic/",
) -> None:
    """Expose readings as OPC UA nodes until the supplied readings are exhausted."""
    try:
        from asyncua import Server
    except ImportError as error:
        raise RuntimeError("Install OPC UA support with: pip install .[opcua]") from error

    server = Server()
    await server.init()
    server.set_endpoint(endpoint)
    namespace = await server.register_namespace("traffic-edge")
    readings = tuple(readings)
    junctions = server.nodes.objects.add_object(namespace, "Junctions")
    nodes: dict[str, dict[str, object]] = {}
    for junction_id in {reading.junction_id for reading in readings}:
        junction = junctions.add_object(namespace, junction_id)
        nodes[junction_id] = {
            "vehicle_count": junction.add_variable(namespace, "VehicleCount", 0),
            "avg_speed": junction.add_variable(namespace, "AverageSpeed", 0.0),
            "queue_length": junction.add_variable(namespace, "QueueLength", 0),
            "lane_occupancy": junction.add_variable(namespace, "LaneOccupancy", 0.0),
            "waiting_time": junction.add_variable(namespace, "WaitingTime", 0.0),
            "traffic_flow": junction.add_variable(namespace, "TrafficFlow", 0.0),
            "signal_state": junction.add_variable(namespace, "SignalState", "RED"),
        }
    for junction_nodes in nodes.values():
        for node in junction_nodes.values():
            await node.set_writable()
    async with server:
        for reading in readings:
            for field in NODE_FIELDS:
                value = getattr(reading, field)
                await nodes[reading.junction_id][field].write_value(value)
            await asyncio.sleep(1)

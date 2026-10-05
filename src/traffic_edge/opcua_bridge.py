"""Read the optional OPC UA simulator into the common traffic model."""

import asyncio
from collections.abc import AsyncIterator, Sequence

from .models import TrafficReading


async def poll_readings(
    endpoint: str,
    junction_ids: Sequence[str] = ("J1", "J2", "J3"),
    interval: float = 1.0,
) -> AsyncIterator[TrafficReading]:
    """Yield normalized readings from the simulator's browsable node hierarchy."""
    try:
        from asyncua import Client
    except ImportError as error:
        raise RuntimeError("Install OPC UA support with: pip install .[opcua]") from error

    async with Client(url=endpoint) as client:
        namespace = await client.get_namespace_index("traffic-edge")
        objects = client.nodes.objects
        junction_fields = {}
        for junction_id in junction_ids:
            junction = await objects.get_child([f"{namespace}:Junctions", f"{namespace}:{junction_id}"])
            junction_fields[junction_id] = {
                "vehicle_count": await junction.get_child(f"{namespace}:VehicleCount"),
                "avg_speed": await junction.get_child(f"{namespace}:AverageSpeed"),
                "queue_length": await junction.get_child(f"{namespace}:QueueLength"),
                "lane_occupancy": await junction.get_child(f"{namespace}:LaneOccupancy"),
                "waiting_time": await junction.get_child(f"{namespace}:WaitingTime"),
                "traffic_flow": await junction.get_child(f"{namespace}:TrafficFlow"),
                "signal_state": await junction.get_child(f"{namespace}:SignalState"),
            }
        while True:
            for junction_id, fields in junction_fields.items():
                values = {name: await node.read_value() for name, node in fields.items()}
                yield TrafficReading.now(junction_id, **values)
            await asyncio.sleep(interval)
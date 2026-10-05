import argparse
import json
import time

from .mqtt_publisher import publish_readings
from .pipeline import EdgePipeline
from .simulator import SCENARIOS, stream_readings


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the simulated traffic edge pipeline")
    parser.add_argument("--cycles", type=int, default=3)
    parser.add_argument("--interval", type=float, default=0.0)
    parser.add_argument("--scenario", choices=sorted(SCENARIOS), default="normal")
    parser.add_argument("--forever", action="store_true", help="continue publishing until interrupted")
    parser.add_argument("--mqtt", action="store_true", help="publish readings to MQTT instead of printing JSON")
    parser.add_argument("--broker", default="localhost")
    parser.add_argument("--port", type=int, default=1883)
    args = parser.parse_args()
    scenarios = {"J1": args.scenario, "J2": args.scenario, "J3": args.scenario}
    readings = stream_readings(scenarios, None if args.forever else args.cycles, seed=42)
    if args.mqtt:
        publish_readings(readings, args.broker, args.port, args.interval)
        return
    pipeline = EdgePipeline()
    for reading in readings:
        print(json.dumps(pipeline.process(reading).to_dict()))
        if args.interval:
            time.sleep(args.interval)


if __name__ == "__main__":
    main()
import csv
import io
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

import paho.mqtt.client as mqtt

_container_web_root = Path("/app/web")
WEB_ROOT = _container_web_root if _container_web_root.is_dir() else Path(__file__).resolve().parents[2] / "web"
BROKER = os.getenv("MQTT_BROKER", "mosquitto")
INFLUX_URL = os.getenv("INFLUX_URL", "http://influxdb:8086")
INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "traffic-demo-token")


def query_latest() -> list[dict]:
    query = 'from(bucket: "traffic") |> range(start: -15m) |> filter(fn: (r) => r._measurement == "traffic") |> sort(columns: ["_time"], desc: true)'
    body = json.dumps({"query": query, "type": "flux"}).encode()
    request = Request(
        f"{INFLUX_URL}/api/v2/query?org=traffic",
        data=body,
        headers={"Authorization": f"Token {INFLUX_TOKEN}", "Accept": "application/csv", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=3) as response:
            rows = list(csv.DictReader(io.StringIO(response.read().decode())))
    except Exception:
        rows = []
    latest = {junction_id: {"junction_id": junction_id, "status": "OFFLINE"} for junction_id in ("J1", "J2", "J3")}
    for row in rows:
        junction_id = row.get("junction_id")
        field = row.get("_field")
        if junction_id in latest and field and field not in latest[junction_id]:
            latest[junction_id][field] = row.get("_value")
            latest[junction_id]["junction_id"] = junction_id
    for junction in latest.values():
        for field in ("vehicle_count", "queue_length", "congestion_score"):
            if field in junction:
                junction[field] = int(float(junction[field]))
        for field in ("avg_speed", "lane_occupancy", "waiting_time", "traffic_flow"):
            if field in junction:
                junction[field] = round(float(junction[field]), 1)
        if "congestion_score" in junction:
            score = junction["congestion_score"]
            junction["congestion"] = "CRITICAL" if score >= 9 else "HIGH" if score >= 6 else "MODERATE" if score >= 3 else "NORMAL"
            junction["status"] = "CRITICAL" if junction["congestion"] == "CRITICAL" else "WARNING" if junction["congestion"] == "HIGH" else "OK"
            junction["recommendation"] = "Increase green duration" if junction["congestion"] == "CRITICAL" else "Prepare additional green time" if junction["congestion"] == "HIGH" else "Monitor current signal plan"
    return list(latest.values())


def publish_readings(readings: list[dict]) -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(BROKER, 1883, 10)
    client.loop_start()
    try:
        for reading in readings:
            client.publish(f"traffic/junction/{reading['junction_id']}", json.dumps(reading), qos=1).wait_for_publish()
    finally:
        client.loop_stop()
        client.disconnect()


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/status":
            self.send_json({"junctions": query_latest()})
            return
        relative_path = "index.html" if path == "/" else path.lstrip("/")
        file_path = (WEB_ROOT / relative_path).resolve()
        if file_path.is_file() and WEB_ROOT.resolve() in file_path.parents:
            content_type = "text/html" if file_path.suffix == ".html" else "text/css" if file_path.suffix == ".css" else "application/javascript"
            data = file_path.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_json({"error": "not found"}, 404)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/feed":
            self.send_json({"error": "not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length))
            readings = payload["readings"]
            if {reading.get("junction_id") for reading in readings} != {"J1", "J2", "J3"}:
                raise ValueError("readings must contain J1, J2, and J3")
            publish_readings(readings)
            self.send_json({"published": len(readings)})
        except Exception as error:
            self.send_json({"error": str(error)}, 400)

    def log_message(self, format: str, *args: object) -> None:
        return


def main() -> None:
    server = ThreadingHTTPServer(("0.0.0.0", int(os.getenv("PORT", "8000"))), Handler)
    print("Traffic control UI listening on port 8000", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
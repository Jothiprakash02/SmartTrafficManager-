# Traffic Edge Prototype

For the complete architecture, data flow, technologies, scenarios, testing instructions, deployment process, and limitations, see [PROJECT_DOCUMENTATION.md](PROJECT_DOCUMENTATION.md).

This repository implements the core of the proposed three-junction traffic system:

`Python simulator -> MQTT/Mosquitto -> Node-RED edge analytics -> InfluxDB -> Grafana`

The Python package is the reference implementation for validation, congestion scoring, anomaly detection, propagation detection, and signal recommendations. Node-RED contains the deployable edge-side equivalent for live MQTT messages, and Grafana is provisioned with a starter dashboard.

## Run the tested core

```powershell
python -m pip install -e ".[dev]"
python -m pytest -q
python -m traffic_edge.cli --cycles 3 --scenario congested
```

The simulator supports `normal`, `heavy`, `congested`, and `abnormal` scenarios. Each output record is JSON and includes the current congestion level, score, status, anomalies, and recommendation.

## Run the infrastructure

```powershell
docker compose up -d
```

For a complete Windows startup, use the checked startup script. It validates Docker, validates Compose, builds and starts all six services, checks container state and health, checks the Node-RED, InfluxDB, Grafana, and web endpoints, then opens the control website:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\start-traffic-edge.ps1
```

Stop the stack:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\stop-traffic-edge.ps1
```

The stop script checks Docker, validates Compose, stops all six services, removes orphan containers, and verifies that no project containers remain. It preserves InfluxDB and Grafana data by default. To delete the stored data as well:

```powershell
.\stop-traffic-edge.ps1 -RemoveVolumes
```

Compose builds a small Node-RED image with `node-red-contrib-influxdb`, which is required by the included flow.
It also builds a simulator container that continuously publishes fresh random baseline traffic to J1, J2, and J3 every second. The integrated OPC UA simulator and bridge also run automatically and publish a second input stream to Node-RED. These live streams start automatically and keep the Overview populated. The website feeder is optional and publishes a selected scenario as a one-shot test input; it does not replace the background simulators.

Configure the background stream interval or start it in a fixed scenario without editing files:

```powershell
$env:SCENARIO = "congested"
$env:INTERVAL = "1"
docker compose up --build -d
```

Use `SCENARIO=live` for normal random baseline traffic. The background simulator runs until the stop script or `docker compose down` is used.

Endpoints:

- Traffic control website: http://localhost:8000
- Node-RED: http://localhost:1880
- InfluxDB: http://localhost:8086
- Grafana: http://localhost:3000 (`admin` / `traffic-admin-password`)
- MQTT: `localhost:1883`
- OPC UA simulator: `opc.tcp://localhost:4840/traffic/`

The traffic control website has three tabs. `Overview` shows the latest state of J1, J2, and J3, including congestion score, queue, speed, waiting time, and recommendations. `Feed traffic` provides five demonstration scenarios, editable values for every junction, and a side-by-side decision preview. `Decision view` expands the same traffic-to-analysis-to-decision chain into a dedicated response room.

The five scenarios are:

1. `Normal baseline`: stable operation with no intervention.
2. `Rush-hour surge`: rising demand and downstream queue risk.
3. `Signal incident`: a local J2 intervention case.
4. `Weather slowdown`: corridor-wide speed and waiting-time degradation.
5. `Cascade propagation`: a severe J1 -> J2 -> J3 propagation case.

Compose mounts `node-red/flows-ditto-safe.json` into Node-RED. The flow subscribes to both `traffic/junction/+` and `traffic/opcua/junction/+`, validates both inputs with the same logic, computes congestion, and writes the result to InfluxDB. Ditto updates are disabled by default unless a real Ditto endpoint is configured, so the core stack does not generate DNS errors when Ditto is not deployed.

Grafana loads `grafana/provisioning/dashboards/traffic-edge.json` automatically. It includes congestion score, vehicle count, queue length, and average speed panels for the last hour.

When enabled, the Node-RED flow creates or updates each Ditto thing at `/api/2/things/traffic:<junction_id>` with `attributes` and a `state` feature, using Basic Auth. It also emits non-OK events to `traffic/alerts/<junction_id>` through MQTT and the Node-RED debug panel. Configure a reachable Ditto endpoint before starting Compose:

```powershell
$env:DITTO_ENABLED = "true"
$env:DITTO_URL = "http://host.docker.internal:8080"
$env:DITTO_USER = "ditto"
$env:DITTO_PASSWORD = "ditto"
docker compose up -d
```

Eclipse Ditto is intentionally not bundled into this Compose file because a complete Ditto deployment requires its gateway, connectivity, policies, and MongoDB services. The included adapter works with a local or separately deployed Ditto instance.

## Publish simulator traffic through MQTT

```powershell
python -m pip install -e ".[mqtt]"
python -m traffic_edge.cli --cycles 5 --scenario congested --mqtt
```

## Optional OPC UA source

Install the OPC UA extra and expose the same simulated readings as industrial-style nodes:

```powershell
python -m pip install -e ".[opcua]"
```

The `traffic_edge.opcua_simulator.run_server` coroutine publishes `J1`, `J2`, and `J3` under `opc.tcp://localhost:4840/traffic/`. This is the second ingestion path for an OPC UA-capable gateway; MQTT remains the default live path.

Use `traffic_edge.opcua_bridge.poll_readings` to consume those nodes and pass each yielded `TrafficReading` into `EdgePipeline.process`. The bridge discovers the `traffic-edge` namespace instead of assuming a fixed namespace index.

Initialize the three Ditto twins before sending live updates:

```powershell
traffic-ditto-bootstrap --url http://localhost:8080 --user ditto --password ditto
```

## Architecture phases

1. The Python package and tests establish correct domain behavior without infrastructure.
2. Mosquitto and the optional MQTT publisher provide live ingestion.
3. Node-RED performs edge validation, classification, and persistence.
4. InfluxDB and Grafana provide historical storage and monitoring.
5. Eclipse Ditto can be connected with `DittoClient`: it publishes each `TrafficResult.to_dict()` to a `traffic:<junction_id>` thing feature and reads the current state back through REST. Keeping Ditto behind that adapter avoids coupling the analytics core to a particular twin deployment.

For a production deployment, replace demo credentials and anonymous Mosquitto access with secrets, authentication, and TLS.

# Smart Traffic Junction Monitoring and Congestion Management
## Using an Edge-IoT Architecture

## 1. Abstract

Urban traffic congestion is a growing problem caused by increasing vehicle volume, limited road capacity, inefficient signal management, and the spread of congestion between connected junctions.

This project implements a prototype Edge-IoT traffic monitoring and congestion management system for three interconnected junctions:

```text
J1 ---- J2 ---- J3
```

The system continuously generates simulated traffic data, transfers the data through MQTT, processes it locally using Node-RED, classifies congestion, detects abnormal conditions, identifies possible congestion propagation, stores historical measurements in InfluxDB, and displays operational information through a browser dashboard and Grafana.

The system is designed as a decision-support prototype. It generates signal adjustment recommendations but does not directly control real traffic signals.

---

## 2. Problem Statement

Traditional traffic monitoring solutions often analyze each junction independently. This creates several limitations:

- Congestion can be detected too late.
- Abnormal traffic patterns may be missed.
- Relationships between connected junctions are not considered.
- Centralized analysis can introduce processing delay.
- Historical data may not be available for trend analysis.
- Operators may not receive an actionable recommendation.

For connected junctions, a local traffic problem can quickly become a corridor-wide problem:

```text
J1 congestion
      |
      v
J2 queue growth
      |
      v
J3 downstream congestion
```

The system therefore needs to collect data from multiple junctions, process the readings close to the source, compare junction states, identify propagation, and provide a fast recommendation.

---

## 3. Proposed Solution

The proposed solution is a simulated smart traffic monitoring system based on an Edge-IoT architecture.

The prototype contains:

1. A continuous Python MQTT traffic simulator.
2. MQTT communication through Mosquitto.
3. Node-RED as the edge gateway.
4. Rule-based congestion analysis.
5. Abnormal-pattern detection.
6. Multi-junction propagation analysis.
7. InfluxDB historical storage.
8. Grafana historical and operational visualization.
9. A browser-based operator dashboard.
10. A scenario feeder for controlled demonstrations.
11. Optional Eclipse Ditto integration.
12. Integrated OPC UA simulation and MQTT bridge.
13. Docker Compose deployment.

The normal application starts a continuous live traffic stream automatically. The web feeder is an optional tool for injecting controlled test scenarios.

---

## 4. Project Objectives

The main objectives are:

- Generate realistic traffic readings for three junctions.
- Publish readings continuously through MQTT.
- Process traffic data at the edge with low latency.
- Validate incoming readings before analysis.
- Classify traffic as NORMAL, MODERATE, HIGH, or CRITICAL.
- Detect sudden vehicle increases, slowdowns, and queue growth.
- Analyze congestion propagation between J1, J2, and J3.
- Generate signal adjustment recommendations.
- Store traffic history as time-series data.
- Display live traffic status through a web interface.
- Display historical trends through Grafana.
- Make the entire system reproducible with Docker Compose.

---

## 5. System Architecture

```text
+-----------------------------+
| Continuous Python Simulator |
| J1, J2, J3                  |
+--------------+--------------+
               |
               | MQTT
               v
+-----------------------------+
| Mosquitto MQTT Broker       |
+--------------+--------------+
               |
               | traffic/junction/+
               v
+-----------------------------+
| Node-RED Edge Gateway       |
|                             |
| - JSON parsing              |
| - Data validation           |
| - Congestion scoring        |
| - Anomaly detection        |
| - Propagation analysis     |
| - Recommendation generation|
+---------+----------+--------+
          |          |
          |          +--------------------+
          |                               |
          v                               v
+------------------+             +------------------+
| InfluxDB         |             | MQTT Alerts      |
| Historical data  |             | traffic/alerts/# |
+--------+---------+             +------------------+
         |
         v
+------------------+
| Grafana          |
| Historical charts|
+------------------+

+------------------+
| Browser Web App  |
| Overview         |
| Feed Traffic     |
| Decision View    |
+--------+---------+
         |
         | HTTP API + MQTT publish
         v
+------------------+
| Web Gateway      |
+------------------+

Optional:

+------------------+       +------------------+
| Eclipse Ditto    |       | OPC UA Simulator |
| Digital twins    |       | Industrial input|
+------------------+       +------------------+
```

---

## 6. Technologies Used

| Technology | Purpose |
|---|---|
| Python 3.13 | Traffic simulation and domain analytics |
| paho-mqtt | Python MQTT publishing |
| MQTT | Lightweight traffic-message transport |
| Eclipse Mosquitto | MQTT broker |
| Node-RED | Edge ingestion, validation, routing, and processing |
| JavaScript Function nodes | Node-RED edge logic |
| InfluxDB 2.7 | Time-series traffic storage |
| Flux | InfluxDB query language |
| Grafana | Historical and operational dashboards |
| HTML | Browser dashboard structure |
| CSS | Browser dashboard styling and responsive layout |
| JavaScript | Browser interaction and feeder API calls |
| Docker | Service isolation and reproducible deployment |
| Docker Compose | Multi-service orchestration |
| PowerShell | Windows startup and shutdown automation |
| asyncua | Optional OPC UA support |
| Eclipse Ditto | Optional digital-twin integration |
| cURL | Optional API testing |

---

## 7. Input Data

Each simulated traffic reading contains:

| Field | Purpose |
|---|---|
| `junction_id` | Identifies J1, J2, or J3 |
| `timestamp` | Time at which the reading was generated |
| `vehicle_count` | Number of vehicles detected |
| `avg_speed` | Average speed in km/h |
| `queue_length` | Number of vehicles waiting at the junction |
| `lane_occupancy` | Occupancy percentage from 0 to 100 |
| `waiting_time` | Estimated waiting time in seconds |
| `traffic_flow` | Vehicles per minute |
| `signal_state` | GREEN, YELLOW, or RED |

The current prototype uses `lane_occupancy` as the traffic-density proxy.

Traffic density can later be added as a separate field:

```text
traffic_density = vehicles / road_segment_length
```

Signal cycle time can also be added as a future field:

```text
signal_cycle_time = total signal cycle duration in seconds
```

The current prototype focuses on the core edge-processing behavior and can be extended without changing the MQTT topic structure.

---

## 8. Example MQTT Message

```json
{
  "junction_id": "J1",
  "timestamp": "2026-10-06T10:25:01Z",
  "vehicle_count": 120,
  "avg_speed": 5.0,
  "queue_length": 75,
  "lane_occupancy": 92.0,
  "waiting_time": 180.0,
  "traffic_flow": 35.0,
  "signal_state": "RED"
}
```

MQTT topic:

```text
traffic/junction/J1
```

Other topics:

```text
traffic/junction/J2
traffic/junction/J3
```

---

## 9. Continuous Traffic Simulator

The simulator is implemented in:

```text
src/traffic_edge/simulator.py
```

The simulator supports:

```text
live
normal
heavy
congested
abnormal
```

The `live` mode is the default Compose mode. It generates random baseline readings continuously.

The simulator publishes all three junctions in sequence:

```text
Cycle 1: J1 -> J2 -> J3
Cycle 2: J1 -> J2 -> J3
Cycle 3: J1 -> J2 -> J3
...
```

The container runs with:

```text
python -m traffic_edge.cli --forever --scenario live --mqtt --broker mosquitto --interval 1
```

This means the Overview dashboard receives data without waiting for the user to select a scenario.

---

## 10. MQTT Communication Layer

Mosquitto receives traffic messages and distributes them to subscribers.

Node-RED subscribes to:

```text
traffic/junction/+
```

The wildcard allows Node-RED to receive messages from all junctions.

Alerts are published to:

```text
traffic/alerts/J1
traffic/alerts/J2
traffic/alerts/J3
```

MQTT is appropriate for this prototype because it is:

- Lightweight
- Low overhead
- Suitable for IoT devices
- Publish/subscribe based
- Easy to use across multiple services
- Suitable for intermittent or continuous sensor data

---

## 11. Node-RED Edge Gateway

Node-RED is the main edge-processing component.

The flow is mounted from:

```text
node-red/flows-ditto-safe.json
```

The flow performs the following operations:

```text
MQTT IN
   |
   v
JSON parsing
   |
   v
Validation
   |
   v
Congestion classification
   |
   +--> InfluxDB HTTP write
   |
   +--> Alert generation
   |
   +--> Optional Ditto update
   |
   +--> Node-RED debug output
```

The current flow is Ditto-safe. Ditto is disabled unless explicitly configured, so the main traffic pipeline does not fail when Ditto is unavailable.

---

## 12. Data Validation

The edge gateway rejects invalid values.

Validation rules include:

```text
vehicle_count >= 0
avg_speed >= 0
queue_length >= 0
0 <= lane_occupancy <= 100
waiting_time >= 0
traffic_flow >= 0
signal_state in {GREEN, YELLOW, RED}
```

Example invalid reading:

```json
{
  "junction_id": "J1",
  "vehicle_count": -10
}
```

This reading is rejected before congestion analysis.

---

## 13. Congestion Classification

The prototype uses a rule-based congestion score.

### Speed thresholds

```text
Speed >= 20 km/h : lower congestion contribution
Speed < 20 km/h  : congestion contribution
Speed < 10 km/h  : high congestion contribution
Speed < 5 km/h   : critical congestion contribution
```

### Queue thresholds

```text
Queue >= 20 : moderate contribution
Queue >= 40 : high contribution
Queue >= 60 : critical contribution
```

### Occupancy thresholds

```text
Occupancy >= 50% : moderate contribution
Occupancy >= 70% : high contribution
Occupancy >= 85% : critical contribution
```

### Waiting-time thresholds

```text
Waiting >= 45 seconds  : moderate contribution
Waiting >= 90 seconds  : high contribution
Waiting >= 150 seconds : critical contribution
```

The final score is mapped to:

```text
NORMAL
MODERATE
HIGH
CRITICAL
```

---

## 14. Anomaly Detection

The system compares the current reading with the previous reading for the same junction.

It detects:

### Sudden vehicle-count increase

```text
50 vehicles -> 120 vehicles
```

### Sudden slowdown

```text
40 km/h -> 20 km/h
```

### Rapid queue growth

```text
10 vehicles -> 50 vehicles
```

Anomalies are attached to the processed result and can be sent through alerts.

---

## 15. Congestion Propagation Analysis

The junction topology is:

```text
J1 -> J2 -> J3
```

The edge gateway compares neighboring junction states.

Example:

```text
J1 = CRITICAL
J2 = HIGH
J3 = NORMAL
```

The system reports:

```text
Propagation risk detected from J1
```

A complete cascade scenario looks like:

```text
J1 severe congestion
        |
        v
J2 developing congestion
        |
        v
J3 downstream congestion
```

This is the key feature that differentiates the project from independent junction monitoring.

---

## 16. Recommendations and Alerts

The system generates recommendations instead of directly controlling real signals.

### Normal

```text
Monitor current signal plan.
```

### High

```text
Prepare additional green time.
```

### Critical

```text
Increase green duration.
```

This design is safer for a prototype because it supports operator decision-making without connecting to real signal controllers.

---

## 17. Browser Application

The browser application runs at:

```text
http://localhost:8000
```

### Overview tab

Shows:

- Live J1, J2, and J3 status
- Congestion score
- Queue length
- Average speed
- Waiting time
- Recommendations
- Network status
- Corridor condition chart
- Edge intelligence panel

### Feed Traffic tab

Provides five controlled simulation scenarios:

1. Normal baseline
2. Rush-hour surge
3. Signal incident
4. Weather slowdown
5. Cascade propagation

Each scenario contains different values for J1, J2, and J3.

The user can also edit:

- Vehicle count
- Speed
- Queue length
- Occupancy
- Waiting time
- Traffic flow
- Signal state

The feeder publishes all three readings to MQTT with one button.

### Decision View tab

Displays:

```text
Traffic feed -> Edge analysis -> Decision
```

It shows:

- Expected outcome
- Alert level
- Propagation risk
- Recommended response plan

---

## 18. Five Test Scenarios

### Scenario 1: Normal Baseline

Purpose:

- Verify stable operation
- Demonstrate normal traffic
- Confirm no intervention is required

Different junction profiles:

```text
J1: 32 vehicles, speed 44, queue 8
J2: 48 vehicles, speed 39, queue 16
J3: 25 vehicles, speed 46, queue 6
```

Expected result:

```text
NORMAL
No signal adjustment required
```

### Scenario 2: Rush-Hour Surge

Purpose:

- Demonstrate increasing demand
- Show a queue forming near J1
- Test early warning behavior

Profiles:

```text
J1: 135 vehicles, speed 16, queue 58
J2: 96 vehicles, speed 22, queue 38
J3: 61 vehicles, speed 29, queue 22
```

Expected result:

```text
Demand building
J1 -> J2 watch condition
```

### Scenario 3: Signal Incident

Purpose:

- Simulate a local J2 signal problem
- Demonstrate junction-specific intervention

Profiles:

```text
J1: moderate or normal
J2: speed 4, queue 62, occupancy 86%
J3: moderate downstream condition
```

Expected result:

```text
CRITICAL at J2
Local intervention required
```

### Scenario 4: Weather Slowdown

Purpose:

- Simulate rain, fog, or poor visibility
- Reduce speed across the corridor
- Increase waiting time without an immediate vehicle spike

Profiles:

```text
J1: speed 18, queue 28, wait 88
J2: speed 12, queue 43, wait 126
J3: speed 16, queue 34, wait 102
```

Expected result:

```text
Network caution
Continue monitoring
```

### Scenario 5: Cascade Propagation

Purpose:

- Demonstrate connected-junction propagation
- Test the strongest decision-support behavior

Profiles:

```text
J1: 180 vehicles, speed 4, queue 96
J2: 132 vehicles, speed 8, queue 71
J3: 94 vehicles, speed 13, queue 49
```

Expected result:

```text
J1 -> J2 -> J3
Propagation detected
Protect downstream capacity
Increase green time upstream
```

---

## 19. InfluxDB and Grafana

InfluxDB is available at:

```text
http://localhost:8086
```

Grafana is available at:

```text
http://localhost:3000
```

Grafana credentials:

```text
Username: admin
Password: traffic-admin-password
```

Grafana panels include:

- Congestion score by junction
- Vehicle count
- Queue length
- Average speed
- Waiting time
- Latest recommendations

The data is retained as time-series data for trend analysis.

---

## 20. Docker Services

The Compose application contains:

| Service | Responsibility |
|---|---|
| `mosquitto` | MQTT broker |
| `simulator` | Continuous background traffic source |
| `opcua-simulator` | Continuous OPC UA J1/J2/J3 node source |
| `opcua-bridge` | Reads OPC UA nodes and publishes normalized MQTT readings |
| `web` | Browser dashboard and feeder API |
| `nodered` | Edge processing and alerting |
| `influxdb` | Historical time-series storage |
| `grafana` | Dashboard visualization |

Start the complete application:

```powershell
.\start-traffic-edge.ps1
```

The startup script:

1. Checks Docker.
2. Validates Compose.
3. Builds the images.
4. Starts all services.
5. Waits for service readiness.
6. Checks container state.
7. Checks web endpoints.
8. Opens the website.

Stop the application:

```powershell
.\stop-traffic-edge.ps1
```

Remove stored InfluxDB and Grafana data:

```powershell
.\stop-traffic-edge.ps1 -RemoveVolumes
```

---

## 21. Testing Commands

Run the Python tests:

```powershell
python -m pytest -q
```

Run a local normal simulation:

```powershell
python -m traffic_edge.cli --cycles 3 --scenario normal
```

Run a local congested simulation:

```powershell
python -m traffic_edge.cli --cycles 3 --scenario congested
```

Run a continuous MQTT stream manually:

```powershell
python -m traffic_edge.cli --forever --scenario live --mqtt --broker localhost --interval 1
```

Subscribe to MQTT traffic:

```powershell
docker compose exec mosquitto mosquitto_sub -h localhost -t "traffic/#"
```

Check Docker services:

```powershell
docker compose ps
```

Check Node-RED logs:

```powershell
docker compose logs -f nodered
```

---

## 22. Optional Eclipse Ditto

Eclipse Ditto is not required for the core application and is disabled by default.

The default working architecture is:

```text
Simulator -> MQTT -> Node-RED -> InfluxDB -> Grafana -> Web Dashboard
```

If Ditto is deployed separately, enable it with:

```powershell
$env:DITTO_ENABLED = "true"
$env:DITTO_URL = "http://host.docker.internal:8080"
$env:DITTO_USER = "ditto"
$env:DITTO_PASSWORD = "ditto"

docker compose up -d --force-recreate nodered
```

Ditto can represent:

```text
traffic:J1
traffic:J2
traffic:J3
```

The Ditto integration is an optional extension and is not needed for MQTT, Node-RED, InfluxDB, Grafana, or the web application.

---

## 23. Optional OPC UA

The project includes an integrated OPC UA path:

```text
traffic_edge.opcua_simulator
traffic_edge.opcua_bridge
```

The Compose deployment starts two OPC UA services automatically:

```text
opcua-simulator -> opc.tcp://localhost:4840/traffic/
opcua-bridge -> traffic/opcua/junction/+ -> Node-RED
```

The bridge publishes to a separate topic so OPC UA data can be distinguished from the native MQTT simulator while still using the same Node-RED analytics logic.

For local Python use, install the dependency:

```powershell
python -m pip install -e ".[opcua]"
```

OPC UA provides an alternative industrial-style input path:

```text
OPC UA Simulator
        |
        v
OPC UA Bridge
        |
        v
TrafficReading
        |
        v
EdgePipeline
```

The MQTT and OPC UA paths can ultimately feed the same analytics pipeline.

---

## 24. Complete End-to-End Data Flow

```text
1. The startup script launches Docker Compose.
2. Mosquitto starts and accepts MQTT connections.
3. The continuous simulator starts in live mode.
4. The simulator generates random readings for J1, J2, and J3.
5. Each reading is published to traffic/junction/<junction_id>.
6. Mosquitto distributes the message to Node-RED.
7. Node-RED validates the reading.
8. Node-RED calculates the congestion score.
9. Node-RED classifies the traffic condition.
10. Node-RED checks for sudden anomalies.
11. Node-RED compares connected junction states.
12. Node-RED detects possible propagation.
13. Node-RED generates a recommendation.
14. Node-RED writes numeric values to InfluxDB.
15. Node-RED publishes high and critical alerts.
16. The web API reads recent InfluxDB values.
17. The browser dashboard displays live junction cards.
18. Grafana displays historical time-series charts.
19. The user can open Feed Traffic for a controlled scenario.
20. The feeder publishes distinct readings for J1, J2, and J3.
21. Node-RED processes the injected scenario.
22. The Overview and Decision View update with the result.
23. The stop script shuts down all services when testing is complete.
```

---

## 25. Limitations and Future Enhancements

Current prototype limitations:

- Traffic sensors are simulated.
- Signal cycle time is not yet a separate input field.
- Traffic density is represented by lane occupancy.
- Signal recommendations are not connected to real controllers.
- Eclipse Ditto is optional and external.
- The default MQTT broker configuration is intended for local demonstrations.
- Authentication and TLS should be strengthened for production.

Possible future enhancements:

- Add separate traffic-density calculation.
- Add signal cycle-time and phase-duration fields.
- Add lane-level traffic readings.
- Add real OPC UA hardware input.
- Add authentication and TLS to Mosquitto.
- Add Grafana alert rules.
- Add operator acknowledgement of alerts.
- Add a traffic topology editor.
- Add machine-learning prediction models.
- Add a real digital-twin deployment with Eclipse Ditto.
- Add role-based access to the web dashboard.

---

## 26. Final Result

The completed prototype provides a complete Edge-IoT traffic monitoring workflow:

```text
Continuous simulated traffic
        |
        v
MQTT communication
        |
        v
Local edge validation and analysis
        |
        v
Congestion and anomaly detection
        |
        v
Propagation analysis
        |
        v
Alerts and recommendations
        |
        +--> InfluxDB historical data
        +--> Grafana dashboard
        +--> Browser operations dashboard
        +--> Optional Eclipse Ditto twins
```

The system demonstrates how traffic data from multiple connected junctions can be collected, processed locally, analyzed collectively, stored historically, visualized operationally, and tested through controlled traffic scenarios.

const scenarios = {
  normal: { title: 'Normal baseline', copy: 'Balanced traffic across the network.', outcome: 'Normal operation', outcomeCopy: 'The corridor can keep its current signal plan.', propagation: 'None detected', alert: 'OK', values: { vehicle_count: 35, avg_speed: 42, queue_length: 12, lane_occupancy: 35, waiting_time: 20, traffic_flow: 48, signal_state: 'GREEN' } },
  rush: { title: 'Rush-hour surge', copy: 'Demand rises at J1 and forms a manageable downstream queue.', outcome: 'Demand building', outcomeCopy: 'Watch J1 and prepare additional green time before the queue spreads.', propagation: 'J1 -> J2 | watch', alert: 'WARNING', values: { vehicle_count: 105, avg_speed: 19, queue_length: 44, lane_occupancy: 72, waiting_time: 92, traffic_flow: 70, signal_state: 'RED' } },
  incident: { title: 'Signal incident', copy: 'J2 is slow despite a full approach, simulating a blocked signal phase.', outcome: 'Local intervention', outcomeCopy: 'Prioritize J2 and recommend a corrective green phase.', propagation: 'J2 | local', alert: 'CRITICAL', values: { vehicle_count: 76, avg_speed: 4, queue_length: 62, lane_occupancy: 86, waiting_time: 170, traffic_flow: 12, signal_state: 'RED' } },
  weather: { title: 'Weather slowdown', copy: 'Lower speeds and longer waits affect all junctions without a sudden queue spike.', outcome: 'Network caution', outcomeCopy: 'Keep monitoring conditions and use measured signal adjustments.', propagation: 'Corridor-wide | low', alert: 'WARNING', values: { vehicle_count: 68, avg_speed: 15, queue_length: 35, lane_occupancy: 58, waiting_time: 105, traffic_flow: 38, signal_state: 'YELLOW' } },
  cascade: { title: 'Cascade propagation', copy: 'A severe J1 event flows through J2 toward J3.', outcome: 'Propagation detected', outcomeCopy: 'Protect downstream capacity while increasing green time upstream.', propagation: 'J1 -> J2 -> J3', alert: 'CRITICAL', values: { vehicle_count: 145, avg_speed: 6, queue_length: 84, lane_occupancy: 94, waiting_time: 210, traffic_flow: 25, signal_state: 'RED' } }
};
let currentStatus = [];
let selectedScenario = 'normal';
const scenarioReadings = {
  normal: {
    J1: { vehicle_count: 32, avg_speed: 44, queue_length: 8, lane_occupancy: 28, waiting_time: 15, traffic_flow: 46, signal_state: 'GREEN' },
    J2: { vehicle_count: 48, avg_speed: 39, queue_length: 16, lane_occupancy: 42, waiting_time: 28, traffic_flow: 52, signal_state: 'GREEN' },
    J3: { vehicle_count: 25, avg_speed: 46, queue_length: 6, lane_occupancy: 24, waiting_time: 12, traffic_flow: 43, signal_state: 'GREEN' }
  },
  rush: {
    J1: { vehicle_count: 135, avg_speed: 16, queue_length: 58, lane_occupancy: 82, waiting_time: 118, traffic_flow: 78, signal_state: 'RED' },
    J2: { vehicle_count: 96, avg_speed: 22, queue_length: 38, lane_occupancy: 68, waiting_time: 76, traffic_flow: 65, signal_state: 'YELLOW' },
    J3: { vehicle_count: 61, avg_speed: 29, queue_length: 22, lane_occupancy: 51, waiting_time: 48, traffic_flow: 57, signal_state: 'GREEN' }
  },
  incident: {
    J1: { vehicle_count: 58, avg_speed: 31, queue_length: 20, lane_occupancy: 48, waiting_time: 42, traffic_flow: 40, signal_state: 'GREEN' },
    J2: { vehicle_count: 76, avg_speed: 4, queue_length: 62, lane_occupancy: 86, waiting_time: 170, traffic_flow: 12, signal_state: 'RED' },
    J3: { vehicle_count: 44, avg_speed: 27, queue_length: 28, lane_occupancy: 55, waiting_time: 65, traffic_flow: 36, signal_state: 'YELLOW' }
  },
  weather: {
    J1: { vehicle_count: 58, avg_speed: 18, queue_length: 28, lane_occupancy: 52, waiting_time: 88, traffic_flow: 35, signal_state: 'YELLOW' },
    J2: { vehicle_count: 81, avg_speed: 12, queue_length: 43, lane_occupancy: 64, waiting_time: 126, traffic_flow: 41, signal_state: 'YELLOW' },
    J3: { vehicle_count: 65, avg_speed: 16, queue_length: 34, lane_occupancy: 58, waiting_time: 102, traffic_flow: 38, signal_state: 'GREEN' }
  },
  cascade: {
    J1: { vehicle_count: 180, avg_speed: 4, queue_length: 96, lane_occupancy: 98, waiting_time: 260, traffic_flow: 19, signal_state: 'RED' },
    J2: { vehicle_count: 132, avg_speed: 8, queue_length: 71, lane_occupancy: 88, waiting_time: 190, traffic_flow: 27, signal_state: 'RED' },
    J3: { vehicle_count: 94, avg_speed: 13, queue_length: 49, lane_occupancy: 73, waiting_time: 132, traffic_flow: 34, signal_state: 'YELLOW' }
  }
};
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];

function showView(view) {
  $$('.view').forEach(element => element.classList.toggle('active-view', element.id === view));
  $$('.nav-item').forEach(element => element.classList.toggle('active', element.dataset.view === view));
  $('#page-title').textContent = view === 'feed' ? 'Feed traffic' : view === 'decision' ? 'Decision view' : 'Network overview';
}

function card(junction) {
  const level = (junction.congestion || junction.status || 'OFFLINE').toLowerCase();
  return `<article class="junction-card"><div class="card-head"><h3>${junction.junction_id}</h3><span class="status status-${level}">${junction.congestion || junction.status || 'OFFLINE'}</span></div><div class="score"><strong>${junction.congestion_score ?? '-'}</strong><span>congestion score</span></div><div class="stats"><div><span>Queue</span><strong>${junction.queue_length ?? '-'}</strong></div><div><span>Speed</span><strong>${junction.avg_speed ?? '-'} <small>km/h</small></strong></div><div><span>Wait</span><strong>${junction.waiting_time ?? '-'} <small>sec</small></strong></div></div><div class="recommendation">${junction.recommendation || 'No recommendation available yet.'}</div></article>`;
}

function renderStatus() {
  const active = currentStatus.filter(junction => junction.status !== 'OFFLINE');
  $('#junction-grid').innerHTML = currentStatus.map(card).join('');
  $('#network-status').textContent = active.length === 3 ? 'OPERATIONAL' : 'PARTIAL SIGNAL';
  const critical = currentStatus.find(junction => junction.congestion === 'CRITICAL' || junction.status === 'CRITICAL');
  $('#last-decision').textContent = critical ? `${critical.junction_id} · CRITICAL` : 'Stable corridor';
  $('#last-update').textContent = `Updated ${new Date().toLocaleTimeString()}`;
  $('#bar-chart').innerHTML = currentStatus.map(junction => `<div class="bar-wrap"><div class="bar" style="height:${Math.min(100, Number(junction.congestion_score || 0) * 9)}%" title="${junction.congestion_score || 0}"></div><span class="bar-label">${junction.junction_id}</span></div>`).join('');
  $('#recommendations').innerHTML = currentStatus.map(junction => `<div class="rec"><strong>${junction.junction_id} · ${junction.congestion || junction.status || 'OFFLINE'}</strong>${junction.recommendation || 'Waiting for telemetry.'}</div>`).join('');
}

async function refresh() {
  try {
    const response = await fetch('/api/status');
    currentStatus = (await response.json()).junctions;
    renderStatus();
  } catch (error) {
    $('#last-update').textContent = 'Gateway unavailable';
  }
}

function routeMarkup(key) {
  const scenario = scenarios[key];
  const readings = scenarioReadings[key];
  const danger = scenario.alert === 'CRITICAL';
  const totalVehicles = Object.values(readings).reduce((total, reading) => total + reading.vehicle_count, 0);
  const highestQueue = Math.max(...Object.values(readings).map(reading => reading.queue_length));
  const score = Math.round(highestQueue / 10);
  return `<div class="route-line"><div class="route-node"><span class="route-dot source"></span><strong>Traffic feed</strong><small>${totalVehicles} vehicles / 3 junctions</small></div><span class="route-arrow">→</span><div class="route-node"><span class="route-dot ${danger ? 'danger' : 'active'}"></span><strong>Edge analysis</strong><small>${scenario.alert} · queue ${highestQueue}</small></div><span class="route-arrow">→</span><div class="route-node"><span class="route-dot ${danger ? 'danger' : 'active'}"></span><strong>Decision</strong><small>${scenario.outcome}</small></div></div>`;
}

function updateDecision() {
  const scenario = scenarios[selectedScenario];
  $('#decision-route').innerHTML = routeMarkup(selectedScenario);
  $('#room-route').innerHTML = routeMarkup(selectedScenario);
  $('#preview-outcome').textContent = scenario.outcome;
  $('#preview-copy').textContent = scenario.outcomeCopy;
  $('#preview-propagation').textContent = scenario.propagation;
  $('#preview-alert').textContent = scenario.alert;
  $('#preview-status').textContent = scenario.alert === 'OK' ? 'READY' : 'REVIEW';
  $('#room-outcome').textContent = scenario.outcome;
  $('#room-copy').textContent = scenario.outcomeCopy;
  $('#room-actions').innerHTML = ['Validate incoming readings', `Classify congestion as ${scenario.alert}`, `Monitor ${scenario.propagation}`, 'Publish recommendation to the operator'].map(action => `<div class="rec"><strong>${action}</strong>Ready for this demonstration scenario.</div>`).join('');
}

function renderFeed() {
  $('#feed-grid').innerHTML = ['J1', 'J2', 'J3'].map(id => { const values = scenarioReadings[selectedScenario][id]; return `<article class="feed-card"><div class="feed-card-head"><h3>${id}</h3><span class="junction-tag">SIMULATED</span></div><div class="field-grid">${[['vehicle_count', 'Vehicles'], ['avg_speed', 'Speed (km/h)'], ['queue_length', 'Queue'], ['lane_occupancy', 'Occupancy (%)'], ['waiting_time', 'Wait (sec)'], ['traffic_flow', 'Flow / min']].map(([key, label]) => `<div class="field"><label>${label}</label><input data-junction="${id}" data-field="${key}" type="number" value="${values[key]}" min="0"></div>`).join('')}<div class="field"><label>Signal state</label><select data-junction="${id}" data-field="signal_state"><option ${values.signal_state === 'GREEN' ? 'selected' : ''}>GREEN</option><option ${values.signal_state === 'YELLOW' ? 'selected' : ''}>YELLOW</option><option ${values.signal_state === 'RED' ? 'selected' : ''}>RED</option></select></div></div></article>`; }).join('');
  updateDecision();
}

$('#scenario').addEventListener('change', () => {
  selectedScenario = $('#scenario').value;
  const scenario = scenarios[selectedScenario];
  $('#scenario-title').textContent = scenario.title;
  $('#scenario-copy').textContent = scenario.copy;
  renderFeed();
});

$('#apply-scenario').addEventListener('click', async () => {
  const readings = ['J1', 'J2', 'J3'].map(id => {
    const reading = { junction_id: id, timestamp: new Date().toISOString() };
    $$(`[data-junction="${id}"]`).forEach(input => { reading[input.dataset.field] = input.type === 'number' ? Number(input.value) : input.value; });
    return reading;
  });
  $('#feed-result').textContent = 'Publishing to the edge gateway...';
  try {
    const response = await fetch('/api/feed', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ readings }) });
    const result = await response.json();
    $('#feed-result').textContent = response.ok ? `Published ${result.published} readings. Open Overview to watch the decision update.` : `Publish failed: ${result.error}`;
  } catch (error) {
    $('#feed-result').textContent = 'Gateway unavailable.';
  }
});

$$('.nav-item').forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
$$('[data-view-target]').forEach(button => button.addEventListener('click', () => showView(button.dataset.viewTarget)));
renderFeed();
refresh();
setInterval(refresh, 5000);

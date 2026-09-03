/**
 * PyVRP Web Visualizer Application Logic - Fully Bulletproof Drag and Drop Relocation
 */

document.addEventListener('DOMContentLoaded', () => {
  // State variables
  let currentProblem = null;
  let currentSolution = null;
  let map = null;
  let mapLayers = [];
  let ganttChart = null;
  let convergenceChart = null;
  let dragDebounceTimer = null;
  let polylineClickTimer = null;
  let selectedRouteId = null; // null = all routes overview
  let activeEditingRouteId = null;
  let lastDClickLatLng = null;

  // In-memory OSRM road geometry cache for instant rendering
  const osrmCache = new Map();

  // Route colors palette
  const ROUTE_COLORS = [
    '#3b82f6', // Blue
    '#10b981', // Green
    '#f59e0b', // Amber
    '#ec4899', // Pink
    '#8b5cf6', // Purple
    '#06b6d4', // Cyan
    '#f97316', // Orange
    '#14b8a6', // Teal
  ];

  // Format time into 12-hour AM/PM format (hh:mm AM/PM)
  function formatTime12h(totalSeconds) {
    if (totalSeconds === null || totalSeconds === undefined || isNaN(totalSeconds)) return '-';
    let secs = parseInt(totalSeconds, 10);
    if (secs < 0) secs = 0;

    let hours = Math.floor(secs / 3600);
    let mins = Math.floor((secs % 3600) / 60);

    let startHourOffset = 8;
    hours = (hours + startHourOffset) % 24;

    const ampm = hours >= 12 ? 'PM' : 'AM';
    let h12 = hours % 12;
    if (h12 === 0) h12 = 12;

    const hStr = h12 < 10 ? '0' + h12 : '' + h12;
    const mStr = mins < 10 ? '0' + mins : '' + mins;

    return `${hStr}:${mStr} ${ampm}`;
  }

  // Initialize App
  initMap();
  initEventListeners();
  loadDataset('ne_india_real');

  // Initialize Leaflet Map
  function initMap() {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;

    map = L.map('map', {
      zoomControl: true,
      attributionControl: true,
      doubleClickZoom: false, // Enable double-click route location adding
    }).setView([26.1445, 91.7362], 7);

    // Standard OpenStreetMap tiles
    const osmLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap contributors',
    });

    osmLayer.addTo(map);

    // Map Double-Click Event Handler
    map.on('dblclick', (e) => {
      openDClickModal(e.latlng);
    });

    setTimeout(() => {
      if (map) map.invalidateSize();
    }, 150);
  }

  // Event Listeners Setup
  function initEventListeners() {
    // Dataset select change
    document.getElementById('dataset-select').addEventListener('change', (e) => {
      selectedRouteId = null;
      loadDataset(e.target.value);
    });

    // Run Optimizer Button
    document.getElementById('btn-solve').addEventListener('click', runOptimizer);

    // Recenter map button
    document.getElementById('btn-fit-map').addEventListener('click', fitMapBounds);

    // KPI Filter Card Reset
    document.getElementById('kpi-filter-card').addEventListener('click', () => {
      selectedRouteId = null;
      updateKPIDashboard();
      highlightSelectedRouteCard();
    });

    // Tab buttons switching
    document.querySelectorAll('.tab-btn').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const tabTarget = e.currentTarget.getAttribute('data-tab');
        document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach((p) => p.classList.remove('active'));

        e.currentTarget.classList.add('active');
        document.getElementById(tabTarget).classList.add('active');

        if (tabTarget === 'tab-locations') renderLocationsTable();
        if (tabTarget === 'tab-gantt' && ganttChart) ganttChart.update();
        if (tabTarget === 'tab-convergence' && convergenceChart) convergenceChart.update();
      });
    });

    // JSON Editor buttons
    document.getElementById('btn-format-json').addEventListener('click', () => {
      try {
        const editor = document.getElementById('json-input-editor');
        const parsed = JSON.parse(editor.value);
        editor.value = JSON.stringify(parsed, null, 2);
      } catch (err) {
        alert('Invalid JSON format: ' + err.message);
      }
    });

    document.getElementById('btn-apply-json').addEventListener('click', () => {
      try {
        const editor = document.getElementById('json-input-editor');
        currentProblem = JSON.parse(editor.value);
        runOptimizer();
      } catch (err) {
        alert('Invalid JSON specification: ' + err.message);
      }
    });

    // Locations Editor & Modal Triggers
    const locModal = document.getElementById('add-location-modal');
    document.getElementById('btn-add-location').addEventListener('click', () => {
      document.getElementById('new-loc-name').value = '';
      locModal.classList.remove('hidden');
    });

    document.getElementById('btn-close-loc-modal').addEventListener('click', () => locModal.classList.add('hidden'));
    document.getElementById('btn-cancel-loc').addEventListener('click', () => locModal.classList.add('hidden'));

    document.getElementById('btn-geocode-add').addEventListener('click', geocodeAndAddCustomer);

    document.getElementById('btn-save-locations').addEventListener('click', () => {
      saveLocationsFromTable();
      runOptimizer();
    });

    // Route Actions & Client Editor Modal Handlers
    const routeModal = document.getElementById('route-edit-modal');
    document.getElementById('btn-close-route-modal').addEventListener('click', () => routeModal.classList.add('hidden'));
    document.getElementById('btn-cancel-route-modal').addEventListener('click', () => routeModal.classList.add('hidden'));

    document.getElementById('btn-route-add-cust').addEventListener('click', () => {
      routeModal.classList.add('hidden');
      document.getElementById('new-loc-name').value = '';
      locModal.classList.remove('hidden');
    });

    document.getElementById('btn-route-focus-kpi').addEventListener('click', () => {
      selectedRouteId = activeEditingRouteId;
      updateKPIDashboard();
      highlightSelectedRouteCard();
      routeModal.classList.add('hidden');
    });

    document.getElementById('btn-save-route-clients').addEventListener('click', () => {
      saveRouteClientsFromModal();
      routeModal.classList.add('hidden');
      runOptimizer();
    });

    // Double-Click Modal Handlers
    const dclickModal = document.getElementById('dclick-modal');
    document.getElementById('btn-close-dclick-modal').addEventListener('click', () => dclickModal.classList.add('hidden'));
    document.getElementById('btn-cancel-dclick').addEventListener('click', () => dclickModal.classList.add('hidden'));

    document.getElementById('dclick-loc-type').addEventListener('change', (e) => {
      const demandGroup = document.getElementById('dclick-demand-group');
      if (e.target.value === 'depot') {
        demandGroup.style.display = 'none';
      } else {
        demandGroup.style.display = 'flex';
      }
    });

    document.getElementById('btn-confirm-dclick-add').addEventListener('click', confirmDClickLocationAdd);

    // Random Modal toggles
    const modal = document.getElementById('random-modal');
    document.getElementById('btn-random-modal').addEventListener('click', () => modal.classList.remove('hidden'));
    document.getElementById('btn-close-modal').addEventListener('click', () => modal.classList.add('hidden'));
    document.getElementById('btn-cancel-random').addEventListener('click', () => modal.classList.add('hidden'));

    document.getElementById('btn-generate-random').addEventListener('click', generateRandomInstance);
  }

  // Handle Route Click (Focus KPI + Allow Edit Client & Add Client)
  function handleRouteClick(routeId) {
    selectedRouteId = routeId;
    updateKPIDashboard();
    highlightSelectedRouteCard();
    openRouteModal(routeId);
  }

  // Open Route Actions & Client Editor Modal
  function openRouteModal(routeId) {
    if (!currentSolution || !currentProblem) return;
    const r = currentSolution.routes.find((route) => route.route_id === routeId);
    if (!r) return;

    activeEditingRouteId = routeId;
    document.getElementById('route-modal-title').innerHTML = `<i class="fa-solid fa-route"></i> Route #${r.route_id} (${r.vehicle_type_name}) Management`;

    const container = document.getElementById('route-clients-table-container');
    const routeClientActs = r.activities.filter((act) => act.activity_type !== 'DEPOT');

    if (routeClientActs.length === 0) {
      container.innerHTML = `<div class="empty-state"><p>No customer stops assigned to this route.</p></div>`;
    } else {
      let rowsHtml = '';
      routeClientActs.forEach((act) => {
        const clientMatch = currentProblem.clients.find(
          (c) => c.id === act.location_id || c.name === act.location_name || (Math.abs(c.x - act.x) < 0.001 && Math.abs(c.y - act.y) < 0.001)
        );
        const cId = clientMatch ? clientMatch.id : act.location_id;
        const cName = clientMatch ? clientMatch.name : act.location_name;
        const cLat = clientMatch ? clientMatch.y : act.y;
        const cLng = clientMatch ? clientMatch.x : act.x;
        const cDel = clientMatch ? clientMatch.delivery : 15;
        const cTwe = clientMatch ? clientMatch.tw_early : 0;
        const cTwl = clientMatch ? clientMatch.tw_late : 86400;

        rowsHtml += `
          <tr data-client-id="${cId}">
            <td><strong>#${act.sequence_index}</strong> (${cId})</td>
            <td><input type="text" class="form-input route-cname-input" value="${cName}"></td>
            <td><input type="number" step="0.0001" class="form-input number-input route-clat-input" value="${cLat}"></td>
            <td><input type="number" step="0.0001" class="form-input number-input route-clng-input" value="${cLng}"></td>
            <td><input type="number" class="form-input number-input route-cdel-input" value="${cDel}"></td>
            <td><input type="number" class="form-input number-input route-ctwe-input" value="${cTwe}"></td>
            <td><input type="number" class="form-input number-input route-ctwl-input" value="${cTwl}"></td>
            <td><button class="btn btn-sm btn-danger btn-del-route-client" data-client-id="${cId}"><i class="fa-solid fa-trash"></i></button></td>
          </tr>
        `;
      });

      container.innerHTML = `
        <table class="route-stops-table">
          <thead>
            <tr>
              <th>Seq (ID)</th>
              <th>Location Name</th>
              <th>Latitude</th>
              <th>Longitude</th>
              <th>Demand</th>
              <th>TW Early</th>
              <th>TW Late</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>${rowsHtml}</tbody>
        </table>
      `;

      container.querySelectorAll('.btn-del-route-client').forEach((btn) => {
        btn.addEventListener('click', (e) => {
          const clientId = e.currentTarget.getAttribute('data-client-id');
          currentProblem.clients = currentProblem.clients.filter((c) => c.id !== clientId);
          openRouteModal(routeId);
        });
      });
    }

    document.getElementById('route-edit-modal').classList.remove('hidden');
  }

  // Save Route Clients from Modal Table
  function saveRouteClientsFromModal() {
    const container = document.getElementById('route-clients-table-container');
    if (!currentProblem || !container) return;

    const rows = container.querySelectorAll('tbody tr');
    rows.forEach((tr) => {
      const clientId = tr.getAttribute('data-client-id');
      const clientMatch = currentProblem.clients.find((c) => c.id === clientId);
      if (clientMatch) {
        clientMatch.name = tr.querySelector('.route-cname-input').value;
        clientMatch.y = parseFloat(tr.querySelector('.route-clat-input').value) || 0;
        clientMatch.x = parseFloat(tr.querySelector('.route-clng-input').value) || 0;
        clientMatch.delivery = parseInt(tr.querySelector('.route-cdel-input').value, 10) || 0;
        clientMatch.tw_early = parseInt(tr.querySelector('.route-ctwe-input').value, 10) || 0;
        clientMatch.tw_late = parseInt(tr.querySelector('.route-ctwl-input').value, 10) || 86400;
      }
    });

    document.getElementById('json-input-editor').value = JSON.stringify(currentProblem, null, 2);
  }

  // Open Modal on Route / Map Double-Click
  async function openDClickModal(latlng) {
    lastDClickLatLng = latlng;
    const lat = parseFloat(latlng.lat.toFixed(4));
    const lng = parseFloat(latlng.lng.toFixed(4));

    document.getElementById('dclick-coords-display').value = `Latitude: ${lat}, Longitude: ${lng}`;
    document.getElementById('dclick-loc-name').value = `Stop @ (${lat}, ${lng})`;
    document.getElementById('dclick-loc-type').value = 'client';
    document.getElementById('dclick-demand-group').style.display = 'flex';
    document.getElementById('dclick-modal').classList.remove('hidden');

    try {
      const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`, {
        headers: { 'User-Agent': 'PyVRP-App/1.0' },
      });
      if (res.ok) {
        const data = await res.json();
        if (data && data.display_name) {
          const placeName = data.display_name.split(',')[0] || data.display_name;
          document.getElementById('dclick-loc-name').value = placeName;
        }
      }
    } catch (e) {
      // Ignore reverse geocoding fallback
    }
  }

  // Confirm Double-Click Location Addition
  function confirmDClickLocationAdd() {
    if (!lastDClickLatLng || !currentProblem) return;

    const lat = parseFloat(lastDClickLatLng.lat.toFixed(4));
    const lng = parseFloat(lastDClickLatLng.lng.toFixed(4));

    const locType = document.getElementById('dclick-loc-type').value;
    const nameInput = document.getElementById('dclick-loc-name').value.trim() || `Stop @ (${lat}, ${lng})`;
    const demand = parseInt(document.getElementById('dclick-loc-demand').value, 10) || 20;
    const twe = parseInt(document.getElementById('dclick-loc-twe').value, 10) || 3600;
    const twl = parseInt(document.getElementById('dclick-loc-twl').value, 10) || 32400;

    if (locType === 'depot') {
      const newDepotId = `depot_${currentProblem.depots.length + 1}`;
      currentProblem.depots.push({
        id: newDepotId,
        x: lng,
        y: lat,
        name: nameInput,
        tw_early: twe,
        tw_late: twl,
        service_duration: 0,
      });
    } else {
      const newClientId = `c${currentProblem.clients.length + 1}`;
      currentProblem.clients.push({
        id: newClientId,
        x: lng,
        y: lat,
        name: nameInput,
        delivery: demand,
        pickup: 0,
        service_duration: 1200,
        tw_early: twe,
        tw_late: twl,
        required: true,
      });
    }

    document.getElementById('json-input-editor').value = JSON.stringify(currentProblem, null, 2);
    document.getElementById('dclick-modal').classList.add('hidden');

    runOptimizer();
  }

  // Geocode Location Name & Add to VRP Model
  async function geocodeAndAddCustomer() {
    const locName = document.getElementById('new-loc-name').value.trim();
    if (!locName) {
      alert('Please enter a city or location name.');
      return;
    }

    const demand = parseInt(document.getElementById('new-loc-demand').value, 10) || 20;
    const twe = parseInt(document.getElementById('new-loc-twe').value, 10) || 3600;
    const twl = parseInt(document.getElementById('new-loc-twl').value, 10) || 32400;

    const btnGeocode = document.getElementById('btn-geocode-add');
    btnGeocode.disabled = true;
    btnGeocode.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Geocoding...';

    try {
      const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(locName)}`;
      const res = await fetch(url, { headers: { 'User-Agent': 'PyVRP-App/1.0' } });
      if (!res.ok) throw new Error('Geocoding request failed');
      const data = await res.json();

      if (!data || data.length === 0) {
        throw new Error(`Location "${locName}" could not be geocoded. Please try a different city name.`);
      }

      const match = data[0];
      const lat = parseFloat(parseFloat(match.lat).toFixed(4));
      const lon = parseFloat(parseFloat(match.lon).toFixed(4));
      const displayName = match.display_name.split(',')[0] || locName;

      const newId = `c${currentProblem.clients.length + 1}`;
      currentProblem.clients.push({
        id: newId,
        x: lon,
        y: lat,
        name: displayName,
        delivery: demand,
        pickup: 0,
        service_duration: 1200,
        tw_early: twe,
        tw_late: twl,
        required: true,
      });

      document.getElementById('json-input-editor').value = JSON.stringify(currentProblem, null, 2);
      document.getElementById('add-location-modal').classList.add('hidden');

      map.setView([lat, lon], 9);

      await runOptimizer();
    } catch (err) {
      console.error(err);
      alert('Geocoding Error: ' + err.message);
    } finally {
      btnGeocode.disabled = false;
      btnGeocode.innerHTML = '<i class="fa-solid fa-magnifying-glass-location"></i> Search Location & Add';
    }
  }

  // Load Preset Benchmark Dataset
  async function loadDataset(key) {
    try {
      showLoadingState();
      const res = await fetch(`/api/datasets/${key}`);
      if (!res.ok) throw new Error('Failed to fetch dataset');
      currentProblem = await res.json();

      document.getElementById('problem-name-badge').textContent = currentProblem.name;
      document.getElementById('json-input-editor').value = JSON.stringify(currentProblem, null, 2);

      await runOptimizer();
    } catch (err) {
      console.error(err);
      alert('Error loading dataset: ' + err.message);
    }
  }

  // Generate Random VRP Instance
  async function generateRandomInstance() {
    const clients = parseInt(document.getElementById('random-clients-count').value, 10) || 15;
    const vehicles = parseInt(document.getElementById('random-vehicles-count').value, 10) || 4;
    const tw = document.getElementById('random-tw-check').checked;

    document.getElementById('random-modal').classList.add('hidden');

    try {
      showLoadingState();
      const res = await fetch(`/api/generate_random?num_clients=${clients}&num_vehicles=${vehicles}&include_time_windows=${tw}`, {
        method: 'POST',
      });
      if (!res.ok) throw new Error('Failed to generate random instance');
      currentProblem = await res.json();

      document.getElementById('problem-name-badge').textContent = currentProblem.name;
      document.getElementById('json-input-editor').value = JSON.stringify(currentProblem, null, 2);

      await runOptimizer();
    } catch (err) {
      console.error(err);
      alert('Error generating random instance: ' + err.message);
    }
  }

  // Run PyVRP Optimizer
  async function runOptimizer() {
    if (!currentProblem) return;

    const runtime = parseFloat(document.getElementById('runtime-input').value) || 1.5;
    currentProblem.config.max_runtime_seconds = runtime;

    showLoadingState();

    try {
      const res = await fetch('/api/solve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(currentProblem),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || 'Solver request failed');
      }

      currentSolution = await res.json();
      renderSolution(currentSolution);
    } catch (err) {
      console.error(err);
      alert('Optimizer Error: ' + err.message);
    }
  }

  function triggerDebouncedOptimizer() {
    if (dragDebounceTimer) clearTimeout(dragDebounceTimer);
    dragDebounceTimer = setTimeout(() => {
      runOptimizer();
    }, 150);
  }

  function showLoadingState() {
    document.getElementById('kpi-status').textContent = 'Solving...';
    document.getElementById('kpi-status-card').className = 'kpi-card';
    document.getElementById('btn-solve').disabled = true;
    document.getElementById('btn-solve').innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Solving...';
  }

  // Render Full Solution Outputs
  function renderSolution(sol) {
    document.getElementById('btn-solve').disabled = false;
    document.getElementById('btn-solve').innerHTML = '<i class="fa-solid fa-play"></i> Run Optimizer';

    updateKPIDashboard();

    renderMap(sol);
    renderRoutesList(sol);
    renderGanttChart(sol);
    renderConvergenceChart(sol);
    renderAudit(sol);
    renderLocationsTable();
  }

  // Dynamic Route-Specific KPI Dashboard Updater
  function updateKPIDashboard() {
    if (!currentSolution) return;
    const sol = currentSolution;

    const statusCard = document.getElementById('kpi-status-card');
    const statusText = document.getElementById('kpi-status');
    const filterText = document.getElementById('kpi-filter-text');

    if (selectedRouteId === null) {
      if (sol.is_feasible) {
        statusText.textContent = 'Feasible';
        statusCard.className = 'kpi-card badge-success';
      } else {
        statusText.textContent = 'Infeasible';
        statusCard.className = 'kpi-card badge-danger';
      }

      filterText.textContent = 'All Routes (Overview)';
      document.getElementById('kpi-cost').textContent = sol.total_cost.toLocaleString();
      document.getElementById('kpi-distance').textContent = `${sol.total_distance.toLocaleString()} km`;
      document.getElementById('kpi-duration').textContent = formatTime12h(sol.total_duration);
      document.getElementById('kpi-vehicles').textContent = `${sol.vehicles_used} / ${sol.total_vehicles_available}`;
      document.getElementById('kpi-clients').textContent = `${sol.clients_visited} / ${sol.total_clients}`;
    } else {
      const r = sol.routes.find((route) => route.route_id === selectedRouteId);
      if (r) {
        statusText.textContent = `Route #${r.route_id}`;
        statusCard.className = 'kpi-card badge-info';
        filterText.textContent = `Route #${r.route_id} Focus`;

        document.getElementById('kpi-cost').textContent = r.cost.toLocaleString();
        document.getElementById('kpi-distance').textContent = `${r.distance.toLocaleString()} km`;
        document.getElementById('kpi-duration').textContent = formatTime12h(r.duration);
        document.getElementById('kpi-vehicles').textContent = `1 (${r.vehicle_type_name})`;
        document.getElementById('kpi-clients').textContent = `${r.num_stops} Stops (${r.max_load}/${r.capacity})`;
      }
    }
  }

  // Fast Parallel OSRM Routing Machine Fetcher with Cache
  async function fetchRealRoadGeometry(waypoints) {
    if (waypoints.length < 2) return waypoints;
    const coordStr = waypoints.map((pt) => `${pt[1].toFixed(5)},${pt[0].toFixed(5)}`).join(';');

    if (osrmCache.has(coordStr)) {
      return osrmCache.get(coordStr);
    }

    const url = `https://router.project-osrm.org/route/v1/driving/${coordStr}?overview=full&geometries=geojson`;

    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 1200);
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);

      if (!res.ok) return waypoints;
      const data = await res.json();
      if (data.routes && data.routes.length > 0) {
        const roadCoords = data.routes[0].geometry.coordinates.map((c) => [c[1], c[0]]);
        osrmCache.set(coordStr, roadCoords);
        return roadCoords;
      }
    } catch (e) {
      return waypoints;
    }
    return waypoints;
  }

  // Render Map Elements & Parallel Real Road Polylines
  async function renderMap(sol) {
    if (!map) return;

    map.invalidateSize();

    mapLayers.forEach((l) => map.removeLayer(l));
    mapLayers = [];

    const bounds = [];
    const legendItemsContainer = document.getElementById('legend-items');
    legendItemsContainer.innerHTML = '';

    // Add Draggable Depot Markers (Bulletproof Matching)
    currentProblem.depots.forEach((d, depIdx) => {
      const icon = L.divIcon({
        className: 'custom-map-icon depot-icon',
        html: `<div style="background:#06b6d4;color:#fff;width:28px;height:28px;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:14px;border:2px solid #fff;box-shadow:0 0 10px rgba(6,182,212,0.8);"><i class="fa-solid fa-warehouse"></i></div>`,
        iconSize: [28, 28],
      });

      const marker = L.marker([d.y, d.x], { icon, draggable: true }).addTo(map);
      marker.bindPopup(`<b>🏬 ${d.name}</b><br>Coordinates: (${d.x.toFixed(4)}, ${d.y.toFixed(4)})<br><i>Drag marker on map to relocate!</i>`);

      // Bulletproof Depot Drag Handler
      marker.on('dragend', (e) => {
        const newPos = e.target.getLatLng();
        const depotTarget = currentProblem.depots[depIdx] || currentProblem.depots.find((dep) => dep.id === d.id || dep.name === d.name);
        if (depotTarget) {
          depotTarget.x = parseFloat(newPos.lng.toFixed(4));
          depotTarget.y = parseFloat(newPos.lat.toFixed(4));
          document.getElementById('json-input-editor').value = JSON.stringify(currentProblem, null, 2);
          triggerDebouncedOptimizer();
        }
      });

      mapLayers.push(marker);
      bounds.push([d.y, d.x]);
    });

    // Add Draggable Customer Markers (Bulletproof Coordinate Matching)
    const routePromises = sol.routes.map(async (r, idx) => {
      const routeColor = ROUTE_COLORS[idx % ROUTE_COLORS.length];
      const waypoints = [];

      r.activities.forEach((act) => {
        waypoints.push([act.y, act.x]);
        bounds.push([act.y, act.x]);

        if (act.activity_type !== 'DEPOT') {
          let iconHtml = `<div style="background:${routeColor};color:#fff;width:24px;height:24px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;font-weight:bold;border:2px solid #fff;box-shadow:0 0 6px ${routeColor};">${act.sequence_index}</div>`;

          const icon = L.divIcon({
            className: 'custom-map-icon client-icon',
            html: iconHtml,
            iconSize: [24, 24],
          });

          const marker = L.marker([act.y, act.x], { icon, draggable: true }).addTo(map);
          marker.bindPopup(`
            <b>📍 ${act.location_name}</b> [${act.activity_type}]<br>
            <b>Route:</b> #${r.route_id}<br>
            <b>Stop Order:</b> ${act.sequence_index}<br>
            <b>Arrival Schedule:</b> ${formatTime12h(act.start_time)}<br>
            <b>Departure Schedule:</b> ${formatTime12h(act.end_time)}<br>
            <b>Service Time:</b> ${Math.round(act.service_duration / 60)} mins<br>
            <b>Current Load:</b> ${act.current_load}<br>
            <i>Drag marker to relocate customer!</i>
          `);

          // Bulletproof Customer Drag Handler (Matches by ID, Name, or Proximity)
          marker.on('dragend', (e) => {
            const newPos = e.target.getLatLng();
            const clientMatch = currentProblem.clients.find(
              (c) => c.id === act.location_id || 
                     c.name === act.location_name || 
                     (Math.abs(c.x - act.x) < 0.001 && Math.abs(c.y - act.y) < 0.001)
            );

            if (clientMatch) {
              clientMatch.x = parseFloat(newPos.lng.toFixed(4));
              clientMatch.y = parseFloat(newPos.lat.toFixed(4));
              document.getElementById('json-input-editor').value = JSON.stringify(currentProblem, null, 2);
              triggerDebouncedOptimizer();
            }
          });

          mapLayers.push(marker);
        }
      });

      const legendItem = document.createElement('div');
      legendItem.className = 'legend-item';
      legendItem.style.cursor = 'pointer';
      legendItem.innerHTML = `<span class="legend-color-dot" style="background:${routeColor};"></span> Route #${r.route_id} (${r.num_stops} stops, ${r.distance} km)`;
      legendItem.addEventListener('click', () => {
        handleRouteClick(r.route_id);
      });

      legendItemsContainer.appendChild(legendItem);

      const roadCoords = await fetchRealRoadGeometry(waypoints);
      return { routeId: r.route_id, roadCoords, routeColor };
    });

    const routeResults = await Promise.all(routePromises);

    routeResults.forEach(({ routeId, roadCoords, routeColor }) => {
      const isSelected = selectedRouteId === routeId;
      const polyline = L.polyline(roadCoords, {
        color: routeColor,
        weight: isSelected ? 9 : 5,
        opacity: isSelected ? 1.0 : 0.85,
        smoothFactor: 1,
      }).addTo(map);

      polyline.on('click', (e) => {
        L.DomEvent.stopPropagation(e);
        if (polylineClickTimer) clearTimeout(polylineClickTimer);

        polylineClickTimer = setTimeout(() => {
          handleRouteClick(routeId);
        }, 220);
      });

      polyline.on('dblclick', (e) => {
        L.DomEvent.stopPropagation(e);
        if (polylineClickTimer) clearTimeout(polylineClickTimer);
        openDClickModal(e.latlng);
      });

      mapLayers.push(polyline);
    });

    if (bounds.length > 0) {
      setTimeout(() => {
        map.fitBounds(bounds, { padding: [40, 40] });
        map.invalidateSize();
      }, 50);
    }
  }

  function fitMapBounds() {
    if (map && mapLayers.length > 0) {
      const group = new L.featureGroup(mapLayers);
      map.fitBounds(group.getBounds(), { padding: [40, 40] });
      map.invalidateSize();
    }
  }

  // Render Tab 1: Routes Breakdown
  function renderRoutesList(sol) {
    const container = document.getElementById('routes-container');
    container.innerHTML = '';

    if (sol.routes.length === 0) {
      container.innerHTML = `<div class="empty-state"><p>No active routes generated.</p></div>`;
      return;
    }

    sol.routes.forEach((r, idx) => {
      const routeColor = ROUTE_COLORS[idx % ROUTE_COLORS.length];

      const card = document.createElement('div');
      card.className = 'route-card';
      card.setAttribute('data-route-id', r.route_id);
      card.style.cursor = 'pointer';

      card.addEventListener('click', (e) => {
        handleRouteClick(r.route_id);
      });

      let rowsHtml = '';
      r.activities.forEach((act) => {
        const badgeClass = act.activity_type === 'DEPOT' ? 'badge-info' : 'badge-success';
        rowsHtml += `
          <tr>
            <td>${act.sequence_index}</td>
            <td><span class="badge ${badgeClass}">${act.activity_type}</span></td>
            <td><strong>${act.location_name}</strong></td>
            <td><i class="fa-regular fa-clock"></i> ${formatTime12h(act.start_time)} ➔ ${formatTime12h(act.end_time)}</td>
            <td>${Math.round(act.service_duration / 60)} mins</td>
            <td>${act.wait_duration > 0 ? `<span class="badge badge-warning">+${Math.round(act.wait_duration / 60)}m</span>` : '0'}</td>
            <td>${act.current_load}</td>
          </tr>
        `;
      });

      card.innerHTML = `
        <div class="route-card-header">
          <div class="route-card-title">
            <span class="legend-color-dot" style="background:${routeColor};"></span>
            Route #${r.route_id} (${r.vehicle_type_name})
          </div>
          <div class="route-stats-row">
            <span>Stops: ${r.num_stops}</span>
            <span>Dist: ${r.distance} km</span>
            <span>Dur: ${formatTime12h(r.duration)}</span>
            <span>Load: ${r.max_load}/${r.capacity} (${r.capacity_utilization_pct}%)</span>
          </div>
        </div>
        <div class="route-card-body">
          <table class="route-stops-table">
            <thead>
              <tr>
                <th>Seq</th>
                <th>Type</th>
                <th>Location</th>
                <th>12-Hour Schedule</th>
                <th>Service</th>
                <th>Wait</th>
                <th>Load</th>
              </tr>
            </thead>
            <tbody>${rowsHtml}</tbody>
          </table>
        </div>
      `;

      container.appendChild(card);
    });

    highlightSelectedRouteCard();
  }

  // Highlight selected route card in the list
  function highlightSelectedRouteCard() {
    document.querySelectorAll('.route-card').forEach((card) => {
      const rId = parseInt(card.getAttribute('data-route-id'), 10);
      if (selectedRouteId !== null && rId === selectedRouteId) {
        card.style.borderColor = 'var(--accent-cyan)';
        card.style.boxShadow = '0 0 15px rgba(6, 182, 212, 0.4)';
      } else {
        card.style.borderColor = 'var(--border-color)';
        card.style.boxShadow = 'none';
      }
    });
  }

  // Render Tab 2: Editable Locations Table
  function renderLocationsTable() {
    const container = document.getElementById('locations-table-container');
    if (!currentProblem || !container) return;

    let rowsHtml = '';
    currentProblem.clients.forEach((c, idx) => {
      rowsHtml += `
        <tr data-client-idx="${idx}">
          <td><strong>${c.id}</strong></td>
          <td><input type="text" class="form-input loc-name-input" value="${c.name}"></td>
          <td><input type="number" step="0.0001" class="form-input number-input loc-lat-input" value="${c.y}"></td>
          <td><input type="number" step="0.0001" class="form-input number-input loc-lng-input" value="${c.x}"></td>
          <td><input type="number" class="form-input number-input loc-del-input" value="${c.delivery}"></td>
          <td><input type="number" class="form-input number-input loc-twe-input" value="${c.tw_early}"></td>
          <td><input type="number" class="form-input number-input loc-twl-input" value="${c.tw_late}"></td>
          <td><button class="btn btn-sm btn-danger btn-del-client" data-client-idx="${idx}"><i class="fa-solid fa-trash"></i></button></td>
        </tr>
      `;
    });

    container.innerHTML = `
      <table class="route-stops-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Location Name</th>
            <th>Latitude (Y)</th>
            <th>Longitude (X)</th>
            <th>Demand</th>
            <th>TW Early</th>
            <th>TW Late</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>${rowsHtml}</tbody>
      </table>
    `;

    container.querySelectorAll('.btn-del-client').forEach((btn) => {
      btn.addEventListener('click', (e) => {
        const cIdx = parseInt(e.currentTarget.getAttribute('data-client-idx'), 10);
        currentProblem.clients.splice(cIdx, 1);
        renderLocationsTable();
        runOptimizer();
      });
    });
  }

  function saveLocationsFromTable() {
    const container = document.getElementById('locations-table-container');
    if (!currentProblem || !container) return;

    const rows = container.querySelectorAll('tbody tr');
    rows.forEach((tr) => {
      const cIdx = parseInt(tr.getAttribute('data-client-idx'), 10);
      if (currentProblem.clients[cIdx]) {
        currentProblem.clients[cIdx].name = tr.querySelector('.loc-name-input').value;
        currentProblem.clients[cIdx].y = parseFloat(tr.querySelector('.loc-lat-input').value) || 0;
        currentProblem.clients[cIdx].x = parseFloat(tr.querySelector('.loc-lng-input').value) || 0;
        currentProblem.clients[cIdx].delivery = parseInt(tr.querySelector('.loc-del-input').value, 10) || 0;
        currentProblem.clients[cIdx].tw_early = parseInt(tr.querySelector('.loc-twe-input').value, 10) || 0;
        currentProblem.clients[cIdx].tw_late = parseInt(tr.querySelector('.loc-twl-input').value, 10) || 86400;
      }
    });
    document.getElementById('json-input-editor').value = JSON.stringify(currentProblem, null, 2);
  }

  // Render Tab 3: Schedule Gantt Chart
  function renderGanttChart(sol) {
    const ctx = document.getElementById('gantt-chart').getContext('2d');
    if (ganttChart) ganttChart.destroy();

    const labels = sol.routes.map((r) => `Route #${r.route_id}`);
    const datasets = [];

    sol.routes.forEach((r, idx) => {
      const color = ROUTE_COLORS[idx % ROUTE_COLORS.length];
      r.activities.forEach((act) => {
        if (act.activity_type !== 'DEPOT') {
          datasets.push({
            label: `${act.location_name}`,
            data: [
              {
                x: [act.start_time, act.end_time],
                y: `Route #${r.route_id}`,
              },
            ],
            backgroundColor: color,
            borderColor: '#ffffff',
            borderWidth: 1,
            barPercentage: 0.5,
          });
        }
      });
    });

    ganttChart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: datasets,
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: (context) => {
                const v = context.raw.x;
                return `${context.dataset.label}: ${formatTime12h(v[0])} ➔ ${formatTime12h(v[1])}`;
              },
            },
          },
        },
        scales: {
          x: {
            title: { display: true, text: 'Time Schedule (12-Hour Format)', color: '#94a3b8' },
            grid: { color: '#334155' },
            ticks: {
              color: '#94a3b8',
              callback: (value) => formatTime12h(value),
            },
          },
          y: {
            grid: { color: '#334155' },
            ticks: { color: '#f8fafc' },
          },
        },
      },
    });
  }

  // Render Tab 4: Iteration Convergence Plot
  function renderConvergenceChart(sol) {
    const ctx = document.getElementById('convergence-chart').getContext('2d');
    if (convergenceChart) convergenceChart.destroy();

    const labels = sol.convergence.map((pt) => pt.iteration);
    const data = sol.convergence.map((pt) => pt.best_cost);

    convergenceChart = new Chart(ctx, {
      type: 'line',
      data: {
        labels: labels,
        datasets: [
          {
            label: 'PyVRP Best Solution Objective Cost',
            data: data,
            borderColor: '#3b82f6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
            fill: true,
            tension: 0.2,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: '#f8fafc' } },
        },
        scales: {
          x: {
            title: { display: true, text: 'Solver Iterations', color: '#94a3b8' },
            grid: { color: '#334155' },
            ticks: { color: '#94a3b8' },
          },
          y: {
            title: { display: true, text: 'Objective Cost', color: '#94a3b8' },
            grid: { color: '#334155' },
            ticks: { color: '#f8fafc' },
          },
        },
      },
    });
  }

  // Render Tab 5: Constraint Violation Audit
  function renderAudit(sol) {
    const container = document.getElementById('audit-container');
    const v = sol.constraint_violations;

    let auditHtml = `
      <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:1rem;margin-bottom:1rem;">
        <div class="kpi-card">
          <div class="kpi-data">
            <span class="kpi-label">Capacity Violations</span>
            <span class="kpi-value ${v.capacity_violations > 0 ? 'badge-danger' : 'badge-success'}">${v.capacity_violations}</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-data">
            <span class="kpi-label">Time Window Violations</span>
            <span class="kpi-value ${v.time_window_violations > 0 ? 'badge-danger' : 'badge-success'}">${v.time_window_violations}</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-data">
            <span class="kpi-label">Duration Limit Violations</span>
            <span class="kpi-value ${v.duration_violations > 0 ? 'badge-danger' : 'badge-success'}">${v.duration_violations}</span>
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-data">
            <span class="kpi-label">Unvisited Required Customers</span>
            <span class="kpi-value ${v.unvisited_required_clients > 0 ? 'badge-danger' : 'badge-success'}">${v.unvisited_required_clients}</span>
          </div>
        </div>
      </div>
    `;

    if (sol.is_feasible && (!v.details || v.details.length === 0)) {
      auditHtml += `
        <div class="badge badge-success" style="padding:1rem;font-size:0.9rem;width:100%;text-align:center;">
          <i class="fa-solid fa-circle-check"></i> Clean Solution! All vehicle capacity, maximum distance, duration limits, time windows, and customer pickup/deliveries are fully satisfied.
        </div>
      `;
    } else {
      let detailsList = v.details.map((d) => `<li>${d}</li>`).join('');
      auditHtml += `
        <div style="background:rgba(244,63,94,0.1);border:1px solid #f43f5e;border-radius:8px;padding:1rem;color:#fecdd3;">
          <h4 style="margin-bottom:0.5rem;font-weight:700;"><i class="fa-solid fa-triangle-exclamation"></i> Constraint Diagnostic Log:</h4>
          <ul style="padding-left:1.2rem;font-size:0.85rem;">${detailsList}</ul>
        </div>
      `;
    }

    container.innerHTML = auditHtml;
  }
});

// ── State ──
const MONTHS = ["January","February","March","April","May","June",
  "July","August","September","October","November","December"];

let yearlyData   = [];
let activeChart  = null;
let activeMetric = "rainfall";
let selectedYear  = new Date().getFullYear();
let selectedMonth = null;
let currentLocation = { lat: 11.00, lon: 76.95, name: "Coimbatore, India" };
let pendingLocation = null;
let leafletMap = null;
let leafletMarker = null;

// ══════════════════════════════════════════
// LOCATION PANEL
// ══════════════════════════════════════════
function openLocationPanel() {
  document.getElementById("locOverlay").style.display = "flex";
  if (!leafletMap) initMap();
}
function closeLocationPanel() {
  document.getElementById("locOverlay").style.display = "none";
}

function initMap() {
  leafletMap = L.map("locationMap").setView([20, 78], 4);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "© OpenStreetMap"
  }).addTo(leafletMap);

  leafletMap.on("click", e => {
    const { lat, lng } = e.latlng;
    setMapPin(lat, lng, `${lat.toFixed(2)}, ${lng.toFixed(2)}`);
  });
}

function setMapPin(lat, lon, name) {
  if (leafletMarker) leafletMap.removeLayer(leafletMarker);
  leafletMarker = L.marker([lat, lon]).addTo(leafletMap);
  pendingLocation = { lat: parseFloat(lat.toFixed(4)), lon: parseFloat(lon.toFixed(4)), name };
  document.getElementById("locCoords").textContent = `📍 ${name}  (${lat.toFixed(4)}, ${lon.toFixed(4)})`;
  document.getElementById("locConfirmBtn").disabled = false;
}

async function searchLocation() {
  const q = document.getElementById("locSearch").value.trim();
  if (!q) return;
  try {
    const r = await fetch(`https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=1`);
    const d = await r.json();
    if (!d.length) { alert("Location not found. Try a different search."); return; }
    const { lat, lon, display_name } = d[0];
    leafletMap.setView([lat, lon], 8);
    setMapPin(parseFloat(lat), parseFloat(lon), display_name.split(",").slice(0,2).join(","));
  } catch(e) { alert("Search failed. Check your internet connection."); }
}

document.addEventListener("DOMContentLoaded", () => {
  const inp = document.getElementById("locSearch");
  if (inp) inp.addEventListener("keydown", e => { if (e.key === "Enter") searchLocation(); });
});

function useGPS() {
  if (!navigator.geolocation) { alert("GPS not available in this browser."); return; }
  navigator.geolocation.getCurrentPosition(pos => {
    const { latitude: lat, longitude: lon } = pos.coords;
    if (leafletMap) { leafletMap.setView([lat, lon], 10); }
    setMapPin(lat, lon, "My Location");
  }, () => alert("Could not get GPS location."));
}

function setPreset(lat, lon, name) {
  if (!leafletMap) initMap();
  leafletMap.setView([lat, lon], 7);
  setMapPin(lat, lon, name);
}

async function confirmLocation() {
  if (!pendingLocation) return;
  closeLocationPanel();
  showRetrainOverlay();

  try {
    const r = await fetch("/api/location/set", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(pendingLocation)
    });
    const d = await r.json();
    if (d.error) throw new Error(d.error);

    currentLocation = pendingLocation;
    document.getElementById("locPillText").textContent = currentLocation.name;
    hideRetrainOverlay();

    // Reload yearly data and re-predict current selection
    await loadYearlyData(selectedYear);
    buildMonthGrid();
    const activeBtn = document.querySelector(".month-btn.active");
    if (activeBtn) activeBtn.click();
    else autoSelectCurrentMonth();

  } catch(e) {
    hideRetrainOverlay();
    alert("Error: " + e.message);
  }
}

// ── Retrain overlay animation ──
function showRetrainOverlay() {
  document.getElementById("retrainOverlay").style.display = "flex";
  const steps = ["rs1","rs2","rs3","rs4"];
  steps.forEach((id,i) => {
    document.getElementById(id).classList.remove("active","done");
    setTimeout(() => {
      document.getElementById(id).classList.add("active");
      if (i > 0) document.getElementById(steps[i-1]).classList.add("done");
    }, i * 2800);
  });
}
function hideRetrainOverlay() {
  document.getElementById("rs4").classList.add("done");
  setTimeout(() => {
    document.getElementById("retrainOverlay").style.display = "none";
    document.querySelectorAll(".rstep").forEach(el => el.classList.remove("active","done"));
  }, 800);
}

// ══════════════════════════════════════════
// MONTH GRID
// ══════════════════════════════════════════
function buildAllowedMonths() {
  const now = new Date();
  const curM = now.getMonth() + 1, curY = now.getFullYear();
  const allowed = [];
  for (let offset = -5; offset <= 5; offset++) {
    let m = curM + offset, y = curY;
    if (m < 1)  { m += 12; y--; }
    if (m > 12) { m -= 12; y++; }
    if (y > curY + 1 || (y === curY + 1 && m > curM)) continue;
    allowed.push({ month: m, year: y });
  }
  return allowed;
}

function buildMonthGrid() {
  const grid = document.getElementById("monthGrid");
  const allowed = buildAllowedMonths();
  const now = new Date();
  const curM = now.getMonth() + 1, curY = now.getFullYear();
  grid.innerHTML = "";
  allowed.forEach(({ month, year }) => {
    const isNow  = month === curM && year === curY;
    const isPast = year < curY || (year === curY && month < curM);
    const btn = document.createElement("button");
    btn.className = "month-btn";
    btn.dataset.month = month;
    btn.dataset.year  = year;
    btn.innerHTML = `
      <span class="m-name">${MONTHS[month-1].slice(0,3)}</span>
      <span class="m-num">${String(month).padStart(2,"0")} · ${year}</span>
      ${isNow  ? '<span class="m-badge now">NOW</span>'    : ""}
      ${isPast && !isNow ? '<span class="m-badge past">PAST</span>' : ""}
      ${!isPast && !isNow ? '<span class="m-badge future">FCST</span>' : ""}
    `;
    btn.addEventListener("click", () => selectMonth(month, year, btn));
    grid.appendChild(btn);
  });
}

// ══════════════════════════════════════════
// PREDICTIONS
// ══════════════════════════════════════════
async function selectMonth(month, year, btn) {
  document.querySelectorAll(".month-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");
  selectedMonth = month;
  selectedYear  = year;

  document.getElementById("resultsSection").style.display = "block";
  document.getElementById("resultsSection").style.opacity = "0.4";
  document.getElementById("resultsSection").scrollIntoView({ behavior:"smooth", block:"start" });

  try {
    const r    = await fetch(`/api/predict/${month}?year=${year}`);
    const data = await r.json();
    if (data.error) throw new Error(data.error);
    renderResults(data);
  } catch(e) {
    console.error(e);
    document.getElementById("resultTip").textContent = "⚠️ Failed to load: " + e.message;
  } finally {
    document.getElementById("resultsSection").style.opacity = "1";
  }
}

function renderResults({ weather, crops, materials, location }) {
  const now  = new Date();
  const curM = now.getMonth() + 1, curY = now.getFullYear();
  let tag = weather.month === curM && selectedYear === curY ? " · Current"
           : selectedYear < curY || (selectedYear === curY && weather.month < curM) ? " · Historical"
           : " · Forecast";

  document.getElementById("resultSeason").textContent   = weather.season + tag;
  document.getElementById("resultMonth").textContent    = `${weather.month_name} ${selectedYear}`;
  document.getElementById("resultLocation").textContent = `📍 ${currentLocation.name}`;
  document.getElementById("resultTip").textContent      = `💡 ${crops.tip}`;

  document.getElementById("wTemp").textContent      = `${weather.temp_avg}°C`;
  document.getElementById("wTempRange").textContent = `${weather.temp_min}° – ${weather.temp_max}°C`;
  document.getElementById("wRain").textContent      = `${weather.rainfall}`;
  document.getElementById("wHumidity").textContent  = `${weather.humidity}%`;
  document.getElementById("wWind").textContent      = `${weather.wind_speed}`;

  // Crops with confidence bars
  document.getElementById("cropList").innerHTML = crops.recommended_conf.map(entry => {
    const m = entry.match(/^(.+?)\s*\((\d+\.?\d*)%\)$/);
    if (!m) return `<li>${entry}</li>`;
    const name = m[1].charAt(0).toUpperCase() + m[1].slice(1);
    const conf = parseFloat(m[2]);
    return `<li>
      <span class="crop-name">${name}</span>
      <span class="crop-conf">
        <span class="conf-bar" style="width:${Math.min(100,conf*2)}px"></span>
        <span class="conf-pct">${conf}%</span>
      </span>
    </li>`;
  }).join("");

  document.getElementById("avoidList").innerHTML    = crops.avoid.map(c=>`<li>${c}</li>`).join("");
  document.getElementById("materialsList").innerHTML = materials.map(m=>`<div class="material-item">${m}</div>`).join("");

  // Data source badge
  if (location) {
    const badge = document.getElementById("dataSourceBadge");
    badge.innerHTML = location.has_real_data
      ? '<span class="m-badge now">NASA REAL</span> Satellite data'
      : '<span class="m-badge past">SYNTHETIC</span> Climate normals';
  }

  loadYearlyData(selectedYear).then(() => renderChart(activeMetric, weather.month - 1));
}

// ══════════════════════════════════════════
// CHART
// ══════════════════════════════════════════
async function loadYearlyData(year) {
  const r = await fetch(`/api/yearly?year=${year}`);
  yearlyData = await r.json();
}

function renderChart(metric, highlightIndex = -1) {
  activeMetric = metric;
  const ctx    = document.getElementById("yearlyChart").getContext("2d");
  const values = yearlyData.map(d => d[metric]);
  const meta   = {
    rainfall: { label:"Rainfall (mm)",        color:"#3A6B8A", fill:"rgba(58,107,138,0.12)" },
    temp_avg: { label:"Avg Temperature (°C)", color:"#C8880A", fill:"rgba(200,136,10,0.12)" },
    humidity: { label:"Humidity (%)",         color:"#2D5A27", fill:"rgba(45,90,39,0.12)"   },
  }[metric];

  if (activeChart) activeChart.destroy();
  activeChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: MONTHS.map(m => m.slice(0,3)),
      datasets: [{
        label: meta.label, data: values,
        borderColor: meta.color, backgroundColor: meta.fill,
        pointBackgroundColor: values.map((_,i)=> i===highlightIndex ? "#A02020" : meta.color),
        pointRadius: values.map((_,i)=> i===highlightIndex ? 8 : 4),
        pointHoverRadius: 8, borderWidth: 2.5, tension: 0.4, fill: true,
      }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { backgroundColor:"#1A2E1A", titleColor:"#F5F0E8", bodyColor:"#F5F0E8", padding:12, cornerRadius:8 }
      },
      scales: {
        x: { grid:{color:"rgba(0,0,0,0.06)"}, ticks:{font:{family:"JetBrains Mono",size:11},color:"#5A5A40"} },
        y: { grid:{color:"rgba(0,0,0,0.06)"}, ticks:{font:{size:11},color:"#5A5A40"} }
      }
    }
  });
}

document.querySelectorAll(".chart-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".chart-tab").forEach(t=>t.classList.remove("active"));
    tab.classList.add("active");
    const activeBtn = document.querySelector(".month-btn.active");
    renderChart(tab.dataset.metric, activeBtn ? parseInt(activeBtn.dataset.month)-1 : -1);
  });
});

function autoSelectCurrentMonth() {
  const now = new Date();
  const btn = document.querySelector(`.month-btn[data-month="${now.getMonth()+1}"][data-year="${now.getFullYear()}"]`);
  if (btn) btn.click();
}

// ── Init ──
(async () => {
  buildMonthGrid();
  // Load initial location meta
  try {
    const r = await fetch("/api/location/meta");
    const m = await r.json();
    if (m.lat) currentLocation = { lat: m.lat, lon: m.lon, name: `${m.lat}, ${m.lon}` };
  } catch(e) {}
  autoSelectCurrentMonth();
})();

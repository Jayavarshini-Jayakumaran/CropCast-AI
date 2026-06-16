const MONTHS = [
  "January","February","March","April","May","June",
  "July","August","September","October","November","December"
];

let yearlyData = [];
let activeChart = null;
let activeMetric = "rainfall";

// ── Build month buttons ──
function buildMonthGrid() {
  const grid = document.getElementById("monthGrid");
  MONTHS.forEach((name, i) => {
    const btn = document.createElement("button");
    btn.className = "month-btn";
    btn.dataset.month = i + 1;
    btn.innerHTML = `<span class="m-name">${name.slice(0,3)}</span><span class="m-num">${String(i+1).padStart(2,"0")}</span>`;
    btn.addEventListener("click", () => selectMonth(i + 1, btn));
    grid.appendChild(btn);
  });
}

// ── Select month ──
async function selectMonth(month, btn) {
  document.querySelectorAll(".month-btn").forEach(b => b.classList.remove("active"));
  btn.classList.add("active");

  try {
    const res = await fetch(`/api/predict/${month}`);
    const data = await res.json();
    renderResults(data);

    document.getElementById("resultsSection").style.display = "block";
    document.getElementById("resultsSection").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (err) {
    console.error("Failed to fetch prediction:", err);
  }
}

// ── Render results ──
function renderResults({ weather, crops, materials }) {
  // Header
  document.getElementById("resultSeason").textContent = weather.season;
  document.getElementById("resultMonth").textContent = weather.month_name;
  document.getElementById("resultTip").textContent = `💡 ${crops.tip}`;

  // Weather cards
  document.getElementById("wTemp").textContent = `${weather.temp_avg}°C`;
  document.getElementById("wTempRange").textContent = `${weather.temp_min}° – ${weather.temp_max}°C`;
  document.getElementById("wRain").textContent = `${weather.rainfall}`;
  document.getElementById("wHumidity").textContent = `${weather.humidity}%`;
  document.getElementById("wWind").textContent = `${weather.wind_speed}`;

  // Crops
  const cropList = document.getElementById("cropList");
  cropList.innerHTML = crops.recommended.map(c => `<li>${c}</li>`).join("");

  const avoidList = document.getElementById("avoidList");
  avoidList.innerHTML = crops.avoid.map(c => `<li>${c}</li>`).join("");

  // Materials
  const matList = document.getElementById("materialsList");
  matList.innerHTML = materials.map(m => `<div class="material-item">${m}</div>`).join("");

  // Rebuild chart with highlight
  renderChart(activeMetric, weather.month - 1);
}

// ── Yearly chart ──
async function loadYearlyData() {
  const res = await fetch("/api/yearly");
  yearlyData = await res.json();
}

function renderChart(metric, highlightIndex = -1) {
  activeMetric = metric;
  const canvas = document.getElementById("yearlyChart");
  const ctx = canvas.getContext("2d");

  const labels = MONTHS.map(m => m.slice(0, 3));
  const values = yearlyData.map(d => d[metric]);

  const metaMap = {
    rainfall:  { label: "Rainfall (mm)",    color: "#4A7FA5", fill: "rgba(74,127,165,0.12)" },
    temp_avg:  { label: "Avg Temperature (°C)", color: "#E8A020", fill: "rgba(232,160,32,0.12)" },
    humidity:  { label: "Humidity (%)",      color: "#3D6B35", fill: "rgba(61,107,53,0.12)" },
  };
  const meta = metaMap[metric];

  const pointColors = values.map((_, i) =>
    i === highlightIndex ? "#C0392B" : meta.color
  );
  const pointRadius = values.map((_, i) => i === highlightIndex ? 8 : 4);

  if (activeChart) activeChart.destroy();

  activeChart = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: meta.label,
        data: values,
        borderColor: meta.color,
        backgroundColor: meta.fill,
        pointBackgroundColor: pointColors,
        pointRadius: pointRadius,
        pointHoverRadius: 8,
        borderWidth: 2.5,
        tension: 0.4,
        fill: true,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: "#2C1A0E",
          titleColor: "#F0F5EE",
          bodyColor: "#F0F5EE",
          padding: 12,
          cornerRadius: 8,
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(0,0,0,0.05)" },
          ticks: { font: { family: "JetBrains Mono", size: 11 }, color: "#6B6B6B" }
        },
        y: {
          grid: { color: "rgba(0,0,0,0.05)" },
          ticks: { font: { size: 11 }, color: "#6B6B6B" }
        }
      }
    }
  });
}

// ── Chart tab switching ──
document.querySelectorAll(".chart-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".chart-tab").forEach(t => t.classList.remove("active"));
    tab.classList.add("active");

    const activeBtn = document.querySelector(".month-btn.active");
    const highlightIdx = activeBtn ? parseInt(activeBtn.dataset.month) - 1 : -1;
    renderChart(tab.dataset.metric, highlightIdx);
  });
});

// ── Init ──
(async () => {
  buildMonthGrid();
  await loadYearlyData();

  // Auto-select current month
  const currentMonth = new Date().getMonth() + 1;
  const defaultBtn = document.querySelector(`.month-btn[data-month="${currentMonth}"]`);
  if (defaultBtn) defaultBtn.click();
})();

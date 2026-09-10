/* =====================================================
   AirGuard AI — Frontend Application
   ===================================================== */

"use strict";

// ── State ────────────────────────────────────────────
const state = {
  city: "bhilai",
  ageGroup: "adult",
  activity: "moderate",
  sensitivity: "none",
  sessionId: "sess_" + Math.random().toString(36).slice(2),
  forecastChart: null,
  analyticsChart: null,
  darkMode: false,
  chatOpen: true,
};

const API = window.location.origin; // same origin (Flask serves frontend)

// ── Helpers ──────────────────────────────────────────
function $(id) { return document.getElementById(id); }
function setText(id, v) { const el = $(id); if (el) el.textContent = v; }
function setHTML(id, v) { const el = $(id); if (el) el.innerHTML = v; }
function showLoading(on) { $("loadingOverlay").style.display = on ? "flex" : "none"; }

function aqi2Color(aqi) {
  if (aqi <= 50)  return "#22c55e";
  if (aqi <= 100) return "#eab308";
  if (aqi <= 150) return "#f97316";
  if (aqi <= 200) return "#ef4444";
  if (aqi <= 300) return "#a855f7";
  return "#7f1d1d";
}

function pollFillPct(pollutant, value) {
  const maxes = { pm25: 250, pm10: 430, no2: 200, o3: 200, co: 15, so2: 350 };
  return Math.min(100, Math.round((value / (maxes[pollutant] || 200)) * 100));
}

// ── Date Display ─────────────────────────────────────
function initDate() {
  const d = new Date();
  $("currentDate").textContent = d.toLocaleDateString("en-IN", {
    weekday: "short", day: "numeric", month: "short", year: "numeric",
  });
}

// ── Section Navigation ────────────────────────────────
function showSection(name) {
  document.querySelectorAll(".section").forEach(s => s.classList.remove("active"));
  const el = $("section" + name.charAt(0).toUpperCase() + name.slice(1));
  if (el) el.classList.add("active");
  if (name === "analytics") loadAnalytics();
}
window.showSection = showSection;

// ── AQI Gauge (Chart.js doughnut) ────────────────────
function drawGauge(aqi) {
  const canvas = $("aqiGauge");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");

  // Segments: Good | Moderate | USG | Unhealthy | Very | Hazardous
  const segments = [50, 50, 50, 50, 100, 200]; // spans within 500
  const colors   = ["#22c55e","#eab308","#f97316","#ef4444","#a855f7","#7f1d1d"];
  const pct = Math.min(aqi, 500) / 500;

  // Use doughnut as half gauge
  if (window._gaugeChart) window._gaugeChart.destroy();
  window._gaugeChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      datasets: [{
        data: segments,
        backgroundColor: colors,
        borderWidth: 0,
      }],
    },
    options: {
      rotation: -90,
      circumference: 180,
      cutout: "70%",
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      animation: { duration: 600 },
    },
  });

  // Draw needle
  const drawNeedle = () => {
    const { width, height } = canvas;
    const cx = width / 2, cy = height - 10;
    const angle = Math.PI * (pct - 0.5); // -90° to +90°
    const len = cy * 0.7;
    ctx.save();
    ctx.strokeStyle = "#1a202c";
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx + len * Math.cos(angle), cy + len * Math.sin(angle));
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(cx, cy, 6, 0, 2 * Math.PI);
    ctx.fillStyle = "#1a202c";
    ctx.fill();
    ctx.restore();
  };
  setTimeout(drawNeedle, 650);
}

// ── Dashboard Load ────────────────────────────────────
async function loadDashboard(showSpinner = true) {
  if (showSpinner) showLoading(true);
  try {
    const params = new URLSearchParams({
      city: state.city,
      age_group: state.ageGroup,
      activity: state.activity,
      sensitivity: state.sensitivity,
    });
    const res = await fetch(`${API}/api/dashboard?${params}`);
    const json = await res.json();
    if (!json.success) throw new Error(json.error || "Failed to load data");
    renderDashboard(json.data);
  } catch (err) {
    console.error(err);
    showError("Could not load dashboard: " + err.message);
  } finally {
    showLoading(false);
  }
}

// ── Render Dashboard ──────────────────────────────────
function renderDashboard(data) {
  const aqi_data = data.aqi_data;
  const health   = data.health_advisory;
  const forecast = data.forecast;
  const community= data.community;
  const policy   = data.policy_insights;
  const plan     = data.daily_plan;

  // ── AQI Card
  const aqi = aqi_data.aqi;
  setText("aqiValue", aqi);
  setText("aqiCategory", aqi_data.category);
  setText("riskLevel", aqi_data.risk);
  setText("mainPollutant", aqi_data.main_pollutant);
  setText("cityName", aqi_data.city);
  setText("lastUpdated", new Date(aqi_data.updated_at).toLocaleTimeString("en-IN"));
  setText("aqiInterpretation", data.aqi_interpretation);
  $("aqiValue").style.color = aqi2Color(aqi);
  if (aqi_data.demo) $("demoTag").style.display = "block";
  // Show Groq tag if AI was used
  const planSrc2 = data.plan_source || "";
  if (planSrc2.toLowerCase().includes("groq")) {
    $("groqTag").style.display = "block";
  }

  drawGauge(aqi);

  // ── Pollutants
  const polls = aqi_data.pollutants;
  ["pm25","pm10","no2","o3","co","so2"].forEach(p => {
    const val = polls[p] || 0;
    setText(`val-${p}`, val);
    const fill = $(`bar-${p}`);
    if (fill) {
      fill.style.width = pollFillPct(p, val) + "%";
      fill.style.background = aqi2Color(Math.min(aqi, 300));
    }
  });

  // ── Health Advisory
  $("healthVerdict").textContent = health.verdict;
  $("healthVerdict").style.borderLeft = `4px solid ${health.verdict_color}`;
  const ul = $("healthRecs");
  ul.innerHTML = health.recommendations
    .map(r => `<li>${r}</li>`)
    .join("");
  setText("healthDisclaimer", health.disclaimer);

  // ── Forecast Chart
  renderForecast(forecast);

  // ── Community Actions
  setText("communitySummary", community.summary);
  $("communityList").innerHTML = community.actions
    .map(a => `
      <div class="community-action">
        <div class="comm-icon">${a.icon}</div>
        <div>
          <div class="comm-title">${a.title}</div>
          <div class="comm-detail">${a.detail}</div>
        </div>
      </div>`)
    .join("");

  // ── Daily Plan
  setText("dailyPlan", plan);
  // Show actual LLM source in workflow badge and plan source badge
  const planSrc = data.plan_source || "AirGuard AI";
  const planBadge = $("planSourceBadge");
  if (planBadge) planBadge.textContent = planSrc;

  // ── Policy Insights
  setText("pol-issue",     policy.current_issue);
  setText("pol-why",       policy.why_it_matters);
  setText("pol-public",    policy.recommended_public_action);
  setText("pol-community", policy.community_action);
  setText("pol-awareness", policy.awareness_message);

  // ── Alert Banner
  if (aqi > 150) {
    $("alertBanner").style.display = "flex";
    setText("alertText", `⚠️ AQI Alert: ${aqi} — ${aqi_data.category} in ${aqi_data.city}. ${health.verdict}`);
  }
}

// ── Forecast Chart ────────────────────────────────────
function renderForecast(forecast) {
  const labels  = forecast.forecast.map(d => d.label);
  const values  = forecast.forecast.map(d => d.aqi);
  const colors  = forecast.forecast.map(d => aqi2Color(d.aqi));

  const forecastCards = $("forecastCards");
  forecastCards.innerHTML = forecast.forecast.slice(0, 3).map(d => `
    <div class="forecast-day" style="border-top: 3px solid ${aqi2Color(d.aqi)}">
      <div class="fd-label">${d.label}</div>
      <div class="fd-aqi" style="color:${aqi2Color(d.aqi)}">${d.aqi}</div>
      <div class="fd-cat">${d.category.split(" ").slice(0,2).join(" ")}</div>
    </div>`).join("");

  setText("preventiveAction", forecast.preventive_action);

  const ctx = $("forecastChart").getContext("2d");
  if (state.forecastChart) state.forecastChart.destroy();
  state.forecastChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels,
      datasets: [{
        label: "AQI",
        data: values,
        backgroundColor: colors,
        borderRadius: 6,
      }],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => `AQI: ${ctx.parsed.y}`,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: Math.max(500, ...values),
          grid: { color: "rgba(100,116,139,.15)" },
          ticks: { color: "#64748b" },
        },
        x: { grid: { display: false }, ticks: { color: "#64748b" } },
      },
    },
  });
}

// ── Analytics ─────────────────────────────────────────
async function loadAnalytics() {
  try {
    const res  = await fetch(`${API}/api/analytics?city=${state.city}`);
    const json = await res.json();
    if (!json.success) return;
    const d = json.data;
    setText("stat-avg",    d.avg_aqi);
    setText("stat-max",    d.max_aqi);
    setText("stat-min",    d.min_aqi);
    setText("stat-poll",   d.most_common_pollutant);
    setText("stat-alerts", d.alerts_generated);
    setText("stat-total",  d.total_readings);

    if (d.recent_trend && d.recent_trend.length) {
      const ctx = $("analyticsChart").getContext("2d");
      if (state.analyticsChart) state.analyticsChart.destroy();
      const sorted = [...d.recent_trend].reverse();
      state.analyticsChart = new Chart(ctx, {
        type: "line",
        data: {
          labels: sorted.map((_, i) => `R${i + 1}`),
          datasets: [{
            label: "AQI Trend",
            data: sorted.map(r => r.aqi),
            borderColor: "#3b82f6",
            backgroundColor: "rgba(59,130,246,.1)",
            tension: 0.4,
            fill: true,
            pointRadius: 4,
            pointBackgroundColor: sorted.map(r => aqi2Color(r.aqi)),
          }],
        },
        options: {
          responsive: true,
          plugins: { legend: { display: false } },
          scales: {
            y: { beginAtZero: true, grid: { color: "rgba(100,116,139,.12)" } },
            x: { grid: { display: false } },
          },
        },
      });
    }
  } catch (e) {
    console.warn("Analytics error:", e);
  }
}

// ── Profile Form ──────────────────────────────────────
function initProfileForm() {
  $("profileForm").addEventListener("submit", async e => {
    e.preventDefault();
    const profile = {
      name:           $("p-name").value.trim() || "Anonymous",
      age_group:      $("p-age").value,
      city:           $("p-city").value,
      activity_level: $("p-activity").value,
      sensitivity:    $("p-sensitivity").value,
    };
    state.ageGroup   = profile.age_group;
    state.activity   = profile.activity_level;
    state.sensitivity= profile.sensitivity;
    state.city       = profile.city;
    $("citySelect").value = profile.city;

    try {
      const res = await fetch(`${API}/api/profile`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(profile),
      });
      const json = await res.json();
      const msg = $("profileMsg");
      if (json.success) {
        msg.textContent = "✅ Profile saved! Refreshing your recommendations...";
        msg.className = "profile-msg success";
        setTimeout(() => { showSection("dashboard"); loadDashboard(); }, 1200);
      } else {
        msg.textContent = "❌ " + (json.error || "Could not save profile.");
        msg.className = "profile-msg error";
      }
    } catch (err) {
      const msg = $("profileMsg");
      msg.textContent = "❌ Network error. Profile saved locally.";
      msg.className = "profile-msg error";
    }
  });
}

// ── Chat ──────────────────────────────────────────────
function toggleChat() {
  state.chatOpen = !state.chatOpen;
  $("chatBody").style.display = state.chatOpen ? "flex" : "none";
  $("chatToggleIcon").textContent = state.chatOpen ? "▲" : "▼";
}
window.toggleChat = toggleChat;

function appendMsg(text, who) {
  const msgs = $("chatMessages");
  const div = document.createElement("div");
  div.className = `chat-msg ${who}`;
  div.innerHTML = `<strong>${who === "bot" ? "AirGuard AI" : "You"}:</strong> ${text}`;
  msgs.appendChild(div);
  msgs.scrollTop = msgs.scrollHeight;
}

async function sendChat() {
  const input = $("chatInput");
  const q = input.value.trim();
  if (!q) return;
  input.value = "";

  // Disable send while waiting
  const btn = $("chatSendBtn");
  if (btn) btn.disabled = true;

  appendMsg(q, "user");

  const thinking = document.createElement("div");
  thinking.className = "chat-msg bot";
  thinking.innerHTML = `<strong>AirGuard AI:</strong> <em>Thinking with Groq AI...</em>`;
  $("chatMessages").appendChild(thinking);
  $("chatMessages").scrollTop = $("chatMessages").scrollHeight;

  try {
    const res = await fetch(`${API}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: q, city: state.city, session_id: state.sessionId }),
    });
    const json = await res.json();
    const answer = json.data?.answer || "Sorry, I couldn't get an answer. Please try again.";
    const src    = json.data?.source ? `<span style="font-size:10px;color:#94a3b8;margin-left:6px">[${json.data.source}]</span>` : "";
    thinking.innerHTML = `<strong>AirGuard AI:</strong> ${answer}${src}`;
  } catch {
    thinking.innerHTML = "<strong>AirGuard AI:</strong> Network error. Please check your connection and try again.";
  } finally {
    if (btn) btn.disabled = false;
    $("chatMessages").scrollTop = $("chatMessages").scrollHeight;
  }
}
window.sendChat = sendChat;

function sendSuggestion(q) {
  $("chatInput").value = q;
  sendChat();
}
window.sendSuggestion = sendSuggestion;

// ── City & Geo ────────────────────────────────────────
function initCitySelect() {
  $("citySelect").addEventListener("change", e => {
    state.city = e.target.value;
    loadDashboard();
  });

  $("geoBtn").addEventListener("click", () => {
    if (!navigator.geolocation) {
      alert("Geolocation is not supported by this browser. Using demo data.");
      return;
    }
    navigator.geolocation.getCurrentPosition(
      pos => {
        // Map rough coords to nearest demo city
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;
        let nearest = "bhilai";
        const cities = {
          bhilai: [21.209, 81.428],
          raipur: [21.251, 81.630],
          delhi:  [28.614, 77.209],
          mumbai: [19.076, 72.878],
        };
        let minD = Infinity;
        for (const [k, [la, lo]] of Object.entries(cities)) {
          const d = Math.hypot(lat - la, lon - lo);
          if (d < minD) { minD = d; nearest = k; }
        }
        state.city = nearest;
        $("citySelect").value = nearest;
        loadDashboard();
      },
      () => {
        alert("Location permission denied. Using Bhilai as default.");
      }
    );
  });
}

// ── Theme Toggle ──────────────────────────────────────
function initTheme() {
  $("themeBtn").addEventListener("click", () => {
    state.darkMode = !state.darkMode;
    document.documentElement.setAttribute("data-theme", state.darkMode ? "dark" : "light");
    $("themeBtn").textContent = state.darkMode ? "☀️" : "🌙";
  });
}

// ── Refresh Button ────────────────────────────────────
function initRefresh() {
  $("refreshBtn").addEventListener("click", () => loadDashboard(true));
}

// ── Error Display ─────────────────────────────────────
function showError(msg) {
  $("alertBanner").style.display = "flex";
  $("alertText").textContent = "⚠️ " + msg;
}

// ── Init ──────────────────────────────────────────────
(async function init() {
  initDate();
  initTheme();
  initRefresh();
  initCitySelect();
  initProfileForm();

  // Wire Enter key for chat input
  const chatInput = $("chatInput");
  if (chatInput) {
    chatInput.addEventListener("keydown", e => {
      if (e.key === "Enter") sendChat();
    });
  }

  showSection("dashboard");
  await loadDashboard(true);
})();

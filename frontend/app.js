/**
 * TravelSaarthi (ट्रैवल सारथी) - Frontend Application Core
 * High-performance vanilla JS state machine, Leaflet map renderer,
 * and adaptive agent orchestrator client.
 */

// Application State
const state = {
  itinerary: null,
  trace: [],
  replanResult: null,
  chatHistory: [],
  map: null,
  mapMarkers: [],
  mapPolylines: [],
  allPlaces: [],
  isLoading: false
};

// Day Route Color Palette
const DAY_PALETTE = {
  1: { pin: '#2563eb', line: '#3b82f6', label: 'Day 1' },
  2: { pin: '#059669', line: '#10b981', label: 'Day 2' },
  3: { pin: '#7c3aed', line: '#8b5cf6', label: 'Day 3' },
  4: { pin: '#ea580c', line: '#f97316', label: 'Day 4' }
};

// Currency Formatter
function formatINR(amount) {
  if (amount === null || amount === undefined) return '₹0';
  const val = Math.round(amount);
  return '₹' + val.toLocaleString('en-IN');
}

// Category Icons
function getCategoryIcon(cat, type) {
  const c = (cat || '').toLowerCase();
  if (c.includes('heritage') || c.includes('fort') || c.includes('palace')) return '🏰';
  if (c.includes('museum') || c.includes('gallery')) return '🏛️';
  if (c.includes('food') || c.includes('restaurant') || c.includes('cafe')) return '🍛';
  if (c.includes('shopping') || c.includes('bazaar') || c.includes('market')) return '🛍️';
  if (c.includes('spiritual') || c.includes('temple')) return '🛕';
  if (c.includes('nature') || c.includes('lake') || c.includes('garden')) return '🌿';
  if (type === 'indoor') return '🏢';
  return '📍';
}

// Weather Icons
function getWeatherIcon(cond) {
  const c = (cond || '').toLowerCase();
  if (c.includes('rain') || c.includes('shower')) return '🌧️';
  if (c.includes('thunder') || c.includes('storm')) return '⛈️';
  if (c.includes('cloud')) return '⛅';
  if (c.includes('clear') || c.includes('sun')) return '☀️';
  return '🌤️';
}

// Initialize Map
function initMap() {
  const mapElement = document.getElementById('map-container');
  if (!mapElement) return;

  if (!state.map) {
    state.map = L.map('map-container', {
      zoomControl: true,
      attributionControl: false
    }).setView([26.9124, 75.7873], 12);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 19
    }).addTo(state.map);
  }
}

// Render Map Markers & Routes
function renderMapItinerary(itinerary) {
  if (!state.map || !itinerary || !itinerary.days) return;

  // Clear existing layers
  state.mapMarkers.forEach(m => state.map.removeLayer(m));
  state.mapPolylines.forEach(p => state.map.removeLayer(p));
  state.mapMarkers = [];
  state.mapPolylines = [];

  const latLngs = [];

  itinerary.days.forEach(day => {
    const colorInfo = DAY_PALETTE[day.day] || { pin: '#2563eb', line: '#3b82f6' };
    const dayPoints = [];

    day.activities.forEach((act, idx) => {
      const pt = [act.lat, act.lon];
      dayPoints.push(pt);
      latLngs.push(pt);

      const customIcon = L.divIcon({
        className: 'custom-map-pin',
        html: `
          <div style="
            background: ${colorInfo.pin};
            color: white;
            font-size: 11px;
            font-weight: 800;
            width: 26px;
            height: 26px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            border: 2px solid white;
            box-shadow: 0 4px 10px rgba(0,0,0,0.4);
          ">${idx + 1}</div>
        `,
        iconSize: [26, 26],
        iconAnchor: [13, 13]
      });

      const popupHtml = `
        <div style="font-family: inherit; width: 220px; padding: 4px;">
          <div style="font-size: 11px; font-weight: 700; color: ${colorInfo.pin}; text-transform: uppercase;">
            Day ${day.day} • Stop #${idx + 1} (${act.time})
          </div>
          <div style="font-size: 14px; font-weight: 700; color: #0f172a; margin: 4px 0;">
            ${act.name}
          </div>
          <div style="font-size: 11.5px; color: #475569; margin-bottom: 4px;">
            ${act.type === 'indoor' ? '🏢 Indoor' : '🌲 Outdoor'} • ${act.cost > 0 ? formatINR(act.cost) + '/person' : 'Free Entry'}
          </div>
          <div style="font-size: 10.5px; color: #64748b;">
            ⏱️ ${act.duration_hr}h • ⏰ ${act.opening_time} - ${act.closing_time}
          </div>
        </div>
      `;

      const marker = L.marker(pt, { icon: customIcon })
        .bindPopup(popupHtml)
        .addTo(state.map);

      state.mapMarkers.push(marker);
    });

    // Draw route line
    if (dayPoints.length > 1) {
      const poly = L.polyline(dayPoints, {
        color: colorInfo.line,
        weight: 3.5,
        opacity: 0.85,
        dashArray: '6, 8'
      }).addTo(state.map);
      state.mapPolylines.push(poly);
    }
  });

  if (latLngs.length > 0) {
    const bounds = L.latLngBounds(latLngs);
    state.map.fitBounds(bounds, { padding: [40, 40] });
  }
}

// Render Itinerary Cards
function renderItinerary(itinerary) {
  const container = document.getElementById('itinerary-container');
  if (!container) return;

  if (!itinerary || !itinerary.days || itinerary.days.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 40px; color: var(--text-muted);">
        <div style="font-size: 40px; margin-bottom: 10px;">🧭</div>
        <div style="font-size: 15px; font-weight: 600;">No active trip plan yet.</div>
        <div style="font-size: 12px; margin-top: 4px;">Click <b>✨ Demo Trip</b> or enter trip details in chat.</div>
      </div>
    `;
    return;
  }

  let html = '';
  itinerary.days.forEach(day => {
    const wIcon = getWeatherIcon(day.weather.condition);
    const rainyClass = day.weather.is_rainy ? 'weather-rainy' : '';

    let activitiesHtml = '';
    day.activities.forEach(act => {
      const cIcon = getCategoryIcon(act.category, act.type);
      const totalCost = act.cost * (itinerary.trip.people || 4);
      const costText = act.cost > 0 ? `${formatINR(act.cost)} × ${itinerary.trip.people} = ${formatINR(totalCost)}` : 'Free Entry';

      activitiesHtml += `
        <div class="activity-item">
          <div class="act-left">
            <div class="act-time-badge">${act.time}</div>
            <div>
              <div class="act-title">${cIcon} ${act.name}</div>
              <div class="act-meta">
                <span>${act.type === 'indoor' ? '🏢 Indoor' : '🌲 Outdoor'}</span>
                <span>•</span>
                <span>⏱️ ${act.duration_hr}h</span>
                <span>•</span>
                <span>⏰ ${act.opening_time} - ${act.closing_time}</span>
                <span>•</span>
                <span>⭐ Priority ${act.priority}/5</span>
              </div>
            </div>
          </div>
          <div class="act-cost-badge">${costText}</div>
        </div>
      `;
    });

    html += `
      <div class="day-card">
        <div class="day-header">
          <div>
            <div class="day-name">${day.date_label}</div>
            <div class="day-theme">Theme: ${day.theme}</div>
          </div>
          <div>
            <span class="weather-badge ${rainyClass}">
              ${wIcon} ${day.weather.condition} • ${day.weather.temp}°C (Rain: ${day.weather.rain_prob}%)
            </span>
          </div>
        </div>
        <div class="activity-list">
          ${activitiesHtml}
        </div>
        ${day.notes ? `<div style="font-size: 12px; color: var(--accent-cyan); margin-top: 8px;">💡 <i>${day.notes}</i></div>` : ''}
      </div>
    `;
  });

  container.innerHTML = html;
}

// Render Financial Metrics & Expense Breakdown
function renderBudgetMetrics(itinerary) {
  if (!itinerary || !itinerary.budget_breakdown) return;
  const b = itinerary.budget_breakdown;

  document.getElementById('metric-total-budget').innerText = formatINR(b.budget);
  document.getElementById('metric-estimated-spent').innerText = formatINR(b.total);
  document.getElementById('metric-remaining-buffer').innerText = formatINR(b.remaining);
  document.getElementById('metric-utilization').innerText = `${b.percentage_used}%`;

  const expenseContainer = document.getElementById('expense-pills-container');
  if (expenseContainer) {
    expenseContainer.innerHTML = `
      <div class="expense-pill">🚆 Transport: <strong>${formatINR(b.transport)}</strong></div>
      <div class="expense-pill">🏨 Stay (${itinerary.trip.days - 1}N): <strong>${formatINR(b.stay)}</strong></div>
      <div class="expense-pill">🍛 Dining: <strong>${formatINR(b.food)}</strong></div>
      <div class="expense-pill">🎟️ Entry Tickets: <strong>${formatINR(b.activities)}</strong></div>
      <div class="expense-pill">🚕 Local Transit: <strong>${formatINR(b.local_travel)}</strong></div>
    `;
  }
}

// Render Replan "Why Changed?" Banner
function renderReplanBanner(result) {
  const container = document.getElementById('replan-banner-container');
  if (!container) return;

  if (!result) {
    container.innerHTML = '';
    return;
  }

  let diffsHtml = '';
  if (result.changes && result.changes.length > 0) {
    result.changes.forEach(chg => {
      const badgeClass = `diff-${chg.change_type}`;
      diffsHtml += `
        <div class="diff-item">
          <span class="diff-badge ${badgeClass}">Day ${chg.day} • ${chg.change_type.toUpperCase()}</span>
          <div style="font-size: 13px; font-weight: 700; color: #fff;">${chg.activity_name}</div>
          <div style="font-size: 11.5px; color: #94a3b8; margin-top: 3px;">${chg.details}</div>
        </div>
      `;
    });
  }

  container.innerHTML = `
    <div class="why-changed-card">
      <div class="why-header">
        <div class="why-title">✨ Why did TravelSaarthi adapt your plan? (क्यों बदला आपका प्लान?)</div>
        <div class="why-tag">${result.event_classified}</div>
      </div>
      <div class="why-body-hinglish">
        <b>🗣️ Hinglish Rationale:</b> ${result.hinglish_explanation}
      </div>
      <div class="why-body-english">
        <b>📝 Technical Summary:</b> ${result.explanation}
      </div>
      ${diffsHtml ? `<div class="diff-grid">${diffsHtml}</div>` : ''}
    </div>
  `;
}

// Render Trace Logs Timeline
function renderTrace(traceSteps) {
  const container = document.getElementById('trace-timeline-container');
  if (!container) return;

  if (!traceSteps || traceSteps.length === 0) {
    container.innerHTML = `<div style="font-size: 12px; color: var(--text-muted); text-align: center; padding: 20px;">Agent is waiting for inputs...</div>`;
    return;
  }

  let html = '';
  traceSteps.forEach(t => {
    const statusClass = t.status || 'info';
    html += `
      <div class="trace-node ${statusClass}">
        <div class="trace-header">
          <span>${t.icon || '🧠'}</span>
          <span>${t.step}</span>
          ${t.tool_called ? `<span class="trace-tool">🔧 ${t.tool_called}</span>` : ''}
        </div>
        <div class="trace-detail">${t.detail}</div>
      </div>
    `;
  });

  container.innerHTML = html;
  container.scrollTop = container.scrollHeight;
}

// Render Chat Messages
function renderChat(messages, clarificationObj = null) {
  const container = document.getElementById('chat-messages-container');
  if (!container) return;

  let html = '';
  messages.forEach(msg => {
    const isUser = msg.role === 'user';
    html += `
      <div class="chat-bubble ${isUser ? 'chat-user' : 'chat-agent'}">
        ${msg.text.replace(/\n/g, '<br>')}
      </div>
    `;
  });

  // Render quick clarification chips if waiting
  if (clarificationObj) {
    html += `
      <div class="clarification-chips">
        <div class="chip" onclick="sendQuickChoice('Pure Veg + Relaxed Pace + Parents saath hain')">🥦 Pure Veg + Relaxed</div>
        <div class="chip" onclick="sendQuickChoice('Non-Veg + Moderate Pace')">🍗 Non-Veg + Moderate</div>
        <div class="chip" onclick="sendQuickChoice('Packed Fast Pace')">⚡ Fast / Packed Pace</div>
      </div>
    `;
  }

  container.innerHTML = html;
  container.scrollTop = container.scrollHeight;
}

// Send User Message to Backend API
async function sendMessage(text) {
  if (!text || !text.trim()) return;

  state.chatHistory.push({ role: 'user', text: text.trim() });
  renderChat(state.chatHistory);

  const inputEl = document.getElementById('chat-input');
  if (inputEl) inputEl.value = '';

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text.trim(), session_id: 'default' })
    });

    if (!res.ok) throw new Error('Network response was not ok');
    const data = await res.json();

    if (data.reply) {
      state.chatHistory.push({ role: 'agent', text: data.reply });
      renderChat(state.chatHistory, data.type === 'clarification' ? data : null);
    }

    if (data.itinerary) {
      state.itinerary = data.itinerary;
      renderItinerary(data.itinerary);
      renderBudgetMetrics(data.itinerary);
      renderMapItinerary(data.itinerary);
    }

    if (data.replan_result) {
      state.replanResult = data.replan_result;
      renderReplanBanner(data.replan_result);
    }

    if (data.trace) {
      state.trace = data.trace;
      renderTrace(data.trace);
    }
  } catch (err) {
    console.error('Chat error:', err);
    state.chatHistory.push({ role: 'agent', text: '⚠️ Connection error. Please ensure the backend server is running.' });
    renderChat(state.chatHistory);
  }
}

function sendQuickChoice(choiceText) {
  sendMessage(choiceText);
}

// Trigger Pre-Configured Demo Scenarios
async function triggerScenario(type) {
  if (type === 'demo') {
    sendMessage('3 din, ₹15,000, Delhi se Jaipur, family trip, 4 log. Veg khana aur relaxed pace.');
    return;
  }

  let endpointPayload = {};
  if (type === 'weather') {
    endpointPayload = {
      event_type: 'weather',
      day_affected: 2,
      description: 'Day 2 ka weather kharab hai aur heavy rain expected hai.'
    };
  } else if (type === 'delay') {
    endpointPayload = {
      event_type: 'delay',
      delay_hours: 2.0,
      description: 'Inbound train 2 ghante late chal rahi hai.'
    };
  } else if (type === 'budget') {
    endpointPayload = {
      event_type: 'budget',
      reduction_amount: 2000.0,
      description: 'Budget ₹2,000 kam ho gaya hai.'
    };
  } else if (type === 'fatigue') {
    endpointPayload = {
      event_type: 'fatigue',
      description: 'Family aur elders thak gaye hain, schedule relaxed karo.'
    };
  }

  try {
    const res = await fetch('/api/replan', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(endpointPayload)
    });

    const data = await res.json();
    if (data.itinerary) {
      state.itinerary = data.itinerary;
      renderItinerary(data.itinerary);
      renderBudgetMetrics(data.itinerary);
      renderMapItinerary(data.itinerary);
    }
    if (data.replan_result) {
      state.replanResult = data.replan_result;
      renderReplanBanner(data.replan_result);
      state.chatHistory.push({ role: 'agent', text: data.replan_result.hinglish_explanation });
      renderChat(state.chatHistory);
    }
    if (data.trace) {
      state.trace = data.trace;
      renderTrace(data.trace);
    }
  } catch (err) {
    console.error('Scenario error:', err);
  }
}

// Event Listeners on Load
document.addEventListener('DOMContentLoaded', () => {
  initMap();

  // Chat input submit
  const inputEl = document.getElementById('chat-input');
  const sendBtn = document.getElementById('chat-send-btn');

  if (inputEl) {
    inputEl.addEventListener('keydown', e => {
      if (e.key === 'Enter') {
        sendMessage(inputEl.value);
      }
    });
  }

  if (sendBtn) {
    sendBtn.addEventListener('click', () => {
      if (inputEl) sendMessage(inputEl.value);
    });
  }

  // Welcome message in chat
  state.chatHistory.push({
    role: 'agent',
    text: 'नमस्ते! मैं हूँ <b>TravelSaarthi</b> — आपका AI यात्रा सारथी। अपना ट्रिप प्लान करने के लिए लिखें, या ऊपर <b>✨ Demo Trip</b> बटन दबाएं!'
  });
  renderChat(state.chatHistory);
});

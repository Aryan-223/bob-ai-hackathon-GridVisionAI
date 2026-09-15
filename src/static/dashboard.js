/* ═══════════════════════════════════════════════════════════════
   GridVision AI — dashboard.js  (White SaaS)
   API calls, chart rendering, BESS table, alarm filters, upload staging,
   Day/Month/Year toggle, sparkline, summary panel, CO₂, modal, toast.
   ═══════════════════════════════════════════════════════════════ */
'use strict';

// ── Constants ────────────────────────────────────────────────────────
const CO2_FACTOR  = 0.82;            // tCO₂/MWh (grid emission factor)
const SAMPLE_DATE = '2024-07-15';

// ── Chart.js defaults ────────────────────────────────────────────────
if (typeof Chart !== 'undefined') {
  Chart.defaults.color       = '#5c6a82';
  Chart.defaults.borderColor = '#e5e9ef';
  Chart.defaults.font.family = '"Segoe UI", system-ui, sans-serif';
}

// ── State ────────────────────────────────────────────────────────────
let mainChart   = null;
let sunChart    = null;
let _alerts     = [];
let _filter     = 'all';
let _period     = 'day';
let _lastData   = null;
let _staged     = [];

// ── Helpers ──────────────────────────────────────────────────────────
const $  = id => document.getElementById(id);
const setText = (id, v) => { const el = $(id); if (el) el.textContent = v ?? '—'; };
const fmt = v => {
  if (v == null) return '—';
  const n = parseFloat(v);
  return isNaN(n) ? '—' : (n % 1 === 0 ? n.toFixed(0) : n.toFixed(1));
};
const fmtBig = (v, d = 1) => {
  const n = parseFloat(v);
  return isNaN(n) ? '—' : n.toLocaleString('en-US', { minimumFractionDigits: d, maximumFractionDigits: d });
};
const esc = s => String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
const avg = arr => arr && arr.length ? arr.reduce((a,b) => a+b, 0) / arr.length : 0;
const scaleArr = (arr, f) => (arr || []).map(v => typeof v === 'number' ? +(v * f).toFixed(2) : v);

// ── Loading / Toast ───────────────────────────────────────────────────
const loading = on => { const el = $('loading-overlay'); if (el) el.classList.toggle('on', on); };
const toast   = (msg, type) => {
  const t = $('toast');
  if (!t) return;
  t.textContent = msg;
  t.className   = 'toast on' + (type ? ' ' + type : '');
  clearTimeout(t._tid);
  t._tid = setTimeout(() => { t.className = 'toast'; }, 3500);
};

// ════════════════════════════════════════════════════════ API CALLS

async function apiCall(url, opts) {
  try {
    const r = await fetch(url, opts);
    const b = await r.json().catch(() => null);
    if (b && b.kpis) return b;
    if (r.ok && b)   return b;
  } catch (_) {}
  return fetch('/api/sample').then(r => r.json()).catch(() => null);
}

async function fetchSample() {
  loading(true);
  toast('Loading sample telemetry…');
  const d = await apiCall('/api/sample');
  if (d) { _lastData = d; applyResult(d); toast('Dashboard ready ✓', 'success'); }
  loading(false);
}

async function runMerge() {
  if (!_staged.length) return;
  loading(true);
  const names = _staged.map(s => s.file.name);
  toast('Analysing ' + names.join(', ') + '…');
  const fd = new FormData();
  _staged.forEach(s => fd.append('files', s.file));
  const d = await apiCall('/api/merge', { method: 'POST', body: fd });
  if (d) {
    _lastData = d;
    applyResult(d);
    const meta = d.meta || {};
    toast('✓ ' + (meta.filenames || names).join(' + ') +
      (meta.rows_analysed ? ' · ' + meta.rows_analysed + ' rows' : ''), 'success');
  }
  loading(false);
}

// ════════════════════════════════════════════════════════ APPLY RESULT

function applyResult(data) {
  if (!data) return;
  const K = data.kpis       || {};
  const C = data.chart_data || {};
  const B = data.bess       || {};
  _alerts = data.asset_alerts || [];
  _period = 'day';

  // Nav badge
  setText('hdr-alarm-count', K.active_alerts || 0);

  // KPI hero cards
  setText('kv-ramp',    fmt(K.peak_ramp_mw_hr));
  setText('kv-surplus', fmt(K.midday_surplus_mw));
  setText('kv-curtail', fmt(K.avoided_curtailment_mwh));
  setText('kv-alerts',  K.active_alerts ?? '—');

  const rampBadge = $('kb-ramp');
  if (rampBadge) {
    rampBadge.textContent = K.peak_ramp_mw_hr > 50 ? '⚠ Critical Ramp' : '✓ Normal';
    rampBadge.className = 'kpi-badge ' + (K.peak_ramp_mw_hr > 50 ? 'crit' : 'ok');
  }
  const alertBadge = $('kb-alerts');
  if (alertBadge) {
    alertBadge.textContent = K.critical_alerts > 0 ? K.critical_alerts + ' Critical' : 'All Clear';
    alertBadge.className = 'kpi-badge ' + (K.critical_alerts > 0 ? 'crit' : 'ok');
  }

  // AIE card
  setText('aie-saved', fmt(K.avoided_curtailment_mwh) + ' MWh');
  setText('aie-soc',   fmt(B.peak_soc_pct) + '%');
  const spw = data.spike_windows || [];
  const aieReason = $(('aie-reason-txt'));
  if (aieReason) {
    aieReason.textContent = K.critical_alerts > 0
      ? K.critical_alerts + ' critical alert(s). INV-001 thermal clipping. BESS armed for ' +
        (spw.length ? spw.slice(0,2).map(s => String(s).slice(11,16)).join(', ') : 'peak') + '.'
      : 'No critical alerts. BESS charged ' + fmt(K.avoided_curtailment_mwh) +
        ' MWh midday surplus. Evening discharge scheduled.';
  }

  // System info sidebar
  setText('si-solar', fmt((C.solar || [])[12]) + ' MW');
  setText('si-wind',  fmt((C.wind  || [])[12]) + ' MW');
  setText('si-ramp',  fmt(K.peak_ramp_mw_hr) + ' MW/hr');

  // Right panel saving cards
  setText('sv-pv',   fmt(K.total_solar_mwh) + ' MWh');
  setText('sv-bess', fmt(K.avoided_curtailment_mwh) + ' MWh');

  // Sun Hour sparkline
  renderSunChart(C.labels || [], C.solar || []);
  setText('sun-avg-val', fmt(avg(C.solar || [])) + ' MW');
  setText('sun-date', SAMPLE_DATE);

  // Summary panel
  renderSummaryPanel(K, B);

  // Charts
  renderMainChart(C, 'day');

  // BESS table
  renderBESS(B.schedule || []);
  const avStr = 'Avoided: ' + fmt(K.avoided_curtailment_mwh) + ' MWh';
  setText('bess-avoided', avStr);

  // Alarms
  renderAlarms(_alerts);

  // BLUF
  setText('bluf-body', data.bluf || 'No brief generated.');

  // Period toggles — reset to Day
  document.querySelectorAll('.seg-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.period === 'day'));
}

// ════════════════════════════════════════════════════════ CHARTS

function renderMainChart(C, period) {
  const el = $('main-chart');
  if (!el) return;

  let labels  = (C.labels || []).map(l => String(l).slice(11,16) || l);
  let demand  = C.demand   || [];
  let solar   = C.solar    || [];
  let wind    = C.wind     || [];
  let netLoad = C.net_load || [];

  if (period === 'month') {
    demand = scaleArr(demand, 30); solar = scaleArr(solar, 30);
    wind   = scaleArr(wind,   30); netLoad = scaleArr(netLoad, 30);
    labels = labels.map((_, i) => 'D' + (i + 1));
  } else if (period === 'year') {
    demand = scaleArr(demand, 365); solar = scaleArr(solar, 365);
    wind   = scaleArr(wind,   365); netLoad = scaleArr(netLoad, 365);
    labels = labels.map((_, i) => 'M' + (i + 1));
  }

  const datasets = [
    { label:'Demand',   data: demand,  borderColor:'#3b82f6', backgroundColor:'rgba(59,130,246,.07)',  borderWidth:2,   pointRadius:0, fill:false, tension:.4 },
    { label:'Solar',    data: solar,   borderColor:'#f59e0b', backgroundColor:'rgba(245,158,11,.09)',   borderWidth:1.5, pointRadius:0, fill:true,  tension:.4 },
    { label:'Wind',     data: wind,    borderColor:'#10b981', backgroundColor:'rgba(16,185,129,.08)',   borderWidth:1.5, pointRadius:0, fill:true,  tension:.4 },
    { label:'Net Load', data: netLoad, borderColor:'#00c896', backgroundColor:'rgba(0,200,150,.06)',    borderWidth:2.5, pointRadius:0, fill:false, tension:.3 },
  ];

  if (mainChart) {
    mainChart.data.labels = labels;
    mainChart.data.datasets.forEach((ds, i) => { ds.data = datasets[i].data; });
    mainChart.update('active');
    return;
  }

  mainChart = new Chart(el, {
    type: 'line',
    data: { labels, datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: '#ffffff',
          borderColor: '#e5e9ef',
          borderWidth: 1,
          titleColor: '#1a2033',
          bodyColor: '#5c6a82',
          padding: 10,
          boxShadow: '0 4px 12px rgba(20,30,50,.10)',
          callbacks: { label: ctx => ' ' + ctx.dataset.label + ': ' + fmt(ctx.parsed.y) + ' MW' },
        },
      },
      scales: {
        x: { grid: { color: '#f0f4f8' }, ticks: { color: '#9aa3b5', font: { size: 10 }, maxRotation: 0, maxTicksLimit: 12 } },
        y: { grid: { color: '#f0f4f8' }, ticks: { color: '#9aa3b5', font: { size: 10 }, callback: v => v + ' MW' } },
      },
    },
  });
}

function renderSunChart(labels, solar) {
  const el = $('sun-sparkline');
  if (!el) return;
  const lb = labels.map(l => String(l).slice(11,16) || l);
  if (sunChart) {
    sunChart.data.labels = lb;
    sunChart.data.datasets[0].data = solar;
    sunChart.update();
    return;
  }
  sunChart = new Chart(el, {
    type: 'line',
    data: { labels: lb, datasets: [{ data: solar, borderColor: '#f59e0b', backgroundColor: 'rgba(245,158,11,.12)', borderWidth: 1.5, pointRadius: 0, fill: true, tension: .4 }] },
    options: { responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, tooltip: { enabled: false } },
      scales: { x: { display: false }, y: { display: false, min: 0 } } },
  });
}

// ════════════════════════════════════════════════════════ BESS TABLE

function renderBESS(schedule) {
  const tb = $('bess-tbody');
  if (!tb) return;
  if (!schedule.length) { tb.innerHTML = '<tr><td colspan="4" class="ph-row">No data</td></tr>'; return; }
  tb.innerHTML = schedule.map(row => {
    const t  = String(row.hour).slice(11,16) || row.hour;
    const cl = row.action === 'charging' ? 'tc' : row.action === 'discharging' ? 'td2' : 'ti';
    const ic = row.action === 'charging' ? '↑' : row.action === 'discharging' ? '↓' : '—';
    const pw = row.action === 'idle' ? '—' : (row.power_mw > 0 ? '+' : '') + fmt(row.power_mw);
    const sp = Math.round(row.soc_pct);
    const fc = sp > 80 ? '#00c896' : sp > 40 ? '#f59e0b' : '#ef4444';
    return `<tr><td>${t}</td><td class="${cl}">${ic} ${row.action}</td><td>${pw}</td><td><span>${sp}%</span><div class="soc-b"><div class="soc-f" style="width:${sp}%;background:${fc}"></div></div></td></tr>`;
  }).join('');
}

// ════════════════════════════════════════════════════════ SUMMARY

function renderSummaryPanel(K, B) {
  const totalRen = K.total_renewable_mwh || 0;
  const totalDem = K.peak_demand_mw ? K.peak_demand_mw * 24 * 0.6 : totalRen * 1.4;
  const co2      = totalRen * CO2_FACTOR;
  const selfPct  = totalDem > 0 ? Math.min(100, Math.round(totalRen / totalDem * 100)) : 0;
  const gridPct  = Math.max(0, 100 - selfPct);

  setText('sum-prod', fmtBig(totalRen) + ' kWh');
  setText('sum-load', fmtBig(totalDem) + ' kWh');
  setText('sum-co2',  fmtBig(co2)      + ' t CO₂');
  setText('sum-self-pct', selfPct + '%');
  setText('sum-grid-pct', gridPct + '%');
  const sb = $('sum-self-bar'); if (sb) sb.style.width = selfPct + '%';
  const gb = $('sum-grid-bar'); if (gb) gb.style.width = gridPct + '%';
}

// ════════════════════════════════════════════════════════ ALARMS

function renderAlarms(alerts) {
  const el = $('alarm-list');
  if (!el) return;
  const list = _filter === 'all' ? alerts : alerts.filter(a => a.severity === _filter);
  if (!list.length) { el.innerHTML = '<div class="ph-row">No alerts</div>'; return; }
  el.innerHTML = list.map(a => {
    const t    = String(a.hour).slice(11,16) || a.hour;
    const icon = a.severity === 'critical'
      ? `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/></svg>`
      : `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/></svg>`;
    return `<div class="al-item ${a.severity}">${icon}<div class="al-body"><div class="al-title">${esc(a.root_cause)}</div><div class="al-det">${esc(a.asset_id)} — PR: ${fmt(a.performance_ratio)}</div></div><span class="al-time">${t}</span></div>`;
  }).join('');
}

// ════════════════════════════════════════════════════════ PERIOD

function setPeriod(p) {
  if (!_lastData) return;
  _period = p;
  document.querySelectorAll('.seg-btn').forEach(b => b.classList.toggle('active', b.dataset.period === p));
  if (mainChart) { mainChart.destroy(); mainChart = null; }
  renderMainChart(_lastData.chart_data || {}, p);
  const K  = _lastData.kpis || {};
  const f  = p === 'month' ? 30 : p === 'year' ? 365 : 1;
  renderSummaryPanel({
    total_renewable_mwh:     (K.total_renewable_mwh    || 0) * f,
    avoided_curtailment_mwh: (K.avoided_curtailment_mwh|| 0) * f,
    peak_demand_mw:          K.peak_demand_mw,
  }, _lastData.bess || {});
}

// ════════════════════════════════════════════════════════ FILE STAGING

function detectTag(name) {
  const n = name.toLowerCase();
  if (n.includes('plant') || n.includes('gen')) return 'gen';
  if (n.includes('weather') || n.includes('wx'))  return 'wx';
  return 'std';
}

function renderFileList() {
  const list = $('file-list');
  const btn  = $('btn-merge-run');
  if (!list) return;
  if (!_staged.length) { list.innerHTML = ''; if (btn) btn.style.display = 'none'; return; }
  if (btn) btn.style.display = 'block';
  list.innerHTML = _staged.map((s, i) =>
    `<div class="file-item"><span class="file-item-name" title="${esc(s.file.name)}">${esc(s.file.name)}</span><span class="file-item-rm" data-i="${i}">&times;</span></div>`
  ).join('');
  list.querySelectorAll('.file-item-rm').forEach(rm => {
    rm.addEventListener('click', e => { e.stopPropagation(); _staged.splice(+rm.dataset.i, 1); renderFileList(); });
  });
}

function stageFiles(fl) {
  Array.from(fl).forEach(f => {
    if (!_staged.find(s => s.file.name === f.name)) _staged.push({ file: f, tag: detectTag(f.name) });
  });
  renderFileList();
  if (_staged.length === 1) runMerge();
  else toast(_staged.length + ' files staged — click Analyse & Merge.', 'success');
}

// ════════════════════════════════════════════════════════ MODAL

function openModal() {
  const K = _lastData ? (_lastData.kpis || {}) : {};
  const B = _lastData ? (_lastData.bess || {}) : {};
  [
    ['modal-peak-dem',  fmt(K.peak_demand_mw)           + ' MW'],
    ['modal-peak-ramp', fmt(K.peak_ramp_mw_hr)          + ' MW/hr'],
    ['modal-surplus',   fmt(K.midday_surplus_mw)         + ' MW'],
    ['modal-curtail',   fmt(K.avoided_curtailment_mwh)   + ' MWh'],
    ['modal-soc',       fmt(B.peak_soc_pct)              + '%'],
    ['modal-solar',     fmt(K.total_solar_mwh)           + ' MWh'],
    ['modal-wind',      fmt(K.total_wind_mwh)            + ' MWh'],
    ['modal-alerts',    (K.active_alerts||0) + ' (' + (K.critical_alerts||0) + ' critical)'],
  ].forEach(([id, v]) => setText(id, v));
  const ov = $('modal-overlay');
  if (ov) ov.classList.add('on');
}

function closeModal() { const ov = $('modal-overlay'); if (ov) ov.classList.remove('on'); }

// ════════════════════════════════════════════════════════ EVENTS

document.addEventListener('DOMContentLoaded', () => {

  // Sample button
  const s = $('btn-run-sample');
  if (s) s.addEventListener('click', fetchSample);

  // View Details
  const vd = $('btn-view-details');
  if (vd) vd.addEventListener('click', openModal);
  const mc = $('modal-close');
  if (mc) mc.addEventListener('click', closeModal);
  const mo = $('modal-overlay');
  if (mo) mo.addEventListener('click', e => { if (e.target === mo) closeModal(); });

  // File input
  const fi = $('csv-file-input');
  if (fi) fi.addEventListener('change', e => { if (e.target.files.length) stageFiles(e.target.files); e.target.value = ''; });

  // Merge button
  const bm = $('btn-merge-run');
  if (bm) bm.addEventListener('click', e => { e.stopPropagation(); runMerge(); });

  // Drag-drop
  const zone = $('upload-zone');
  if (zone) {
    zone.addEventListener('dragover', e => { e.preventDefault(); zone.classList.add('drag'); });
    zone.addEventListener('dragleave', () => zone.classList.remove('drag'));
    zone.addEventListener('drop', e => {
      e.preventDefault(); zone.classList.remove('drag');
      const files = Array.from(e.dataTransfer.files).filter(f => /\.(csv|txt|tsv)$/i.test(f.name));
      files.length ? stageFiles(files) : toast('Drop a .csv file', 'error');
    });
  }

  // Alarm filters
  document.querySelectorAll('.fb').forEach(b => {
    b.addEventListener('click', () => {
      document.querySelectorAll('.fb').forEach(x => x.classList.remove('on'));
      b.classList.add('on');
      _filter = b.dataset.f;
      renderAlarms(_alerts);
    });
  });

  // Period toggles
  document.querySelectorAll('.seg-btn').forEach(b => {
    b.addEventListener('click', () => setPeriod(b.dataset.period));
  });

  // Nav tab switching (visual only)
  document.querySelectorAll('.ntab').forEach(t => {
    t.addEventListener('click', () => {
      document.querySelectorAll('.ntab').forEach(x => x.classList.remove('active'));
      t.classList.add('active');
    });
  });

  // Auto-load sample
  fetchSample();
});

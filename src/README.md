# Source Code — GridVision AI

This directory contains all source code for the GridVision AI dashboard.

## Structure

```
src/
├── app.py                  # Flask application entry point
│                           #   - GET  /          → serves index.html dashboard
│                           #   - GET  /api/health → health check
│                           #   - GET  /api/sample → pre-loaded sample day analysis
│                           #   - POST /api/analyze → single CSV upload
│                           #   - POST /api/merge   → multi-file CSV merge + analysis
│
├── analytics.py            # Core analytics engine (pure Python, no web dependencies)
│                           #   - normalize_columns()     — SCADA alias → standard keys
│                           #   - compute_net_load()      — demand − (solar + wind)
│                           #   - detect_spike_windows()  — ramp rate > 50 MW/hr
│                           #   - run_asset_diagnostics() — PR-based fault detection
│                           #   - optimise_bess()         — charge/discharge scheduler
│                           #   - generate_bluf()         — IBM Granite brief synthesis
│                           #   - run_analysis()          — single-file pipeline
│                           #   - run_analysis_multi()    — multi-file merge pipeline
│
├── requirements.txt        # Python package dependencies
├── .env.example            # Environment variable template (copy to .env, never commit .env)
│
├── templates/
│   └── index.html          # Dashboard HTML — clean markup, no inline CSS or JS
│                           #   Consumes JSON from /api/sample, /api/analyze, /api/merge
│                           #   JSON shape: kpis · chart_data · bess · asset_alerts ·
│                           #              spike_windows · bluf · meta
│
└── static/
    ├── dashboard.css       # Full white SaaS theme — all styles, no inline
    │                       #   CSS custom properties: --accent (#00c896), --blue (#3b82f6)
    │                       #   Card system, nav, chart, BESS table, alarm list, modal, toast
    │
    └── dashboard.js        # All dashboard logic — no inline scripts in HTML
                            #   fetchSample(), runMerge(), applyResult()
                            #   renderMainChart() with Day/Month/Year period toggle
                            #   renderSunChart() sparkline
                            #   renderBESS() table
                            #   renderSummaryPanel() with CO₂ = total_renewable_mwh × 0.82
                            #   renderAlarms() with All/Critical/Warning filter
                            #   openModal() / closeModal()
                            #   stageFiles() drag-and-drop multi-file upload staging
```

## Running the App

```bash
cd bob-ai-hackathon-Team/src
pip install -r requirements.txt
python app.py
# → http://localhost:5000
```

See [`../docs/setup-guide.md`](../docs/setup-guide.md) for full instructions including optional IBM watsonx.ai configuration.

## Environment Variables

Copy `.env.example` to `.env` — the app works without any variables set (uses pre-computed sample brief):

| Variable | Purpose | Default |
|---|---|---|
| `WATSONX_API_KEY` | IBM Cloud API key for live Granite inference | None (falls back to static brief) |
| `WATSONX_PROJECT_ID` | watsonx.ai project ID | None |
| `WATSONX_URL` | Regional endpoint | `https://us-south.ml.cloud.ibm.com` |
| `PORT` | Flask listen port | `5000` |
| `FLASK_DEBUG` | Enable hot-reload | `false` |

## API JSON Shape

All three endpoints (`/api/sample`, `/api/analyze`, `/api/merge`) return the same JSON structure:

```json
{
  "kpis": {
    "peak_demand_mw": 372.5,
    "peak_net_load_mw": 354.7,
    "min_net_load_mw": -35.0,
    "midday_surplus_mw": 35.0,
    "peak_ramp_mw_hr": 134.1,
    "avoided_curtailment_mwh": 30.6,
    "active_alerts": 1,
    "critical_alerts": 1,
    "total_solar_mwh": 1159.6,
    "total_wind_mwh": 454.3,
    "total_renewable_mwh": 1613.9
  },
  "chart_data": {
    "labels": ["2024-07-15 00:00", "..."],
    "demand": [210.5, "..."],
    "solar": [0.0, "..."],
    "wind": [18.2, "..."],
    "renewable": [18.2, "..."],
    "net_load": [192.3, "..."],
    "ramp_rate": [0.0, "..."],
    "soc_pct": [50.0, "..."]
  },
  "bess": {
    "schedule": [
      {"hour": "2024-07-15 00:00", "action": "idle", "power_mw": 0.0, "soc_mwh": 25.0, "soc_pct": 50.0}
    ],
    "total_avoided_curtailment_mwh": 30.6,
    "peak_soc_pct": 90.0,
    "bess_capacity_mwh": 50.0,
    "bess_max_power_mw": 15.0
  },
  "asset_alerts": [
    {"hour": "2024-07-15 13:00", "asset_id": "INV-001", "root_cause": "Inverter Thermal Clipping",
     "detail": "PR=0.60 (<0.70) | Inv Temp=91.5C. Thermal derating active.", "severity": "critical", "performance_ratio": 0.601}
  ],
  "spike_windows": ["2024-07-15 19:00", "2024-07-15 20:00"],
  "bluf": "BLUF - Grid Shift Operator Brief\n\nSITUATION: ...",
  "meta": {"files_merged": 1, "filenames": ["grid_telemetry.csv"], "rows_analysed": 24}
}
```

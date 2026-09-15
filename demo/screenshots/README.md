# Screenshots — GridVision AI Dashboard

This folder contains screenshots of the GridVision AI dashboard running with live sample telemetry data.

## Screenshot Inventory

| File | Description |
|---|---|
| `01-dashboard-overview.png` | Full dashboard on load — white SaaS theme, KPI hero row, AIE-DR green gradient card, energy chart, BESS table, alarm panel, BLUF brief |
| `02-energy-chart-detail.png` | Energy Generation & Net Load chart — 24-hour demand vs. solar/wind/net-load curves with Day/Month/Year period toggle |
| `03-bess-dispatch-table.png` | BESS Dispatch Schedule table — 24 hourly rows with charge/discharge actions, MW values, SoC% progress bars |
| `04-alarm-filters.png` | Alarm Records panel showing asset anomaly alerts with Critical/Warning severity filters and IBM Granite BLUF brief |
| `05-architecture-strip.png` | Architecture Data Flow strip — 8-node pipeline from CSV → Frontend → Flask → Analytics → BESS Optimizer → Agentic Synthesizer → IBM watsonx.ai Granite-3 |

## How to Reproduce

```bash
cd bob-ai-hackathon-Team/src
pip install -r requirements.txt
python app.py
# Open http://localhost:5000
# Click "Run Pre-loaded Sample Day"
```

All screenshots were taken at 1440×900 resolution in Chrome 124 with the sample day loaded.

## IBM Technology Visible

Screenshots 01 and 04 show the **IBM watsonx.ai — Granite 3** status pill in the navigation bar and the **"IBM Granite · AI Synthesised"** badge on the BLUF brief panel.
Screenshot 05 shows the full IBM watsonx.ai Granite-3 node highlighted in the architecture strip.

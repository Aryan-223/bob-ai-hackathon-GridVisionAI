# Setup Guide — GridVision AI

> Estimated time to first working demo: **under 2 minutes** on any machine with Python 3.10+.

---

## Prerequisites

Before you begin, ensure you have:

- [x] **Python 3.10 or higher** — check with `python --version`
- [x] **pip** — bundled with Python; update with `pip install --upgrade pip`
- [ ] *(Optional)* An **IBM Cloud account** with **watsonx.ai** access — only required for live AI brief generation. The dashboard works completely without it.

No Node.js, Docker, database, or cloud deployment is needed.

---

## Step 1 — Clone the Repository

```bash
git clone https://github.com/drijesh-ppatel/bob-ai-hackathon-GridVisionAI.git
cd bob-ai-hackathon-GridVisionAI/src
```

---

## Step 2 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, Pandas, NumPy, and the optional IBM watsonx-ai SDK. The total install takes roughly 30–60 seconds on a fresh environment.

If you prefer a virtual environment:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Step 3 — (Optional) Configure IBM watsonx.ai

If you want **live IBM Granite BLUF generation**, copy the environment template and fill in your credentials:

```bash
cp .env.example .env
```

Then edit `.env`:

```
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
```

| Variable | Description | Required for live AI |
|---|---|---|
| `WATSONX_API_KEY` | IBM Cloud API key with watsonx.ai access | Yes |
| `WATSONX_PROJECT_ID` | Your watsonx.ai project ID | Yes |
| `WATSONX_URL` | Regional watsonx endpoint (default: us-south) | Yes |
| `PORT` | Flask listen port (default: 5000) | No |
| `FLASK_DEBUG` | Set to `true` for hot-reload (default: false) | No |

> **If you skip this step entirely**, the dashboard falls back to a high-quality pre-computed BLUF brief. All KPI cards, charts, BESS table, alarm list, and Summary panel work 100% without any API key.

---

## Step 4 — Run the Application

```bash
python app.py
```

Expected output:

```
[GridVision AI] http://0.0.0.0:5000  (sample: .../data/grid_telemetry.csv)
 * Running on http://0.0.0.0:5000
```

Open **http://localhost:5000** in any modern browser (Chrome, Firefox, Edge, Safari).

---

## Step 5 — Verify the Dashboard Works

1. The page loads showing the white SaaS dashboard with the top navigation, KPI cards, and chart area.
2. Click **"Run Pre-loaded Sample Day"** in the left sidebar.
3. Within 1–2 seconds, all widgets populate:
   - **KPI hero row** shows Peak Ramp, Midday Surplus, Avoided Curtailment, Active Alerts
   - **Energy chart** renders the 24-hour demand vs. solar/wind/net-load curves
   - **BESS Dispatch Schedule** table fills with 24 hourly rows
   - **Alarm Records** panel shows asset anomaly alerts
   - **Operator BLUF Brief** panel shows the IBM Granite generated or pre-computed brief
   - **Summary panel** shows System Production, Load Consumption, and CO₂ Reduction

You can also upload your own grid telemetry CSV via the drag-and-drop zone in the sidebar.

---

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `GET /` | GET | Serves the dashboard HTML |
| `GET /api/health` | GET | Returns `{"status":"ok","service":"GridVision AI"}` |
| `GET /api/sample` | GET | Returns pre-loaded sample day analysis JSON |
| `POST /api/analyze` | POST | Accepts single CSV file upload, returns analysis JSON |
| `POST /api/merge` | POST | Accepts multiple CSV files, merges and analyses |

Quick test:

```bash
curl http://localhost:5000/api/health
# {"service":"GridVision AI","status":"ok","version":"1.0.0"}

curl http://localhost:5000/api/sample | python -m json.tool | head -30
```

---

## Running Tests

```bash
# From bob-ai-hackathon-Team/src/
python -c "
from app import app
c = app.test_client()
assert c.get('/api/health').status_code == 200
assert c.get('/api/sample').status_code == 200
assert c.get('/').status_code == 200
data = c.get('/api/sample').get_json()
assert 'kpis' in data and 'chart_data' in data and 'bess' in data
print('All smoke tests passed.')
"
```

---

## Supported CSV Formats

GridVision AI accepts CSV files from multiple SCADA / data sources with flexible column name matching:

| Internal Field | Accepted Column Names |
|---|---|
| `grid_demand_mw` | `demand`, `load`, `MW`, `grid_demand_mw`, `DEMAND_MW`, `consumption` |
| `actual_solar_mw` | `solar`, `solar_mw`, `pv_power`, `PV`, `solar_gen`, `PV_MW` |
| `actual_wind_mw` | `wind`, `wind_mw`, `wind_power`, `Wind`, `wind_generation` |
| `timestamp` | `timestamp`, `datetime`, `time`, `date`, `hour` |
| `solar_irradiance_wm2` | `irradiance`, `GHI`, `ghi`, `solar_irradiance` |
| `inverter_temp_c` | `inverter_temp`, `inv_temp`, `InverterTemp` |

The built-in sample uses `data/grid_telemetry.csv` — a clean 24-hour SCADA log for 2024-07-15.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Run `pip install -r requirements.txt` from the `src/` directory |
| `ModuleNotFoundError: No module named 'pandas'` | Same as above — all deps are in `requirements.txt` |
| Port 5000 already in use | Set `PORT=5001` in your `.env` or run `PORT=5001 python app.py` |
| Dashboard loads but charts are blank | Check browser console — likely a Chart.js CDN load failure; requires internet access |
| BLUF brief shows static text | No `WATSONX_API_KEY` set — this is expected; copy `.env.example` to `.env` and add your key |
| `watsonx 401 Unauthorized` | Verify `WATSONX_API_KEY` is correct and the key has watsonx.ai service access |
| CSV upload returns sample data | Your CSV column names may not match — see the Supported CSV Formats table above |
| Windows: `python` not found | Try `py app.py` or ensure Python is on your PATH |

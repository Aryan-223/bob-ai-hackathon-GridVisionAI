# GridVision AI — Intelligent Grid Load Optimisation & Renewable Diagnostic Advisor

[![Validate Submission](https://github.com/drijesh-ppatel/bob-ai-hackathon-Team/actions/workflows/validate.yml/badge.svg)](https://github.com/drijesh-ppatel/bob-ai-hackathon-Team/actions/workflows/validate.yml)

> **GridVision AI** turns 24-hour SCADA telemetry into actionable grid-shift operator intelligence — combining physics-informed renewable diagnostics, BESS curtailment optimisation, and IBM watsonx.ai Granite-powered BLUF briefings in a zero-dependency SaaS dashboard.

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | GridVision-AI |
| **Track** | AI |
| **Team Lead** | Aryan Jariwala — 25ee015@charusat.edu.in |
| **Members** | Meet · Shreya · Keyushi |

---

## 🎯 Problem Statement

Grid operators and renewable energy asset managers face extreme net-load volatility and operational uncertainty as intermittent solar and wind generation collides with steep consumer demand ramps. Without coordinated real-time decision support, massive amounts of clean power are curtailed — over 8 TWh shut off in the US in 2023 alone — while hardware-level faults in solar inverters and wind turbines go undetected for weeks, silently eroding generation capacity and threatening grid stability.

---

## 💡 Solution

GridVision AI is an end-to-end grid load optimisation and renewable diagnostic advisor that ingests 24-hour SCADA telemetry, computes net load and ramp-rate forecasts, runs physics-informed Performance Ratio diagnostics to isolate asset-level faults with root-cause labels, optimises Battery Energy Storage System dispatch to eliminate curtailment, and leverages IBM watsonx.ai Granite-3 to synthesise all quantitative outputs into shift-ready Bottom-Line-Up-Front (BLUF) operational briefs — all rendered in a responsive white-theme SaaS dashboard that judges can run with a single command.

---

## ✨ Key Features

- **Net Load & Ramp Forecasting** — Computes 24-hour net load curves and flags evening demand spikes exceeding 50 MW/hr before they strain grid stability.
- **Autonomous BESS Curtailment Optimisation** — Dynamically schedules charge cycles during midday renewable surplus and discharge during peak ramp windows to eliminate clean-energy waste.
- **Physics-Informed Asset Anomaly Diagnosis** — Cross-references solar irradiance and inverter telemetry against Performance Ratio thresholds to flag root causes: thermal clipping, panel soiling, and pitch degradation.
- **Agentic BLUF Operator Briefs via IBM Granite** — Forwards a pre-aggregated structured JSON to `ibm/granite-3-8b-instruct` through watsonx.ai, receiving a shift-ready operational memo in under 2 seconds.
- **Interactive White-Theme SaaS Dashboard** — Live Chart.js 24-hour generation vs. load chart, BESS dispatch table, alarm severity filters, Day/Month/Year toggle, Sun Hour sparkline, CO₂ reduction summary, drag-and-drop CSV ingest — all in a single Flask + Jinja + vanilla JS page with no build step.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | Python 3.10+, HTML5, CSS3, JavaScript (ES2022) |
| **Frameworks** | Flask 3.0, Pandas 2.0, NumPy 1.26, Chart.js 4.4 |
| **IBM Technologies** | IBM watsonx.ai (granite-3-8b-instruct), IBM Bob IDE (Plan + Agent modes) |
| **Databases** | None — stateless, CSV-driven |
| **Other** | ibm-watsonx-ai SDK, python-dotenv, GitHub Actions (CI validation) |

---

## 📁 Repository Structure

```
bob-ai-hackathon-Team/
├── src/
│   ├── app.py                  # Flask backend — routes, fallback payload, file upload
│   ├── analytics.py            # Core analytics — net load, ramp, BESS, PR diagnostics
│   ├── requirements.txt        # Python dependencies
│   ├── .env.example            # Environment variable template
│   ├── templates/
│   │   └── index.html          # Dashboard markup (references external CSS + JS)
│   └── static/
│       ├── dashboard.css       # White SaaS theme — all styles
│       └── dashboard.js        # All dashboard logic — API calls, charts, filters
├── data/
│   └── grid_telemetry.csv      # 24-hour sample SCADA telemetry (2024-07-15)
├── docs/
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/
│   ├── screenshots/            # Dashboard screenshots
│   ├── demo-video-link.txt     # Link to walkthrough video
│   └── live-demo-url.txt       # NOT DEPLOYED — run locally
├── presentation/
│   └── slides.pdf              # Slide deck
└── submission.yaml             # Structured hackathon metadata
```

---

## ⚡ How to Run

No Docker, no build step, no cloud account required for the base demo.

```bash
# 1. Clone the repo
git clone https://github.com/drijesh-ppatel/bob-ai-hackathon-Team.git
cd bob-ai-hackathon-Team/src

# 2. Install Python dependencies (Python 3.10+ required)
pip install -r requirements.txt

# 3. (Optional) Configure watsonx.ai for live BLUF generation
cp .env.example .env
# Edit .env — set WATSONX_API_KEY and WATSONX_PROJECT_ID
# If skipped, the dashboard uses a high-quality pre-computed brief

# 4. Run the app
python app.py
```

Open **http://localhost:5000** in any modern browser.  
Click **"Run Pre-loaded Sample Day"** to populate every widget instantly.

For full details and troubleshooting see [`docs/setup-guide.md`](docs/setup-guide.md).

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | NOT DEPLOYED — run locally per setup guide |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [presentation/slides.pdf](presentation/) |

---

## ⚠️ Known Limitations

- **No live watsonx.ai without a key** — BLUF brief falls back to a high-quality pre-computed static memo when `WATSONX_API_KEY` is absent from `.env`; all other dashboard features are unaffected.
- **Period toggle uses scaled sample data** — the Day/Month/Year segmented toggle multiplies the 24-hour sample rather than loading real historical time series; a production system would query a time-series database.
- **Fixed PR capacity constants** — Performance Ratio diagnostics use a single fleet-wide 80 MW-peak solar capacity assumption rather than per-asset rated capacity from a CMMS.
- **No authentication** — single-operator demo tool; multi-user sessions, role-based access, and production hardening are out of scope for the hackathon.
- **Browser-only; no mobile breakpoint below 880px** — the dashboard is optimised for 1280px+ widescreen operator monitors.

---

## 🏅 What We're Most Proud Of

The **agentic synthesis pipeline** is our strongest piece of work. Rather than naively streaming thousands of raw CSV rows into the LLM, our analytics engine pre-aggregates the entire 24-hour grid state into a dense structured JSON summary — peak ramp windows, curtailment volumes, asset alert codes, BESS schedule — and forwards exactly that to IBM Granite. The model returns a clean, multi-paragraph BLUF operational memo in under 2 seconds with near-zero hallucination risk. This pre-aggregation pattern is not just a hackathon convenience: it conserves watsonx Resource Units, respects token limits at production telemetry scale, and produces deterministic, operator-grade language every time.

We are equally proud that **the entire product runs with `python app.py`** — no Docker, no build pipeline, no cloud account, no database — and the dashboard auto-populates on first load using the pre-cached sample day. A judge can go from `git clone` to a fully populated professional dashboard in under 90 seconds.

---

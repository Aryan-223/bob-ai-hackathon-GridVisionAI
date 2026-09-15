# 🚀 GridVision-AI

> ⚠️ **Replace everything in l conte`[ ]` brackets with your actuant before submission.**

---

## 👥 Team

| Field | Value |
|---|---|
| **Team Name** | GridVision-AI |
| **Track** | [AI / DevOps / Sustainability / Open] |
| **Team Lead** | Aryan — 25ee015@charusat.edu.in |
| **Members** | Meet, Shreya, Keyushi |

---

## 🎯 Problem Statement

> In 2–3 sentences: What problem does your project solve? Who experiences this problem?

Grid operators and renewable energy asset managers face extreme net-load volatility and high operational uncertainty due to intermittent solar and wind generation coinciding with steep consumer demand ramps. Without coordinated, real-time decision support, massive amounts of clean power are curtailed—over ~8 TWh shut off in the US in 2023 alone—while sudden evening load spikes strain transmission stability and asset performance anomalies go undetected. Our solution solves this by forecasting demand spikes, detecting renewable asset anomalies with root-cause diagnoses, and generating automated load-balancing and curtailment-minimization plans for control room operators.

---

## 💡 Solution

> In 2–3 sentences: What did you build? How does it solve the problem above?

We built an end-to-end grid load optimization and renewable diagnostic advisor that integrates dual time-series forecasting with physical sensor telemetry analysis. The system uses predictive machine learning to detect upcoming demand ramps and renewable overgeneration, optimizes battery energy storage dispatch to absorb clean energy surplus and eliminate curtailment, and isolates asset-level faults using physics-informed performance ratio thresholds. It then leverages IBM foundation models to synthesize these quantitative outputs into actionable, real-time Bottom-Line-Up-Front (BLUF) operational briefs for transmission dispatchers.

---

## ✨ Key Features

- **Feature 1:** Dual-Horizon Net Load & Spike Forecasting — Predicts 24-hour gross electrical demand alongside solar and wind generation profiles to identify rapid evening net-load ramp events before they strain grid stability.
- **Feature 2:** Autonomous Curtailment Reduction & Storage Dispatch — Dynamically schedules Battery Energy Storage System (BESS) charge cycles during midday overgeneration windows to capture surplus green energy and discharge during peak demand hours.
- **Feature 3:** Physics-Informed Asset Anomaly & Root Cause Diagnosis — Continuously cross-references solar irradiance and wind telemetry against theoretical power curves to detect underperforming units and flag specific root causes like inverter thermal clipping or panel soiling.
- **Feature 4:** Agentic BLUF Operator Optimization Briefs — Leverages IBM foundation models to synthesize complex numerical forecasts, asset telemetry alerts, and dispatch schedules into structured, shift-ready Bottom-Line-Up-Front (BLUF) operational briefs.
- **Feature 5:** Interactive Operator Dashboard & Telemetry Ingestion — Provides an intuitive web interface with interactive generation-versus-load visualization, live asset alert monitors, and instant CSV telemetry upload support.

---

## 🛠️ Tech Stack

| Category | Technologies |
|---|---|
| **Languages** | [e.g., Python, TypeScript] |
| **Frameworks** | [e.g., FastAPI, React] |
| **IBM Technologies** | [e.g., watsonx.ai, IBM Bob, IBM Cloud] |
| **Databases** | [e.g., PostgreSQL, Redis] |
| **Other** | [e.g., Docker, GitHub Actions] |

---

## 📁 Repository Structure

```
├── src/                  # All source code
├── docs/                 # Written documentation
│   ├── problem-statement.md
│   ├── solution-overview.md
│   ├── architecture.md
│   └── setup-guide.md
├── demo/                 # Demo artifacts
│   ├── screenshots/      # App screenshots
│   └── demo-video-link.txt  # Link to demo video
├── presentation/         # Slide deck
└── submission.yaml       # Structured submission metadata
```

---

## ⚡ How to Run

> **Copy these exact steps from your [`docs/setup-guide.md`](docs/setup-guide.md)**

```bash
# 1. Clone the repo
git clone https://github.com/[your-repo].git
cd [your-repo]

# 2. Install dependencies
[your install command here]

# 3. Configure environment
cp .env.example .env
# Edit .env with your values

# 4. Run the project
[your run command here]
```

---

## 🖥️ Demo

| Artifact | Link |
|---|---|
| 📹 Demo Video | [See demo/demo-video-link.txt](demo/demo-video-link.txt) |
| 🌐 Live Demo | [See demo/live-demo-url.txt](demo/live-demo-url.txt) |
| 🖼️ Screenshots | [See demo/screenshots/](demo/screenshots/) |
| 📊 Presentation | [See presentation/slides.pdf](presentation/) |

---

## ⚠️ Known Limitations

> Be honest — judges appreciate transparency over overclaiming.

- [Limitation 1: e.g., "Authentication is mocked — not production-ready"]
- [Limitation 2: e.g., "Only tested on Chrome"]
- [Limitation 3: e.g., "Feature X is scaffolded but not fully implemented"]

---

## 🏅 What We're Most Proud Of

[Tell the judges what part of your submission is strongest and worth paying close attention to.]

---

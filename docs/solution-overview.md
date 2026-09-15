# Solution Overview

## What We Built

GridVision AI is an intelligent operations advisor built for electrical grid operators and renewable power plant managers. It acts as a co-pilot in the control room to solve two opposing daily challenges: wasting excess clean power at midday (curtailment) and struggling with rapid consumer electricity surges in the evening (load spikes). Instead of forcing engineers to manually cross-reference separate weather forecasts, power charts, and sensor logs across multiple screens, GridPulse AI continuously calculates net demand, diagnoses physical equipment issues (like overheating solar inverters), schedules battery storage to store surplus green energy, and uses IBM Granite foundation models to draft concise, shift-ready briefing notes.

## How It Works

[Explain the core mechanism step by step. A numbered list or simple flow works well here.]

1. Ingest & Normalize Telemetry: The operator uploads a 24-hour grid telemetry CSV or loads the pre-configured sample day; the backend maps various column naming formats into standardized grid variables.  
2. ompute Net Load & Detect Ramps: The analytics core calculates the net load curve by subtracting solar and wind generation from gross demand, flagging any evening net ramp exceeding $50\text{ MW/hr}$.  
3. Diagnose Asset Health & Root Causes: Sensor feeds are compared against theoretical generation curves using Performance Ratio metrics to identify underperforming equipment and assign root causes, such as inverter thermal clipping or panel soiling.  
4. Optimize Battery Dispatch & Curtailment: The engine models a Battery Energy Storage System (BESS) to charge during midday surplus hours (minimizing clean energy curtailment) and discharge during peak evening demand.  
5. Generate BLUF Operator Brief: The structured findings are passed to ibm/granite-3-8b-instruct via watsonx.ai to output a clear, actionable Bottom-Line-Up-Front (BLUF) operational memo.  
6. Display Real-Time Dashboard: The web UI renders the interactive 24-hour load-versus-renewables forecast chart, color-coded asset diagnostic alerts, battery state-of-charge schedule, and the generated operational brief. 

## Architecture Diagram

> See [`architecture.md`](architecture.md) for the detailed diagram.

[Optionally include a simple ASCII or Mermaid diagram here for quick reference.]

```
[Operator / CSV Data] ──► [Web Dashboard: HTML/JS/Chart.js]
                                     │
                                (REST API)
                                     ▼
                            [Backend: Flask Core]
                                     │
                  ┌──────────────────┴──────────────────┐
                  ▼                                     ▼
       [Analytics Engine (src/)]               [IBM watsonx.ai]
       • Net Load & Ramp Forecast              • granite-3-8b-instruct
       • Performance Ratio Diagnostics         • BLUF Brief Synthesis
       • BESS Curtailment Optimizer
                  │                                     │
                  └──────────────────┬──────────────────┘
                                     ▼
                         [Operator Action Brief]
```

## Key Design Decisions

| Decision | Rationale |
|---|---|
| Physics-Informed Deterministic Diagnostics | Sensor failure modes like inverter thermal clipping and panel soiling follow known physical equations; rule-based PR thresholds are faster, transparent, and more reliable than black-box models. |
| Pre-Aggregation before LLM Inference | Passing structured summary JSON rather than thousands of raw time-series rows to IBM Granite conserves watsonx Resource Units (RUs), prevents hallucination, and reduces inference latency. |
| Dynamic Column Normalization | Permissive column matching ensures telemetry CSVs from varying SCADA or AMI sources run smoothly without throwing formatting crashes. |
| IBM Bob IDE for Full-Stack Scaffolding | Used Bob's Plan and Code modes to scaffold the backend API, algorithms, and automated test suite, tracking development sessions under `bob_sessions/`. |

## IBM Technologies Used

- IBM Bob IDE (Required Core Component): Served as the AI pair programmer across the full software development lifecycle. Used Plan Mode to structure module boundaries and Code/Agent Mode to write src/analytics.py, API endpoints in src/app.py, automated tests, and session report exports stored in bob_sessions/.  
- IBM watsonx.ai & Granite Models: Used the ibm/granite-3-8b-instruct foundation model via the Prompt Lab and Python SDK to transform complex multi-variable grid metrics into shift-ready Bottom-Line-Up-Front (BLUF) operator summaries.  
- IBM Cloud Security Controls: Enforced credential hygiene using environment variable isolation (.env) alongside pre-configured .gitignore and .bobignore patterns to prevent cloud API key exposure.  

# Problem Statement

## Background

This challenge falls within the Utilities sector—specifically electric power transmission, distribution, and renewable generation management. The rapid global transition toward decarbonization has integrated unprecedented volumes of non-dispatchable solar and wind generation into modern power systems. Unlike traditional fossil or hydroelectric generation, renewable energy is intermittent and weather-dependent. Power generation must instantaneously balance load across every millisecond, making modern transmission networks increasingly sensitive to weather volatility, localized feeder constraints, and rapid shifts in consumer demand patterns.

## The Problem

Grid dispatchers and renewable asset managers operate with disconnected, siloed systems, leaving them with very limited real-time decision support. At midday, massive solar generation saturates regional transmission capacity, forcing operators to intentionally curtail clean electricity because the grid cannot absorb it. Hours later, as the sun sets, sharp consumer demand ramps trigger severe grid instability, forcing transmission operators to scramble high-cost, fossil-fuel peaker plants. Simultaneously, hardware-level performance issues across solar arrays and wind farms—such as thermal inverter clipping, panel soiling, and yaw misalignment—are obscured by aggregate telemetry and go undiagnosed until substantial generation is permanently lost.

## Who is Affected

- Transmission System Operators (TSOs) and Regional Grid Dispatchers: Control-room engineers responsible for balancing sub-transmission line capacity, grid frequency, and unit commitment during critical morning and evening ramp windows.

- Renewable Plant Operations & Maintenance (O&M) Managers: Field and monitoring engineers managing solar arrays and wind turbine fleets who need asset-level root-cause diagnostics to prioritize repairs and prevent equipment degradation. 

## Why It Matters

- Severe Clean Energy Waste: The United States alone curtailed approximately 8 TWh of clean renewable energy in 2023 because transmission networks lacked the real-time flexibility to absorb it.  

- High Operational & Environmental Costs: Unanticipated net load spikes force grid operators to spin up high-emission, gas-fired peaker plants on short notice, driving up operational expenses and undermining municipal net-zero targets. 

- Equipment Deterioration and Outage Risks: Undetected thermal clipping in power inverters and structural stress on misaligned wind turbines cause premature component failure, increasing unplanned downtime and risking localized distribution outages.  

## Why Existing Solutions Fall Short

- Static, Calendar-Based Control: Most regional utilities rely on static schedules and historical spreadsheets rather than dynamic, weather-coupled predictive models.  

- Siloed Forecasting and Maintenance: Generation forecasting tools operate completely independently from asset health telemetry and battery dispatch management, forcing operators to manually cross-reference disconnected dashboards during high-stress dispatch windows.  

- Lack of Actionable Root-Cause Insights: Existing SCADA alarms trigger threshold alerts without isolating the underlying physical root cause (e.g., differentiating between natural irradiance drops, inverter thermal derating, and dirty panels), leaving operators without actionable guidance on how to respond. 
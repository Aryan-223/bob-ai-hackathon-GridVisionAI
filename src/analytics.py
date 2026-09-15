# -*- coding: utf-8 -*-
"""
analytics.py - GridVision AI Core Analytics Engine
Computes net load, ramp detection, asset diagnostics, BESS dispatch,
and synthesizes an operator summary for the GridVision AI dashboard.
"""

from __future__ import annotations

import io
import math
from typing import Any

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. COLUMN NORMALIZATION
# ---------------------------------------------------------------------------

# Maps known aliases → internal standard key
_COLUMN_ALIASES: dict[str, list[str]] = {
    "timestamp": [
        "timestamp", "datetime", "time", "date", "hour", "Datetime", "Date",
        "Time", "TIMESTAMP",
    ],
    "grid_demand_mw": [
        "grid_demand_mw", "demand", "load", "MW", "mw", "Load", "Demand",
        "gross_demand", "total_load", "grid_load", "consumption",
        "DEMAND_MW", "LOAD_MW", "demand_mw", "load_mw",
    ],
    "actual_solar_mw": [
        "actual_solar_mw", "solar", "solar_mw", "solar_power", "pv_power",
        "pv_mw", "Solar", "PV", "pv", "solar_gen", "PV_MW",
    ],
    "actual_wind_mw": [
        "actual_wind_mw", "wind", "wind_mw", "wind_power", "Wind",
        "wind_gen", "WIND_MW", "wind_generation",
    ],
    "temperature_c": [
        "temperature_c", "temperature", "temp", "ambient_temp",
        "Temperature", "Temp", "TEMP_C", "temp_c",
    ],
    "solar_irradiance_wm2": [
        "solar_irradiance_wm2", "irradiance", "solar_irradiance",
        "GHI", "ghi", "Irradiance", "IRRADIANCE", "irradiance_wm2",
        "solar_radiation",
    ],
    "inverter_temp_c": [
        "inverter_temp_c", "inverter_temp", "inv_temp", "InverterTemp",
        "inverter_temperature", "INV_TEMP_C",
    ],
}

# Installed solar capacity assumption for PR calculation (MW-peak)
SOLAR_CAPACITY_MW = 80.0
# Irradiance at Standard Test Conditions (W/m²)
STC_IRRADIANCE = 1000.0

# BESS parameters
BESS_CAPACITY_MWH = 50.0
BESS_MAX_POWER_MW = 15.0
BESS_SOC_MIN = 0.10  # 10 %
BESS_SOC_MAX = 0.90  # 90 %
BESS_INITIAL_SOC = 0.50

# Ramp threshold (MW / hr)
RAMP_THRESHOLD_MW_HR = 50.0

# Performance Ratio thresholds
PR_THERMAL_CLIP_THRESHOLD = 0.70
PR_SOILING_THRESHOLD = 0.80
INVERTER_TEMP_CLIP_C = 75.0


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map incoming CSV column names to internal standard keys.
    Performs case-insensitive prefix matching as fallback.
    Unknown columns are left as-is.
    """
    col_map: dict[str, str] = {}
    existing = {c.lower().strip(): c for c in df.columns}

    for standard_key, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in df.columns:
                col_map[alias] = standard_key
                break
            if alias.lower() in existing:
                col_map[existing[alias.lower()]] = standard_key
                break

    df = df.rename(columns=col_map)

    # Ensure numeric columns exist (fill with 0 if missing)
    numeric_keys = [
        "grid_demand_mw", "actual_solar_mw", "actual_wind_mw",
        "temperature_c", "solar_irradiance_wm2", "inverter_temp_c",
    ]
    for key in numeric_keys:
        if key not in df.columns:
            df[key] = 0.0
        else:
            df[key] = pd.to_numeric(df[key], errors="coerce").fillna(0.0)

    return df


# ---------------------------------------------------------------------------
# 2. NET LOAD & RAMP ANALYSIS
# ---------------------------------------------------------------------------

def compute_net_load(df: pd.DataFrame) -> pd.DataFrame:
    """
    Net Load(t) = Demand(t) − (Solar(t) + Wind(t))
    Adds columns: net_load_mw, ramp_rate_mw_hr, is_spike
    """
    df = df.copy()
    df["renewable_total_mw"] = df["actual_solar_mw"] + df["actual_wind_mw"]
    df["net_load_mw"] = df["grid_demand_mw"] - df["renewable_total_mw"]

    # Hourly ramp rate (forward difference, wrap first to 0)
    df["ramp_rate_mw_hr"] = df["net_load_mw"].diff().fillna(0.0)

    # Flag critical spike windows (ramp > threshold)
    df["is_spike"] = df["ramp_rate_mw_hr"].abs() > RAMP_THRESHOLD_MW_HR

    return df


# ---------------------------------------------------------------------------
# 3. ASSET DIAGNOSTICS
# ---------------------------------------------------------------------------

def compute_performance_ratio(
    actual_mw: float,
    irradiance_wm2: float,
    capacity_mw: float = SOLAR_CAPACITY_MW,
    stc: float = STC_IRRADIANCE,
) -> float:
    """
    PR = Actual Generation / (Capacity × (Irradiance / STC))
    Returns NaN when expected generation is effectively zero.
    """
    expected = capacity_mw * (irradiance_wm2 / stc)
    if expected < 0.001:
        return float("nan")
    return actual_mw / expected


def diagnose_assets(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Evaluate each row's solar performance and flag anomalies.
    Returns a list of alert dicts sorted by hour.
    """
    alerts: list[dict[str, Any]] = []

    for _, row in df.iterrows():
        irr = row.get("solar_irradiance_wm2", 0.0)
        actual = row.get("actual_solar_mw", 0.0)
        inv_temp = row.get("inverter_temp_c", 0.0)
        ts = row.get("timestamp", "")

        pr = compute_performance_ratio(actual, irr)

        if math.isnan(pr):
            continue  # night-time / no irradiance — skip

        if pr < PR_THERMAL_CLIP_THRESHOLD and inv_temp > INVERTER_TEMP_CLIP_C:
            alerts.append(
                {
                    "hour": str(ts),
                    "asset_id": "INV-001",
                    "root_cause": "Inverter Thermal Clipping",
                    "detail": (
                        f"PR={pr:.2f} (<0.70) | Inv Temp={inv_temp:.1f}C (>75C). "
                        "Thermal derating active - heat exchanger likely clogged."
                    ),
                    "severity": "critical",
                    "performance_ratio": round(pr, 3),
                }
            )
        elif pr < PR_SOILING_THRESHOLD:
            alerts.append(
                {
                    "hour": str(ts),
                    "asset_id": "PV-ARRAY-02",
                    "root_cause": "Panel Soiling Detected",
                    "detail": (
                        f"PR={pr:.2f} (<0.80) with normal inverter temp. "
                        "Dust/soiling on panel surface reducing light transmission."
                    ),
                    "severity": "warning",
                    "performance_ratio": round(pr, 3),
                }
            )

    return alerts


# ---------------------------------------------------------------------------
# 4. BESS DISPATCH OPTIMIZER
# ---------------------------------------------------------------------------

def optimize_bess_dispatch(df: pd.DataFrame) -> dict[str, Any]:
    """
    Simulate a 50 MWh BESS (15 MW max, 10–90 % SoC).
    Charge during midday surplus (net_load < 0).
    Discharge to shave the evening ramp peak.

    Returns a dict with:
      - schedule: list of per-hour dispatch actions
      - total_avoided_curtailment_mwh: float
      - peak_soc: float
    """
    soc = BESS_INITIAL_SOC * BESS_CAPACITY_MWH  # MWh stored
    schedule: list[dict[str, Any]] = []
    avoided_curtailment = 0.0

    # Pre-identify the single largest positive ramp hour for priority discharge
    ramp = df["ramp_rate_mw_hr"].values
    net = df["net_load_mw"].values

    for i, row in df.iterrows():
        ts = str(row.get("timestamp", i))
        net_load = row["net_load_mw"]
        ramp_rate = row["ramp_rate_mw_hr"]
        action = "idle"
        power_mw = 0.0

        # ---- Charge during surplus (net load < 0 = more renewable than demand)
        if net_load < 0:
            surplus = abs(net_load)
            charge_mw = min(surplus, BESS_MAX_POWER_MW)
            headroom_mwh = (BESS_SOC_MAX * BESS_CAPACITY_MWH) - soc
            charge_mwh = min(charge_mw, headroom_mwh)  # 1-hr interval
            if charge_mwh > 0.001:
                soc += charge_mwh
                avoided_curtailment += charge_mwh
                power_mw = charge_mwh
                action = "charging"

        # ---- Discharge to shave evening ramp spike
        elif ramp_rate > RAMP_THRESHOLD_MW_HR:
            discharge_mw = min(BESS_MAX_POWER_MW, ramp_rate - RAMP_THRESHOLD_MW_HR)
            floor_mwh = BESS_SOC_MIN * BESS_CAPACITY_MWH
            discharge_mwh = min(discharge_mw, soc - floor_mwh)
            if discharge_mwh > 0.001:
                soc -= discharge_mwh
                power_mw = -discharge_mwh
                action = "discharging"

        soc_pct = round((soc / BESS_CAPACITY_MWH) * 100, 1)
        schedule.append(
            {
                "hour": ts,
                "action": action,
                "power_mw": round(power_mw, 2),
                "soc_mwh": round(soc, 2),
                "soc_pct": soc_pct,
            }
        )

    peak_soc = max(s["soc_pct"] for s in schedule)

    return {
        "schedule": schedule,
        "total_avoided_curtailment_mwh": round(avoided_curtailment, 2),
        "peak_soc_pct": peak_soc,
        "bess_capacity_mwh": BESS_CAPACITY_MWH,
        "bess_max_power_mw": BESS_MAX_POWER_MW,
    }


# ---------------------------------------------------------------------------
# 5. OPERATOR SYNTHESIS
# ---------------------------------------------------------------------------

def synthesize_summary(
    df: pd.DataFrame,
    asset_alerts: list[dict],
    bess_result: dict,
) -> dict[str, Any]:
    """
    Compose an integrated operator summary dict combining:
    - KPI metrics
    - Ramp warnings
    - Asset alert table
    - BESS dispatch schedule
    - BLUF executive briefing text
    """
    peak_demand = float(df["grid_demand_mw"].max())
    min_net_load = float(df["net_load_mw"].min())
    max_net_load = float(df["net_load_mw"].max())
    peak_ramp = float(df["ramp_rate_mw_hr"].abs().max())

    spike_windows = df[df["is_spike"]]["timestamp"].astype(str).tolist()

    # Midday surplus = largest deficit in net_load (most overgeneration)
    midday_surplus = max(0.0, float(-df["net_load_mw"].min()))

    avoided = bess_result["total_avoided_curtailment_mwh"]

    total_solar_gen = float(df["actual_solar_mw"].sum())
    total_wind_gen = float(df["actual_wind_mw"].sum())
    total_renewable_gen = total_solar_gen + total_wind_gen

    # Build BLUF text (no LLM dependency — deterministic fallback)
    spike_str = ", ".join(spike_windows) if spike_windows else "None detected"
    alert_count = len(asset_alerts)
    critical_count = sum(1 for a in asset_alerts if a["severity"] == "critical")

    bluf_text = (
        f"BLUF - Grid Shift Operator Brief\n\n"
        f"SITUATION: Today's 24-hr profile shows peak gross demand of "
        f"{peak_demand:.1f} MW with maximum net load ramp of {peak_ramp:.1f} MW/hr "
        f"(threshold: {RAMP_THRESHOLD_MW_HR:.0f} MW/hr). "
        f"Critical evening spike windows: {spike_str}.\n\n"
        f"RENEWABLE PERFORMANCE: Total solar generation {total_solar_gen:.1f} MWh, "
        f"wind generation {total_wind_gen:.1f} MWh. "
        f"Midday overgeneration surplus of {midday_surplus:.1f} MW registered.\n\n"
        f"ASSET HEALTH: {alert_count} anomaly alert(s) raised, "
        f"{critical_count} critical. "
        + (
            "INV-001 is thermally derated — initiate immediate heat-exchanger inspection. "
            if critical_count > 0
            else ""
        )
        + "\n\n"
        f"BESS DISPATCH: BESS charged {avoided:.1f} MWh of surplus renewable energy, "
        f"avoiding equivalent curtailment. "
        f"Peak SoC reached {bess_result['peak_soc_pct']:.1f}%. "
        f"Discharge scheduled during identified ramp windows to suppress demand peaks.\n\n"
        f"RECOMMENDED ACTIONS:\n"
        f"  1. Monitor INV-001 inverter temperature — dispatch field crew if >80°C persists.\n"
        f"  2. Schedule panel cleaning for PV-ARRAY-02 at next maintenance window.\n"
        f"  3. Confirm BESS is armed and charge cycle completes before 17:00 hrs.\n"
        f"  4. Pre-position fast-ramp gas reserve for spike windows: {spike_str}."
    )

    # Time-series arrays for chart rendering
    time_labels = df["timestamp"].astype(str).tolist()
    demand_series = df["grid_demand_mw"].round(2).tolist()
    solar_series = df["actual_solar_mw"].round(2).tolist()
    wind_series = df["actual_wind_mw"].round(2).tolist()
    net_load_series = df["net_load_mw"].round(2).tolist()
    ramp_series = df["ramp_rate_mw_hr"].round(2).tolist()
    renewable_series = df["renewable_total_mw"].round(2).tolist()
    soc_series = [s["soc_pct"] for s in bess_result["schedule"]]

    return {
        "kpis": {
            "peak_demand_mw": round(peak_demand, 1),
            "peak_net_load_mw": round(max_net_load, 1),
            "min_net_load_mw": round(min_net_load, 1),
            "midday_surplus_mw": round(midday_surplus, 1),
            "peak_ramp_mw_hr": round(peak_ramp, 1),
            "avoided_curtailment_mwh": round(avoided, 2),
            "active_alerts": alert_count,
            "critical_alerts": critical_count,
            "total_solar_mwh": round(total_solar_gen, 1),
            "total_wind_mwh": round(total_wind_gen, 1),
            "total_renewable_mwh": round(total_renewable_gen, 1),
        },
        "spike_windows": spike_windows,
        "asset_alerts": asset_alerts,
        "bess": bess_result,
        "bluf": bluf_text,
        "chart_data": {
            "labels": time_labels,
            "demand": demand_series,
            "solar": solar_series,
            "wind": wind_series,
            "renewable": renewable_series,
            "net_load": net_load_series,
            "ramp_rate": ramp_series,
            "soc_pct": soc_series,
        },
    }


# ---------------------------------------------------------------------------
# 6. CSV I/O HELPERS
# ---------------------------------------------------------------------------

def _read_csv_robust(csv_source: "str | bytes | io.IOBase") -> pd.DataFrame:
    """
    Read a CSV tolerating comma, semicolon, tab separators and UTF-8 BOM.
    """
    if isinstance(csv_source, (bytes, bytearray)):
        raw = bytes(csv_source)
    elif isinstance(csv_source, str):
        with open(csv_source, "rb") as fh:
            raw = fh.read()
    else:
        raw = csv_source.read()

    # Strip UTF-8 BOM
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]

    first_line = raw.split(b"\n")[0].decode("utf-8", errors="replace")
    if first_line.count(";") > first_line.count(","):
        sep = ";"
    elif first_line.count("\t") > first_line.count(","):
        sep = "\t"
    else:
        sep = ","

    # Try UTF-8 first, fall back to latin-1 which never fails on any byte sequence
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            df = pd.read_csv(
                io.BytesIO(raw),
                sep=sep,
                skip_blank_lines=True,
                on_bad_lines="skip",
                encoding=enc,
            )
            df.columns = [str(c).strip() for c in df.columns]
            return df
        except UnicodeDecodeError:
            continue
        except Exception:
            break
    return pd.DataFrame()


# ---------------------------------------------------------------------------
# 7. KAGGLE SOLAR / WEATHER DATASET PREPROCESSOR
# ---------------------------------------------------------------------------
# Kaggle "Solar Power Generation" dataset columns:
#   Generation file : DATE_TIME, PLANT_ID, SOURCE_KEY, DC_POWER, AC_POWER,
#                     DAILY_YIELD, TOTAL_YIELD
#   Weather file    : DATE_TIME, PLANT_ID, SOURCE_KEY, AMBIENT_TEMPERATURE,
#                     MODULE_TEMPERATURE, IRRADIATION
#
# We detect these automatically and convert to the internal standard schema.
# ---------------------------------------------------------------------------

_KAGGLE_GEN_COLS  = {"DATE_TIME", "DC_POWER", "AC_POWER", "SOURCE_KEY"}
_KAGGLE_WX_COLS   = {"DATE_TIME", "AMBIENT_TEMPERATURE", "IRRADIATION"}

# Kaggle AC_POWER is in kW per inverter; sum across inverters → divide by 1000 → MW
_KW_TO_MW = 1e-3


def _is_kaggle_generation(df: pd.DataFrame) -> bool:
    cols = {c.upper() for c in df.columns}
    return _KAGGLE_GEN_COLS.issubset(cols)


def _is_kaggle_weather(df: pd.DataFrame) -> bool:
    cols = {c.upper() for c in df.columns}
    return _KAGGLE_WX_COLS.issubset(cols) and "DC_POWER" not in cols


def _parse_kaggle_datetime(series: pd.Series) -> pd.Series:
    """Parse Kaggle DATE_TIME which comes in format '15-05-2020 00:00' or ISO."""
    formats = ["%d-%m-%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"]
    for fmt in formats:
        try:
            return pd.to_datetime(series, format=fmt)
        except Exception:
            continue
    return pd.to_datetime(series, infer_datetime_format=True, errors="coerce")


def preprocess_kaggle_generation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate Kaggle 15-min per-inverter generation data to hourly plant totals.
    Returns df with columns: timestamp, actual_solar_mw, inverter_temp_c
    """
    df = df.copy()
    df.columns = [c.upper().strip() for c in df.columns]

    df["_dt"] = _parse_kaggle_datetime(df["DATE_TIME"])
    df["_hour"] = df["_dt"].dt.floor("h")

    # AC_POWER in kW → sum all inverters per hour → MW
    ac_col = "AC_POWER"
    if ac_col not in df.columns:
        ac_col = next((c for c in df.columns if "AC" in c and "POWER" in c), None)

    if ac_col is None:
        raise ValueError("Could not find AC_POWER column in generation file.")

    df[ac_col] = pd.to_numeric(df[ac_col], errors="coerce").fillna(0.0)

    hourly = (
        df.groupby("_hour")
        .agg(actual_solar_mw=(ac_col, "sum"))
        .reset_index()
        .rename(columns={"_hour": "timestamp"})
    )
    hourly["actual_solar_mw"] = hourly["actual_solar_mw"] * _KW_TO_MW
    hourly["inverter_temp_c"] = 0.0  # filled later if weather file provided
    return hourly


def preprocess_kaggle_weather(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate Kaggle 15-min weather sensor data to hourly averages.
    Returns df with columns: timestamp, temperature_c, solar_irradiance_wm2, inverter_temp_c
    """
    df = df.copy()
    df.columns = [c.upper().strip() for c in df.columns]

    df["_dt"] = _parse_kaggle_datetime(df["DATE_TIME"])
    df["_hour"] = df["_dt"].dt.floor("h")

    # Irradiation in the Kaggle set is in W/m²
    agg: dict = {}
    if "AMBIENT_TEMPERATURE" in df.columns:
        df["AMBIENT_TEMPERATURE"] = pd.to_numeric(df["AMBIENT_TEMPERATURE"], errors="coerce")
        agg["temperature_c"] = ("AMBIENT_TEMPERATURE", "mean")
    if "MODULE_TEMPERATURE" in df.columns:
        df["MODULE_TEMPERATURE"] = pd.to_numeric(df["MODULE_TEMPERATURE"], errors="coerce")
        agg["inverter_temp_c"] = ("MODULE_TEMPERATURE", "mean")
    if "IRRADIATION" in df.columns:
        df["IRRADIATION"] = pd.to_numeric(df["IRRADIATION"], errors="coerce")
        # Kaggle irradiation is W/m² already
        agg["solar_irradiance_wm2"] = ("IRRADIATION", "mean")

    if not agg:
        raise ValueError("Weather file has no recognised sensor columns.")

    hourly = (
        df.groupby("_hour")
        .agg(**agg)
        .reset_index()
        .rename(columns={"_hour": "timestamp"})
    )
    return hourly


def merge_multiple_files(
    files: "list[bytes | str]",
    filenames: "list[str] | None" = None,
) -> pd.DataFrame:
    """
    Accept 1–N CSV byte payloads (or file paths), auto-detect their type,
    and merge them into a single internal-schema DataFrame ready for analysis.

    Supported file types (auto-detected):
      • Standard GridVision CSV  — timestamp + grid_demand_mw + solar + wind …
      • Kaggle Generation CSV    — DATE_TIME + SOURCE_KEY + AC_POWER + DC_POWER …
      • Kaggle Weather/Sensor CSV — DATE_TIME + AMBIENT_TEMPERATURE + IRRADIATION …
      • Any mix of the above

    Returns a DataFrame with all internal-schema columns filled.
    """
    if filenames is None:
        filenames = [f"file_{i}" for i in range(len(files))]

    gen_frames: list[pd.DataFrame] = []
    wx_frames:  list[pd.DataFrame] = []
    std_frames: list[pd.DataFrame] = []

    for i, (src, fname) in enumerate(zip(files, filenames)):
        raw_df = _read_csv_robust(src)
        if raw_df.empty:
            continue  # skip empty files silently

        if _is_kaggle_generation(raw_df):
            gen_frames.append(preprocess_kaggle_generation(raw_df))
        elif _is_kaggle_weather(raw_df):
            wx_frames.append(preprocess_kaggle_weather(raw_df))
        else:
            # Treat as standard GridVision CSV
            raw_df = normalize_columns(raw_df)
            if "timestamp" not in raw_df.columns:
                raw_df["timestamp"] = [f"Hour {j:02d}:00" for j in range(len(raw_df))]
            std_frames.append(raw_df)

    # ── Merge Kaggle gen + weather ──────────────────────────────────────────
    if gen_frames:
        gen_df = pd.concat(gen_frames, ignore_index=True)
        # Sum solar MW per timestamp when multiple gen files supplied
        gen_df = (
            gen_df.groupby("timestamp")
            .agg(actual_solar_mw=("actual_solar_mw", "sum"))
            .reset_index()
        )

        if wx_frames:
            wx_df = pd.concat(wx_frames, ignore_index=True)
            wx_df = (
                wx_df.groupby("timestamp")
                .mean(numeric_only=True)
                .reset_index()
            )
            merged = pd.merge(gen_df, wx_df, on="timestamp", how="outer")
        else:
            merged = gen_df

        merged = merged.sort_values("timestamp").reset_index(drop=True)

        # Fill missing standard columns with zeros
        for col in ["grid_demand_mw", "actual_wind_mw", "temperature_c",
                    "solar_irradiance_wm2", "inverter_temp_c"]:
            if col not in merged.columns:
                merged[col] = 0.0
            else:
                merged[col] = pd.to_numeric(merged[col], errors="coerce").fillna(0.0)

        # Synthesise a plausible demand curve if not provided:
        # base load = 1.5× peak solar + random diurnal variation
        if merged["grid_demand_mw"].sum() == 0:
            peak_solar = merged["actual_solar_mw"].max()
            base = max(peak_solar * 1.5, 200.0)
            n = len(merged)
            hours = np.arange(n)
            # simple diurnal shape: higher morning/evening, dip midday
            diurnal = base + 40 * np.sin(np.pi * hours / (n - 1)) - \
                      30 * np.sin(2 * np.pi * hours / (n - 1))
            merged["grid_demand_mw"] = np.clip(diurnal, base * 0.5, base * 1.6).round(1)

        std_frames.insert(0, merged)

    elif wx_frames and not std_frames:
        # Only weather file: build minimal frame with synthetic demand
        wx_df = pd.concat(wx_frames, ignore_index=True)
        wx_df = wx_df.groupby("timestamp").mean(numeric_only=True).reset_index()
        for col in ["actual_solar_mw", "actual_wind_mw"]:
            if col not in wx_df.columns:
                wx_df[col] = 0.0
        # Synthesise a realistic demand curve (base 250 MW with diurnal shape)
        n = len(wx_df)
        if n > 0:
            hrs = np.linspace(0, 2 * np.pi, n)
            wx_df["grid_demand_mw"] = (250 + 60 * np.sin(hrs - np.pi / 4)).round(1)
        else:
            wx_df["grid_demand_mw"] = 0.0
        std_frames.append(wx_df)

    if not std_frames:
        raise ValueError(
            "No valid data found. Please upload a GridVision CSV or "
            "Kaggle Solar Generation / Weather sensor CSV."
        )

    # ── Concatenate all standard frames ────────────────────────────────────
    final = pd.concat(std_frames, ignore_index=True)

    # Ensure required numeric columns present and clean
    for col in ["grid_demand_mw", "actual_solar_mw", "actual_wind_mw",
                "temperature_c", "solar_irradiance_wm2", "inverter_temp_c"]:
        if col not in final.columns:
            final[col] = 0.0
        else:
            final[col] = pd.to_numeric(final[col], errors="coerce").fillna(0.0)

    # Normalise timestamp column to a common type (string) so mixed
    # Timestamp/str frames can be sorted without TypeError
    final["timestamp"] = final["timestamp"].astype(str)
    final = final.sort_values("timestamp").reset_index(drop=True)
    return final


# ---------------------------------------------------------------------------
# 8. TOP-LEVEL ENTRY POINTS
# ---------------------------------------------------------------------------

def run_analysis(csv_source: "str | bytes | io.IOBase") -> dict[str, Any]:
    """
    Single-file pipeline: ingest CSV → normalize → compute → diagnose → BESS → synthesize.
    Accepts a file path string, raw bytes, or a file-like object.
    Raises ValueError with a human-readable message on bad input.
    """
    if hasattr(csv_source, "read"):
        raw = csv_source.read()
    elif isinstance(csv_source, str):
        raw = csv_source  # path
    else:
        raw = bytes(csv_source)

    df = merge_multiple_files([raw], ["upload.csv"])

    if df.empty:
        raise ValueError("The uploaded CSV is empty or could not be parsed.")

    if "timestamp" not in df.columns:
        df["timestamp"] = [f"Hour {i:02d}:00" for i in range(len(df))]

    df = compute_net_load(df)
    asset_alerts = diagnose_assets(df)
    bess_result  = optimize_bess_dispatch(df)
    summary      = synthesize_summary(df, asset_alerts, bess_result)
    return summary


def run_analysis_multi(
    files: "list[bytes]",
    filenames: "list[str]",
) -> dict[str, Any]:
    """
    Multi-file pipeline: merge all files then analyse.
    """
    df = merge_multiple_files(files, filenames)

    if df.empty:
        raise ValueError("No usable data found across the uploaded files.")

    if "timestamp" not in df.columns:
        df["timestamp"] = [f"Hour {i:02d}:00" for i in range(len(df))]

    df = compute_net_load(df)
    asset_alerts = diagnose_assets(df)
    bess_result  = optimize_bess_dispatch(df)
    summary      = synthesize_summary(df, asset_alerts, bess_result)

    # Tag how many files were merged
    summary["meta"] = {
        "files_merged": len(files),
        "filenames": filenames,
        "rows_analysed": len(df),
    }
    return summary

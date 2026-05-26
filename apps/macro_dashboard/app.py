"""
Macro Dashboard
----------------
Garrison Financial Group

Tracks leading US macroeconomic indicators via the FRED API with
recession probability signals and interactive visualizations.
"""

import streamlit as st

st.set_page_config(
    page_title="Macro Dashboard | Garrison Financial Group",
    page_icon="🌐",
    layout="wide",
)

st.title("Macro Dashboard")
st.caption("Garrison Financial Group")

st.info("This app is under development. Check back soon.", icon="🚧")

# ------------------------------------------------------------
# TODO: Build out the following sections
# ------------------------------------------------------------
# 1. FRED API setup
#    - Store API key in .streamlit/secrets.toml (never commit)
#    - Use fredapi library: pip install fredapi
#    - Key series to pull:
#        T10Y2Y   — 10yr/2yr yield spread (inversion signal)
#        UNRATE   — Unemployment rate
#        CPIAUCSL — CPI (inflation)
#        M2SL     — M2 money supply
#        USREC    — NBER recession indicator (shading)
#        UMCSENT  — Consumer sentiment
#
# 2. Dashboard layout (use st.columns)
#    - Row 1: KPI metric cards (current values vs. 1yr ago)
#    - Row 2: Yield curve chart with recession shading
#    - Row 3: Unemployment + CPI dual-axis chart
#    - Row 4: M2 money supply with YoY % change
#
# 3. Recession signal
#    - Yield curve inversion flag (T10Y2Y < 0)
#    - Sahm Rule real-time indicator (SAHMREALTIME from FRED)
#    - Simple composite signal (0/1/2 indicators triggered)
#    - Display as a colored status badge: Low / Elevated / High
#
# 4. Sidebar controls
#    - Lookback window: 2yr, 5yr, 10yr, Max
#    - Toggle: show/hide recession shading
#    - Data refresh button (cache TTL = 1 hour via @st.cache_data)
# ------------------------------------------------------------

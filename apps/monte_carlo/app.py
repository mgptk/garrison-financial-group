"""
Monte Carlo Retirement Simulator
---------------------------------
Garrison Financial Group

Simulates thousands of retirement outcomes based on user inputs and
displays probability-of-success metrics with interactive visualizations.
"""

import streamlit as st

st.set_page_config(
    page_title="Monte Carlo Retirement Simulator | Garrison Financial Group",
    page_icon="📊",
    layout="wide",
)

st.title("Monte Carlo Retirement Simulator")
st.caption("Garrison Financial Group")

st.info("This app is under development. Check back soon.", icon="🚧")

# ------------------------------------------------------------
# TODO: Build out the following sections
# ------------------------------------------------------------
# 1. Sidebar: user inputs
#    - Current age
#    - Current savings ($)
#    - Annual savings rate (%)
#    - Expected return (%) and volatility (%)
#    - Target retirement age
#    - Annual spending in retirement ($)
#    - Number of simulations (default 1000)
#
# 2. Run Monte Carlo simulation
#    - Geometric Brownian Motion for portfolio growth
#    - Draw random annual returns from normal distribution
#    - Track portfolio value year-by-year across all simulations
#
# 3. Results
#    - Probability of success (portfolio > 0 at end of horizon)
#    - Fan chart: percentile bands (10th, 25th, 50th, 75th, 90th)
#    - Distribution of final portfolio values
#    - Key stats table (median outcome, worst 10%, best 10%)
#
# 4. Sensitivity analysis
#    - Slider to see how changing savings rate affects success %
# ------------------------------------------------------------

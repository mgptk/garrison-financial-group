"""
Portfolio Optimizer
--------------------
Garrison Financial Group

Mean-variance optimization (Markowitz) with efficient frontier visualization,
Sharpe ratio maximization, and CVaR extension.
"""

import streamlit as st

st.set_page_config(
    page_title="Portfolio Optimizer | Garrison Financial Group",
    page_icon="📈",
    layout="wide",
)

st.title("Portfolio Optimizer")
st.caption("Garrison Financial Group")

st.info("This app is under development. Check back soon.", icon="🚧")

# ------------------------------------------------------------
# TODO: Build out the following sections
# ------------------------------------------------------------
# 1. Sidebar: user inputs
#    - Ticker input (comma-separated, e.g. AAPL, MSFT, BND)
#    - Lookback period (1y, 3y, 5y)
#    - Risk-free rate (default 5.0%)
#    - Number of random portfolios for frontier (default 5000)
#
# 2. Data fetch
#    - Pull historical prices via yfinance
#    - Compute log returns, mean returns, covariance matrix
#
# 3. Optimization
#    - Random portfolio simulation for frontier scatter
#    - scipy.optimize: maximize Sharpe ratio (minimize negative Sharpe)
#    - scipy.optimize: minimize volatility for given return levels
#    - Plot efficient frontier with color-coded Sharpe ratio
#    - Mark: max Sharpe, min volatility, equal-weight portfolios
#
# 4. CVaR extension
#    - Historical simulation CVaR at 95% and 99% confidence
#    - Compare optimized vs. equal-weight CVaR
#
# 5. Weights table
#    - Show recommended weights for max-Sharpe portfolio
#    - Rebalancing delta vs. user's current holdings
# ------------------------------------------------------------

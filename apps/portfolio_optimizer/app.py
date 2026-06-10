"""
Portfolio Optimizer
Garrison Financial Group — gfg.finance

Markowitz mean-variance optimisation with Ledoit-Wolf shrinkage covariance,
efficient frontier, CVaR risk analysis, and historical performance comparison.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from scipy.optimize import minimize
from sklearn.covariance import LedoitWolf

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────────────────────────────────────
# Page config  ← must be first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Portfolio Optimizer | GFG",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Brand palette & CSS
# ─────────────────────────────────────────────────────────────────────────────
FOREST       = "#0f2114"
FOREST_MID   = "#1a3320"
FOREST_LIGHT = "#2a4a32"
CREAM        = "#dbd7c1"
CREAM_LIGHT  = "#e8e5d6"
CREAM_DARK   = "#cac6b0"
AMBER        = "#b5702a"
GREEN        = "#2d6a4f"
RED          = "#c0392b"

st.markdown(
    f"""
    <style>
    [data-testid="stAppViewContainer"] {{background-color:{CREAM}; color:{FOREST};}}
    [data-testid="stHeader"]           {{background-color:{CREAM};}}
    [data-testid="stSidebar"]          {{background-color:{CREAM_LIGHT};}}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{color:#4a5c4e;}}
    h1 {{color:{CREAM_DARK}; font-family:'Georgia',serif; letter-spacing:0.02em;}}
    h2, h3, h4 {{color:{FOREST_MID};}}
    [data-testid="metric-container"] {{
        background:{CREAM_LIGHT}; border-radius:8px; padding:0.8rem 1rem;
        border:1px solid {CREAM_DARK};
    }}
    [data-testid="stMetricValue"] {{color:{FOREST};}}
    [data-testid="stMetricLabel"] {{color:#4a5c4e;}}
    [data-testid="stMetricDelta"] {{
        color:{FOREST};
        background-color:{CREAM_DARK}
    }}
    hr {{border-color:{CREAM_DARK};}}

    /* ── number inputs ── */
    .stNumberInput div[data-baseweb="input"] > div {{
        background-color: {FOREST};
        border-color: {FOREST_LIGHT};
    }}
    .stNumberInput input {{color: {CREAM_LIGHT};}}
    div.stNumberInput button {{
        color: {CREAM_LIGHT};
        background-color: {FOREST_LIGHT};
    }}
    div.stNumberInput button:hover {{
        background-color: {RED};
    }}

    /* ── text areas ── */
    [data-testid="stTextArea"] textarea {{
        background-color: {FOREST};
        color: {CREAM_LIGHT};
    }}
    [data-testid="stTextArea"] textarea:focus {{
        border-color: {FOREST_LIGHT} !important;
    }}

    /* ── tabs ── */
    .stTabs [data-baseweb="tab"] {{
        color: {FOREST_LIGHT};
    }}
    .stTabs [aria-selected="true"] {{
        color: {FOREST};
    }}
    div[data-baseweb="tab-highlight"] {{
        background-color: {FOREST};
    }}

    /* ── buttons ── */
    div.stButton > button {{
        background-color: {FOREST};
        color: {CREAM_LIGHT} !important;
    }}
    div.stButton > button:hover {{
        background-color: {FOREST_LIGHT};
        border: 1px solid {FOREST_LIGHT};
    }}

    /* ── expanders ── */
    [data-testid="stIconMaterial"] {{color:{FOREST};}}
    [data-testid="stExpander"] summary:hover {{
        background-color: {FOREST_LIGHT};
    }}

    /* ── selectboxes ── */
    div[data-baseweb="select"] > div {{
        background-color: {FOREST};
        border-color: {FOREST_LIGHT} !important;
        color: {CREAM_LIGHT};
    }}
    [data-testid="stSelectboxVirtualDropdown"]{{
        background-color: {FOREST_LIGHT} !important;
    }}
    [data-testid="stTooltipHoverTarget"] {{
        color: {CREAM_DARK} !important;
    }}
    
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────
PRESETS: dict[str, str] = {
    "Asset Classes": "SPY, AGG, GLD, VNQ, EFA, TLT",
    "US Sectors":    "XLK, XLF, XLE, XLV, XLI, XLY, XLP",
    "Factor ETFs":   "VTV, VUG, MTUM, QUAL, USMV",
}
LOOKBACK_MAP = {"1 yr": 1, "3 yr": 3, "5 yr": 5, "10 yr": 10}
N_RANDOM     = 3_000   # random portfolios for scatter
N_FRONTIER   = 80      # points on parametric efficient frontier
N_STARTS     = 20      # optimiser random restarts for Sharpe maximisation

# Shared Plotly layout for all charts
_CHART_BASE = dict(
    paper_bgcolor = CREAM,
    plot_bgcolor  = CREAM_LIGHT,
    font          = dict(color=FOREST, size=12),
    margin        = dict(l=60, r=30, t=55, b=50),
    xaxis         = dict(gridcolor=CREAM_DARK, zerolinecolor=CREAM_DARK, title_font=dict(color=FOREST_MID), tickfont=dict(color=FOREST_LIGHT)),
    yaxis         = dict(gridcolor=CREAM_DARK, zerolinecolor=CREAM_DARK, title_font=dict(color=FOREST_MID), tickfont=dict(color=FOREST_LIGHT)),
)


# ─────────────────────────────────────────────────────────────────────────────
# Data layer
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=3_600, show_spinner=False)
def fetch_prices(tickers: tuple[str, ...], years: int) -> pd.DataFrame:
    """
    Download adjusted close prices via yfinance.
    Returns a tz-naive daily DataFrame (inner join).
    Tickers with < 60 daily observations are dropped silently;
    the caller detects failures by comparing returned columns to input list.
    """
    end   = pd.Timestamp.today().normalize()
    start = end - pd.DateOffset(years=years)

    series: dict[str, pd.Series] = {}
    for t in tickers:
        try:
            raw = yf.Ticker(t).history(start=start, end=end, auto_adjust=True)
            if "Close" not in raw.columns or len(raw) < 60:
                continue
            s = raw["Close"].copy()
            if s.index.tz is not None:
                s.index = s.index.tz_convert(None)
            series[t] = s
        except Exception:
            pass

    if not series:
        return pd.DataFrame()
    return pd.DataFrame(series).dropna()


def monthly_log_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Month-end resample → log returns, dropping the first NaN row."""
    mp = prices.resample("ME").last()
    return np.log(mp / mp.shift(1)).dropna()


def lw_cov_annual(ret: pd.DataFrame) -> np.ndarray:
    """Ledoit-Wolf shrinkage covariance (monthly input) → annualized (×12)."""
    return LedoitWolf().fit(ret.values).covariance_ * 12


# ─────────────────────────────────────────────────────────────────────────────
# Portfolio mathematics  (all quantities annualized)
# ─────────────────────────────────────────────────────────────────────────────

def port_stats(
    w: np.ndarray,
    mu: np.ndarray,   # annualized expected returns
    cov: np.ndarray,  # annualized covariance matrix
    rf: float,        # annualized risk-free rate
) -> tuple[float, float, float]:
    """Return (ann_return, ann_vol, sharpe)."""
    r = float(w @ mu)
    v = float(np.sqrt(w @ cov @ w))
    s = (r - rf) / v if v > 1e-12 else 0.0
    return r, v, s


def _constraints_bounds(n: int, allow_short: bool, max_pos: float):
    constraints = [{"type": "eq", "fun": lambda w: w.sum() - 1}]
    lo = -0.20 if allow_short else 0.0
    bounds = [(lo, max_pos)] * n
    return constraints, bounds


def opt_max_sharpe(
    mu: np.ndarray, cov: np.ndarray, rf: float,
    allow_short: bool, max_pos: float,
) -> np.ndarray:
    """Maximise Sharpe ratio from N_STARTS random initialisations."""
    n = len(mu)
    constraints, bounds = _constraints_bounds(n, allow_short, max_pos)
    neg_sharpe = lambda w: -(port_stats(w, mu, cov, rf)[2])   # noqa: E731

    rng  = np.random.default_rng(42)
    best = None
    for _ in range(N_STARTS):
        w0  = rng.dirichlet(np.ones(n))
        res = minimize(neg_sharpe, w0, method="SLSQP",
                       constraints=constraints, bounds=bounds,
                       options={"ftol": 1e-9, "maxiter": 1_000})
        if res.success and (best is None or res.fun < best.fun):
            best = res
    return best.x if best is not None else np.ones(n) / n


def opt_min_vol(
    cov: np.ndarray, allow_short: bool, max_pos: float,
) -> np.ndarray:
    """Global Minimum Variance portfolio."""
    n = cov.shape[0]
    constraints, bounds = _constraints_bounds(n, allow_short, max_pos)
    res = minimize(
        lambda w: float(np.sqrt(w @ cov @ w)),
        np.ones(n) / n, method="SLSQP",
        constraints=constraints, bounds=bounds,
        options={"ftol": 1e-12, "maxiter": 1_000},
    )
    return res.x if res.success else np.ones(n) / n


def build_frontier(
    mu: np.ndarray, cov: np.ndarray, rf: float,
    allow_short: bool, max_pos: float,
) -> pd.DataFrame:
    """Parametric efficient frontier — min vol at each target return level."""
    n = len(mu)
    constraints_base, bounds = _constraints_bounds(n, allow_short, max_pos)
    gmv_w  = opt_min_vol(cov, allow_short, max_pos)
    min_r  = float(gmv_w @ mu)
    max_r  = float(np.max(mu))

    rows = []
    for target in np.linspace(min_r, max_r, N_FRONTIER):
        constraints = constraints_base + [
            {"type": "ineq", "fun": lambda w, t=target: (w @ mu) - t}
        ]
        res = minimize(
            lambda w: float(np.sqrt(w @ cov @ w)),
            gmv_w, method="SLSQP",
            constraints=constraints, bounds=bounds,
            options={"ftol": 1e-9, "maxiter": 500},
        )
        if res.success:
            r, v, s = port_stats(res.x, mu, cov, rf)
            rows.append({"return": r, "vol": v, "sharpe": s})
    return pd.DataFrame(rows)


def rand_portfolios(
    mu: np.ndarray, cov: np.ndarray, rf: float,
) -> pd.DataFrame:
    """N_RANDOM random long-only weight vectors with their stats."""
    rng = np.random.default_rng(0)
    W   = rng.dirichlet(np.ones(len(mu)), N_RANDOM)
    ret = W @ mu
    vol = np.sqrt(np.einsum("ni,ij,nj->n", W, cov, W))
    sr  = np.where(vol > 1e-12, (ret - rf) / vol, np.nan)
    return pd.DataFrame({"return": ret, "vol": vol, "sharpe": sr})


def cvar_monthly(ret: pd.DataFrame, w: np.ndarray, alpha: float = 0.05) -> float:
    """Historical 1-month CVaR at (1-alpha) confidence — reported as positive loss."""
    port_r  = ret.values @ w
    cutoff  = np.quantile(port_r, alpha)
    tail    = port_r[port_r <= cutoff]
    return float(-tail.mean()) if len(tail) else 0.0


def max_drawdown(ret: pd.DataFrame, w: np.ndarray) -> float:
    """Max peak-to-trough drawdown of a weighted portfolio (negative value)."""
    port_r  = ret.values @ w
    cumval  = np.exp(np.cumsum(port_r))
    cummax  = np.maximum.accumulate(cumval)
    return float(((cumval - cummax) / cummax).min())


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### :color[Garrison Financial Group]{foreground="+FOREST+"}")
    st.caption(":color[Portfolio Optimizer]{foreground="+FOREST_MID+"}")
    st.divider()

    # Preset buttons
    st.caption(":color[Quick presets]{foreground="+FOREST+"}")
    if "tickers_text" not in st.session_state:
        st.session_state["tickers_text"] = PRESETS["Asset Classes"]

    cols = st.columns(3)
    for col, (label, val) in zip(cols, PRESETS.items()):
        with col:
            if st.button(":color["+label+"]{foreground="+CREAM_LIGHT+"}", use_container_width=True, key=f"preset_{label}"):
                st.session_state["tickers_text"] = val
                st.rerun()

    tickers_raw = st.text_area(
        "Tickers (comma-separated)",
        value=st.session_state["tickers_text"],
        height=90,
    )
    st.session_state["tickers_text"] = tickers_raw

    st.subheader(":color[Settings]{foreground="+FOREST+"}")
    lookback_label = st.selectbox("Lookback period", list(LOOKBACK_MAP.keys()), index=2)
    years          = LOOKBACK_MAP[lookback_label]

    rf_pct = st.number_input("Risk-free rate (%/yr)", 0.0, 15.0, 4.5, 0.1, format="%.1f")
    rf     = rf_pct / 100.0

    gmv_mode = st.toggle(
        "GMV mode — minimise volatility only",
        value=False,
        help="Ignores expected return estimates. Optimal portfolio = Global Minimum Variance.",
    )

    with st.expander("⚙️ Advanced"):
        allow_short = st.toggle("Allow short selling (max −20% per asset)", value=False)
        max_pos_pct = st.slider("Max single-position weight", 10, 100, 100, 5, format="%d%%")
        max_pos     = max_pos_pct / 100.0


# ─────────────────────────────────────────────────────────────────────────────
# Parse & validate tickers
# ─────────────────────────────────────────────────────────────────────────────
tickers_input: list[str] = list(dict.fromkeys(
    t.strip().upper()
    for t in tickers_raw.replace(",", " ").split()
    if t.strip()
))

if len(tickers_input) < 2:
    st.title("Portfolio Optimizer")
    st.warning("⚠️ Enter at least two tickers in the sidebar to begin.")
    st.stop()

# Guard: max_pos must be feasible given number of tickers
min_feasible = 1.0 / len(tickers_input)
if max_pos < min_feasible - 0.01:
    max_pos = min_feasible
    st.sidebar.warning(f"Max position raised to {min_feasible*100:.0f}% to remain feasible.")


# ─────────────────────────────────────────────────────────────────────────────
# Fetch prices
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner(f"Fetching {lookback_label} price history for {len(tickers_input)} tickers…"):
    prices = fetch_prices(tuple(tickers_input), years)

if prices.empty:
    st.error("No valid price data returned. Check your tickers and try again.")
    st.stop()

valid  = list(prices.columns)
failed = [t for t in tickers_input if t not in valid]
if failed:
    st.warning(f"Could not fetch data for: **{', '.join(failed)}**. Continuing with remaining tickers.")
if len(valid) < 2:
    st.error("Need at least 2 valid tickers to optimise.")
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Compute returns & covariance
# ─────────────────────────────────────────────────────────────────────────────
ret     = monthly_log_returns(prices)          # (T, n) monthly log returns
n       = len(valid)
mu      = ret.mean().values * 12               # annualized expected returns
cov     = lw_cov_annual(ret)                   # annualized LW covariance

if len(ret) < 24:
    st.warning(
        f"Only **{len(ret)} months** of common history. "
        "Return estimates are noisy — consider a longer lookback or fewer assets."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Optimize
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Running optimization…"):
    gmv_w   = opt_min_vol(cov, allow_short, max_pos)
    opt_w   = gmv_w if gmv_mode else opt_max_sharpe(mu, cov, rf, allow_short, max_pos)
    eq_w    = np.ones(n) / n

    opt_r, opt_v, opt_s = port_stats(opt_w,  mu, cov, rf)
    gmv_r, gmv_v, gmv_s = port_stats(gmv_w,  mu, cov, rf)
    eq_r,  eq_v,  eq_s  = port_stats(eq_w,   mu, cov, rf)

    frontier = build_frontier(mu, cov, rf, allow_short, max_pos)
    scatter  = rand_portfolios(mu, cov, rf)

    opt_cvar = cvar_monthly(ret, opt_w)
    gmv_cvar = cvar_monthly(ret, gmv_w)
    eq_cvar  = cvar_monthly(ret, eq_w)

    opt_mdd = max_drawdown(ret, opt_w)
    eq_mdd  = max_drawdown(ret, eq_w)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
P = lambda v: f"{v*100:.1f}%"     # proportion → "14.3%"   noqa: E731


def alternate_rows(row):
    if row.name % 2 == 0:
        return [f'background-color: {CREAM_LIGHT}'] * len(row)
    else:
        return [f'background-color: {CREAM_DARK}'] * len(row)


def df_styler(df):
    return (
        df.style
        .set_table_styles([
            {'selector': 'th.col_heading', 'props': [
                ('background-color', FOREST_LIGHT),
                ('color', CREAM_LIGHT),
            ]}
        ])
        .set_properties(**{
            'color': FOREST_MID,
            'border': '1px solid',
            'border-color': FOREST_LIGHT,
        })
        .apply(alternate_rows, axis=1)
    )


# ─────────────────────────────────────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────────────────────────────────────
opt_label = "GMV Portfolio" if gmv_mode else "Max-Sharpe Portfolio"

st.title("Portfolio Optimizer")
st.caption(
    f"*{', '.join(valid)} · {lookback_label} · "
    f"{'GMV mode' if gmv_mode else 'Max-Sharpe mode'} · "
    f"Ledoit-Wolf covariance · {'Long-short' if allow_short else 'Long-only'}*"
)

# ─────────────────────────────────────────────────────────────────────────────
# KPI cards
# ─────────────────────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"{opt_label} — Sharpe",      f"{opt_s:.2f}",  f"{opt_s-eq_s:+.2f} vs EW")
c2.metric(f"{opt_label} — Return",      P(opt_r),        f"{(opt_r-eq_r)*100:+.1f}pp vs EW")
c3.metric(f"{opt_label} — Volatility",  P(opt_v),        f"{(opt_v-eq_v)*100:+.1f}pp vs EW")
c4.metric("Equal-Weight Sharpe",        f"{eq_s:.2f}")

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_ef, tab_wt, tab_risk, tab_corr, tab_hist = st.tabs([
    "Efficient Frontier",
    "Optimal Weights",
    "Risk Analysis",
    "Correlations",
    "Historical Returns",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Efficient Frontier
# ══════════════════════════════════════════════════════════════════════════════
with tab_ef:
    fig = go.Figure()

    # ── Random portfolio scatter (coloured by Sharpe) ──
    fig.add_trace(go.Scatter(
        x    = scatter["vol"] * 100,
        y    = scatter["return"] * 100,
        mode = "markers",
        marker = dict(
            color    = scatter["sharpe"],
            colorscale = "Viridis",
            size     = 3,
            opacity  = 0.45,
            colorbar = dict(
                title      = "Sharpe",
                thickness  = 12,
                len        = 0.55,
                tickfont   = dict(size=10),
                title_font = dict(size=11),
            ),
        ),
        name         = "Random portfolios",
        hovertemplate = "Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>",
    ))

    # ── Parametric efficient frontier ──
    if not frontier.empty:
        fig.add_trace(go.Scatter(
            x    = frontier["vol"] * 100,
            y    = frontier["return"] * 100,
            mode = "lines",
            line = dict(color=FOREST, width=2),
            name = "Efficient frontier",
            hovertemplate = "Vol: %{x:.1f}%<br>Return: %{y:.1f}%<extra></extra>",
        ))

    # ── Marked portfolios ──
    def _mark(vol, ret, label, color, symbol, pos="top right"):
        fig.add_trace(go.Scatter(
            x    = [vol * 100], y = [ret * 100],
            mode = "markers+text",
            marker     = dict(color=color, size=13, symbol=symbol,
                              line=dict(color="white", width=1)),
            text       = [label],
            textposition = pos,
            textfont   = dict(color=color, size=11),
            name       = label,
        ))

    _mark(opt_v, opt_r, opt_label,       FOREST, "star")
    if not gmv_mode:
        _mark(gmv_v, gmv_r, "Min Volatility", FOREST_LIGHT, "circle")
    _mark(eq_v,  eq_r,  "Equal Weight",  AMBER, "diamond")

    fig.update_layout(
        **_CHART_BASE,
        title       = dict(text="Efficient Frontier · Annualized Risk vs. Return",
                           font=dict(color=FOREST, size=15)),
        xaxis_title = "Annualized Volatility (%)",
        yaxis_title = "Annualized Return (%)",
        height      = 500,
        legend      = dict(bgcolor=CREAM_LIGHT, bordercolor=FOREST, borderwidth=1,
                           font=dict(color=FOREST)),
        hovermode   = "closest",
    )
    st.plotly_chart(fig, use_container_width=True)

    if gmv_mode:
        st.info(
            "**GMV mode active** — expected return estimates are ignored. "
            "The optimal portfolio is the Global Minimum Variance portfolio. "
            "The efficient frontier is shown for context."
        )
    else:
        st.caption(
            "Return estimates derived from historical means — noisy over short lookbacks. "
            "Covariance estimated via Ledoit-Wolf shrinkage for numerical stability."
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Optimal Weights
# ══════════════════════════════════════════════════════════════════════════════
with tab_wt:
    sorted_idx = np.argsort(opt_w)[::-1]

    # Horizontal bar chart
    fig_w = go.Figure(go.Bar(
        x             = opt_w[sorted_idx] * 100,
        y             = [valid[i] for i in sorted_idx],
        orientation   = "h",
        marker_color  = FOREST,
        text          = [f"{opt_w[i]*100:.1f}%" for i in sorted_idx],
        textposition  = "outside",
        textfont      = dict(color=FOREST, size=11),
        name          = opt_label,
    ))
    # Equal-weight overlay
    fig_w.add_trace(go.Bar(
        x             = [eq_w[0] * 100] * n,
        y             = [valid[i] for i in sorted_idx],
        orientation   = "h",
        marker_color  = AMBER,
        opacity       = 0.45,
        name          = "Equal Weight",
    ))

    fig_w.update_layout(
        **_CHART_BASE,
        title      = dict(text=f"{opt_label} · Asset Allocation",
                          font=dict(color=FOREST, size=15)),
        xaxis_title = "Weight (%)",
        barmode    = "overlay",
        height     = max(320, n * 48 + 100),
        legend     = dict(bgcolor=CREAM_LIGHT, bordercolor=FOREST, borderwidth=1),
    )
    st.plotly_chart(fig_w, use_container_width=True)

    # Weights table
    st.subheader("Weights Table")
    wt_df = pd.DataFrame({
        "Ticker":         valid,
        "Optimal Weight": [P(w) for w in opt_w],
        "Equal Weight":   [P(eq_w[0])] * n,
        "Δ (Opt − EW)":   [f"{(o - eq_w[0])*100:+.1f}pp" for o in opt_w],
    })
    st.table(df_styler(wt_df), hide_index=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Risk Analysis
# ══════════════════════════════════════════════════════════════════════════════
with tab_risk:
    col_l, col_r = st.columns(2)

    # Portfolio comparison table
    with col_l:
        st.subheader("Portfolio Summary")
        risk_df = pd.DataFrame({
            "Portfolio":          [opt_label, "Min Volatility", "Equal Weight"],
            "Ann. Return":        [P(opt_r),  P(gmv_r),  P(eq_r)],
            "Ann. Volatility":    [P(opt_v),  P(gmv_v),  P(eq_v)],
            "Sharpe Ratio":       [f"{opt_s:.2f}", f"{gmv_s:.2f}", f"{eq_s:.2f}"],
            "Monthly CVaR 95%":   [P(opt_cvar), P(gmv_cvar), P(eq_cvar)],
            "Max Drawdown":       [P(opt_mdd), P(max_drawdown(ret, gmv_w)), P(eq_mdd)],
        })
        st.table(df_styler(risk_df), hide_index=True)
        st.caption(
            "CVaR = average monthly loss in the worst 5% of months (historical). "
            "Max Drawdown = worst peak-to-trough decline over the full lookback."
        )

    # Per-asset risk table
    with col_r:
        st.subheader("Individual Asset Risk")
        asset_rows = []
        for i, t in enumerate(valid):
            w1 = np.zeros(n); w1[i] = 1.0
            a_r = float(mu[i])
            a_v = float(np.sqrt(cov[i, i]))
            a_s = (a_r - rf) / a_v if a_v > 1e-12 else 0.0
            asset_rows.append({
                "Ticker":          t,
                "Ann. Return":     P(a_r),
                "Ann. Volatility": P(a_v),
                "Sharpe":          f"{a_s:.2f}",
                "CVaR (monthly)":  P(cvar_monthly(ret, w1)),
            })
        st.table(df_styler(pd.DataFrame(asset_rows)), hide_index=True)

    # Volatility comparison bar chart
    st.subheader("Volatility Comparison")
    vol_labels = valid + [opt_label, "Equal Weight"]
    vol_vals   = [np.sqrt(cov[i, i]) * 100 for i in range(n)] + [opt_v*100, eq_v*100]
    vol_colors = [CREAM_DARK] * n + [FOREST, AMBER]

    fig_vol = go.Figure(go.Bar(
        x             = vol_labels,
        y             = vol_vals,
        marker_color  = vol_colors,
        text          = [f"{v:.1f}%" for v in vol_vals],
        textposition  = "outside",
        textfont      = dict(color=FOREST),
    ))
    fig_vol.update_layout(
        **_CHART_BASE,
        title       = dict(text="Annualized Volatility — Assets vs. Portfolios",
                           font=dict(color=FOREST, size=15)),
        yaxis_title = "Ann. Volatility (%)",
        height      = 360,
        showlegend  = False,
    )
    st.plotly_chart(fig_vol, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Correlations
# ══════════════════════════════════════════════════════════════════════════════
with tab_corr:
    corr = ret.corr()

    # Diverging scale: blue (negative) → cream (zero) → forest (positive)
    corr_scale = [
        [0.0,  "#2c5f8a"],
        [0.5,  CREAM_LIGHT],
        [1.0,  FOREST],
    ]

    fig_corr = go.Figure(go.Heatmap(
        z            = corr.values,
        x            = valid,
        y            = valid,
        colorscale   = corr_scale,
        zmid=0, zmin=-1, zmax=1,
        text         = [[f"{v:.2f}" for v in row] for row in corr.values],
        texttemplate = "%{text}",
        textfont     = dict(size=11, color="white"),
        colorbar     = dict(
            title     = "Corr.",
            thickness = 14,
            tickfont  = dict(size=10),
        ),
    ))
    fig_corr.update_layout(
        **_CHART_BASE,
        title  = dict(text="Asset Correlation Matrix · Monthly Log Returns",
                      font=dict(color=FOREST, size=15)),
        height = max(380, n * 55 + 120),
    )
    st.plotly_chart(fig_corr, use_container_width=True)
    st.caption(
        "Gold = strong positive correlation (assets move together). "
        "Blue = negative correlation (diversification benefit). "
        "Note: Ledoit-Wolf shrinkage is applied to the covariance matrix used for optimisation, not to this display."
    )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Historical Returns
# ══════════════════════════════════════════════════════════════════════════════
with tab_hist:
    # Cumulative total returns from monthly log-return series
    monthly_px = prices.resample("ME").last()
    start_date = monthly_px.index[0]

    # Portfolio cumulative returns (prepend 0% at start date)
    def _cum_ret_pct(w: np.ndarray) -> pd.Series:
        cr = (np.exp(np.cumsum(ret.values @ w)) - 1) * 100
        s  = pd.Series(
            np.concatenate([[0.0], cr]),
            index=pd.DatetimeIndex([start_date, *ret.index]),
        )
        return s

    opt_cum = _cum_ret_pct(opt_w)
    eq_cum  = _cum_ret_pct(eq_w)

    # Individual assets (simple total return)
    asset_cum = (monthly_px / monthly_px.iloc[0] - 1) * 100

    fig_h = go.Figure()

    ASSET_COLORS = [
        "#2c5f8a", "#c0392b", "#2d6a4f", "#b5702a",
        "#6c3483", "#1a5276", "#7d6608", "#78281f",
    ]
    for i, t in enumerate(valid):
        fig_h.add_trace(go.Scatter(
            x    = asset_cum.index,
            y    = asset_cum[t],
            mode = "lines",
            name = t,
            line = dict(color=ASSET_COLORS[i % len(ASSET_COLORS)], width=1.5),
            opacity = 0.65,
        ))

    # Equal weight
    fig_h.add_trace(go.Scatter(
        x    = eq_cum.index, y = eq_cum,
        mode = "lines", name = "Equal Weight",
        line = dict(color=AMBER, width=2, dash="dash"),
    ))

    # Optimal portfolio — prominent gold line
    fig_h.add_trace(go.Scatter(
        x    = opt_cum.index, y = opt_cum,
        mode = "lines", name = opt_label,
        line = dict(color=FOREST, width=3),
    ))

    fig_h.add_hline(y=0, line_color=CREAM_DARK, line_width=1)
    fig_h.update_layout(
        **_CHART_BASE,
        title       = dict(
            text=f"Cumulative Returns · {lookback_label} Lookback  ⚠ In-sample",
            font=dict(color=FOREST, size=15),
        ),
        xaxis_title = "Date",
        yaxis_title        = "Cumulative Return (%)",
        yaxis_ticksuffix   = "%",
        height             = 470,
        legend      = dict(bgcolor=CREAM_LIGHT, bordercolor=FOREST, borderwidth=1,
                           font=dict(color=FOREST)),
        hovermode   = "x unified",
    )
    st.plotly_chart(fig_h, use_container_width=True)
    st.caption(
        "⚠️ **In-sample results.** The optimal weights were derived from this same data period. "
        "Historical returns shown here are not a forecast of future performance."
    )


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "**Garrison Financial Group** · [gfg.finance](https://gfg.finance) · "
    "Optimisation: Markowitz mean-variance with Ledoit-Wolf shrinkage covariance · "
    "Historical return estimates are noisy — treat results as a starting point, not a prescription. "
    "For educational and illustrative purposes only — consult a licensed financial advisor."
)

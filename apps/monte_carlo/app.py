"""
Monte Carlo Retirement Simulator
Garrison Financial Group — gfg.finance

All values expressed in today's purchasing power (real terms).
5,000 simulated futures via log-normal, Cholesky-correlated stock/bond returns.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────────────────────────────────────
# Page config  ← must be the first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Monte Carlo Retirement Simulator | GFG",
    page_icon="📈",
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
GREEN        = "#2d6a4f"
AMBER        = "#b5702a"
RED          = "#c0392b"

st.markdown(
    f"""
    <style>
    /* ── backgrounds ── */
    [data-testid="stAppViewContainer"] {{background-color:{CREAM}; color:{FOREST};}}
    [data-testid="stHeader"]           {{background-color:{CREAM};}}
    [data-testid="stSidebar"]          {{background-color:{CREAM_LIGHT};}}
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{color:#4a5c4e;}}

    /* ── headings ── */
    h1 {{color:{CREAM_DARK}; font-family:'Georgia',serif; letter-spacing:0.02em;}}
    h2, h3, h4 {{color:{FOREST_MID};}}

    /* ── big headline number ── */
    .gfg-headline        {{text-align:center; padding:1.2rem 0 0.4rem;}}
    .gfg-headline .value {{font-size:5rem; font-weight:700; line-height:1;}}
    .gfg-headline .label {{font-size:1.05rem; color:#4a5c4e; margin-top:0.35rem;}}
    .col-green {{color:{GREEN};}}
    .col-amber {{color:{AMBER};}}
    .col-red   {{color:{RED};}}

    /* ── metric cards ── */
    [data-testid="metric-container"] {{
        background:{CREAM_LIGHT}; border-radius:8px; padding:0.8rem 1rem;
        border:1px solid {CREAM_DARK};
    }}
    [data-testid="stMetricValue"] {{color:{FOREST};}}
    [data-testid="stMetricLabel"] {{color:#4a5c4e;}}

    /* ── number inputs ── */
    .stNumberInput div[data-baseweb="input"] > div {{
        background-color: {FOREST};
        border-color: {FOREST_LIGHT};
    }}
    .stNumberInput input {{color: {CREAM_LIGHT};}}
    div.stNumberInput button {{
        color: {CREAM_LIGHT}; /* Change icon color */
        background-color: {FOREST_LIGHT}; /* Change button background color */
    }}
    div.stNumberInput button:hover {{
        background-color: {RED};
    }}
    
    /* ── misc ── */
    hr {{border-color:{CREAM_DARK};}}
    </style>
    """,
    unsafe_allow_html=True,
)

# [data-baseweb="input"] {{foreground-color:{CREAM};background-color:{FOREST};}}

# ─────────────────────────────────────────────────────────────────────────────
# Simulation constants
# ─────────────────────────────────────────────────────────────────────────────
N_SIMS          = 10_000
STOCK_BOND_CORR = -0.15   # long-run stock / bond correlation


# ─────────────────────────────────────────────────────────────────────────────
# Core simulation (cached — reruns only on changed inputs)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(show_spinner=False)
def run_simulation(
    *,
    current_age: int,
    retirement_age: int,
    plan_to_age: int,
    portfolio_value: float,
    annual_contribution: float,
    annual_spending: float,
    ss_annual: float,
    ss_start_age: int,
    stock_alloc: float,        # 0–1
    inflation: float,          # annual, decimal
    stock_return: float,       # nominal annual, decimal
    stock_vol: float,          # annual, decimal
    bond_return: float,
    bond_vol: float,
    seed: int,
) -> np.ndarray:
    """
    Vectorised Monte Carlo retirement simulation.

    Returns
    -------
    portfolio : np.ndarray, shape (N_SIMS, total_months + 1)
        Monthly portfolio value for every simulation path,
        expressed in today's purchasing power (real terms).
    """
    rng = np.random.default_rng(seed)

    total_months = (plan_to_age    - current_age) * 12
    bond_alloc   = 1.0 - stock_alloc

    # ── Nominal → real (inflation-adjusted) annualised returns ──────────────
    real_stock = (1 + stock_return) / (1 + inflation) - 1
    real_bond  = (1 + bond_return)  / (1 + inflation) - 1

    # ── Monthly mean & volatility ────────────────────────────────────────────
    ms = real_stock / 12
    mb = real_bond  / 12
    vs = stock_vol  / np.sqrt(12)
    vb = bond_vol   / np.sqrt(12)

    # ── Log-normal drift parameters ──────────────────────────────────────────
    # Model log(1+r) ~ N(mu, sigma²) so that E[1+r] = 1 + monthly_mean.
    # E[exp(X)] = exp(mu + 0.5·sigma²)  →  mu = log(1+m) - 0.5·sigma²
    mu_s = np.log(1 + ms) - 0.5 * vs ** 2
    mu_b = np.log(1 + mb) - 0.5 * vb ** 2

    # ── Cholesky decomposition for correlated stock / bond draws ────────────
    cov_mat = np.array([
        [vs ** 2,                    STOCK_BOND_CORR * vs * vb],
        [STOCK_BOND_CORR * vs * vb,  vb ** 2                  ],
    ])
    L  = np.linalg.cholesky(cov_mat)               # lower-triangular (2×2)
    z  = rng.standard_normal((N_SIMS, total_months, 2))    # (S, T, 2)
    zc = z @ L.T                                           # correlated normals
    r_s = np.exp(mu_s + zc[:, :, 0]) - 1                  # stock returns (S,T)
    r_b = np.exp(mu_b + zc[:, :, 1]) - 1                  # bond  returns (S,T)

    # Blended portfolio return each month
    r_p = stock_alloc * r_s + bond_alloc * r_b             # (S, T)

    # ── Monthly cash-flow schedule (constant in real / today's dollars) ─────
    #   Accumulation phase : add monthly contribution
    #   Retirement phase   : subtract spending net of SS / pension income
    ages_t    = current_age + np.arange(total_months) / 12
    in_retire = ages_t >= retirement_age
    ss_active = ages_t >= ss_start_age

    cf = np.where(
        in_retire,
        -(annual_spending / 12 - np.where(ss_active, ss_annual / 12, 0.0)),
        annual_contribution / 12,
    )   # shape (T,) — same for all simulation paths

    # ── Vectorised forward simulation ───────────────────────────────────────
    portfolio       = np.empty((N_SIMS, total_months + 1))
    portfolio[:, 0] = portfolio_value

    for t in range(total_months):
        val = portfolio[:, t] * (1.0 + r_p[:, t]) + cf[t]
        # Once a portfolio reaches $0 it stays there (ruin)
        portfolio[:, t + 1] = np.maximum(val, 0.0)

    return portfolio


# ─────────────────────────────────────────────────────────────────────────────
# Metric helpers
# ─────────────────────────────────────────────────────────────────────────────
def success_rate(portfolio: np.ndarray, floor: float = 0.0) -> float:
    """
    Fraction of paths where the final balance exceeds the floor.

    With no legacy floor the criterion is final > 0 (portfolio not depleted).
    With a legacy floor the criterion is final >= floor.
    """
    if floor > 0:
        return float(np.mean(portfolio[:, -1] >= floor))
    return float(np.mean(portfolio[:, -1] > 0.0))


def ruin_rate(portfolio: np.ndarray) -> float:
    """Fraction of paths where the portfolio ever reaches $0 after month 0."""
    return float(np.mean(np.min(portfolio[:, 1:], axis=1) <= 0.0))


def fmt_dollar(v: float) -> str:
    return f"${v:,.0f}"


def fmt_pct(v: float) -> str:
    return f"{v * 100:.1f}%"


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar — all user inputs
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### :color[Garrison Financial Group]{foreground="+FOREST+"}")
    st.caption(":color[Monte Carlo Retirement Simulator]{foreground="+FOREST_MID+"}")
    st.divider()

    st.subheader(":color[Your Situation]{foreground="+FOREST+"}")
    current_age     = st.number_input("Current age",           18,  80,     35,    1)
    portfolio_value = st.number_input(
        "Current portfolio ($)", 0, 10_000_000, 150_000, 5_000, format="%d"
    )
    annual_contrib  = st.number_input(
        "Annual contribution ($)", 0, 500_000, 20_000, 1_000, format="%d"
    )

    st.subheader(":color[Retirement Plan]{foreground="+FOREST+"}")
    retirement_age  = st.number_input(
        "Target retirement age", int(current_age) + 1, 80, 65, 1
    )
    annual_spending = st.number_input(
        "Annual spending in retirement (\$, today's \$)",
        10_000, 1_000_000, 80_000, 1_000, format="%d",
    )
    plan_to_age     = st.number_input(
        "Plan to age (longevity horizon)",
        int(retirement_age) + 1, 110, 90, 1,
    )

    st.subheader(":color[Additional Income in Retirement]{foreground="+FOREST+"}")
    ss_annual    = st.number_input(
        "Social Security / Pension (\$/yr, today's \$)",
        0, 200_000, 24_000, 1_000, format="%d",
    )
    ss_start_age = st.number_input(
        "Income starts at age", int(retirement_age), 85, 67, 1
    )

    st.subheader(":color[Portfolio Allocation]{foreground="+FOREST+"}")
    stock_pct   = st.slider("Stocks", 0, 100, 70, 5, format="%d%%")
    stock_alloc = stock_pct / 100
    st.caption(":color[Stocks "+str(stock_pct)+"% · Bonds "+str(100 - stock_pct)+"%]{foreground="+FOREST_LIGHT+"}")

    st.subheader(":color[Legacy Floor (optional)]{foreground="+FOREST+"}")
    legacy_floor = st.number_input(
        "Minimum ending balance ($, 0 = none)",
        0, 5_000_000, 0, 10_000, format="%d",
    )

    with st.expander("⚙️ Advanced Assumptions"):
        inflation    = st.number_input(
            "Inflation (%/yr)", 0.0, 15.0, 2.5, 0.1, format="%.1f"
        ) / 100
        st.markdown("**US Equities**")
        stock_return = st.number_input(
            "Expected return (%/yr)", 0.0, 30.0, 10.0, 0.1, key="sr", format="%.1f"
        ) / 100
        stock_vol    = st.number_input(
            "Volatility (%/yr)", 1.0, 60.0, 17.0, 0.1, key="sv", format="%.1f"
        ) / 100
        st.markdown("**US Bonds**")
        bond_return  = st.number_input(
            "Expected return (%/yr)", 0.0, 20.0, 4.5, 0.1, key="br", format="%.1f"
        ) / 100
        bond_vol     = st.number_input(
            "Volatility (%/yr)", 0.5, 30.0, 7.0, 0.1, key="bv", format="%.1f"
        ) / 100

    st.divider()

    # Reproducible seed with one-click randomise
    if "seed" not in st.session_state:
        st.session_state["seed"] = 53
    seed = int(st.number_input("Random seed", 0, 99_999, st.session_state["seed"]))
    st.session_state["seed"] = seed
    if st.button("New random seed", use_container_width=True):
        st.session_state["seed"] = int(np.random.randint(0, 99_999))
        st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Input validation
# ─────────────────────────────────────────────────────────────────────────────
if int(retirement_age) >= int(plan_to_age):
    st.error("⚠️ Plan-to age must be greater than retirement age.")
    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# Run simulation (cached by all inputs)
# ─────────────────────────────────────────────────────────────────────────────
sim_kwargs: dict = dict(
    current_age         = int(current_age),
    retirement_age      = int(retirement_age),
    plan_to_age         = int(plan_to_age),
    portfolio_value     = float(portfolio_value),
    annual_contribution = float(annual_contrib),
    annual_spending     = float(annual_spending),
    ss_annual           = float(ss_annual),
    ss_start_age        = int(ss_start_age),
    stock_alloc         = float(stock_alloc),
    inflation           = float(inflation),
    stock_return        = float(stock_return),
    stock_vol           = float(stock_vol),
    bond_return         = float(bond_return),
    bond_vol            = float(bond_vol),
    seed                = int(st.session_state["seed"]),
)

with st.spinner("Running 5,000 simulations…"):
    portfolio = run_simulation(**sim_kwargs)

# ── Derived statistics ────────────────────────────────────────────────────────
total_months  = (int(plan_to_age) - int(current_age)) * 12
ages          = np.linspace(int(current_age), int(plan_to_age), total_months + 1)
final_vals    = portfolio[:, -1]
pX            = {p: np.percentile(portfolio, p, axis=0) for p in (10, 25, 50, 75, 90)}

sr_val       = success_rate(portfolio, float(legacy_floor))
rr_val       = ruin_rate(portfolio)
sr_pct       = sr_val * 100
median_final = float(np.median(final_vals))
p10_final    = float(np.percentile(final_vals, 10))
p90_final    = float(np.percentile(final_vals, 90))
prob_double  = float(np.mean(final_vals >= 2 * portfolio_value))
median_peak  = float(np.median(np.max(portfolio, axis=1)))

# ─────────────────────────────────────────────────────────────────────────────
# ── MAIN LAYOUT ──────────────────────────────────────────────────────────────
# ─────────────────────────────────────────────────────────────────────────────
st.title("Monte Carlo Retirement Simulator")
st.caption(
    f"*All values in today's purchasing power (real terms) · "
    f"{N_SIMS:,} simulated futures · "
    f"Accumulation ages {int(current_age)}–{int(retirement_age)} · "
    f"Retirement ages {int(retirement_age)}–{int(plan_to_age)}*"
)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Headline success rate
# ─────────────────────────────────────────────────────────────────────────────
css_color   = "col-green" if sr_pct >= 80 else ("col-amber" if sr_pct >= 60 else "col-red")
floor_label = f" — ending ≥ {fmt_dollar(legacy_floor)}" if legacy_floor > 0 else ""

st.markdown(
    f"""
    <div class="gfg-headline">
      <div class="value {css_color}">{sr_pct:.1f}%</div>
      <div class="label">Probability of Success{floor_label}</div>
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("")   # spacer

# Secondary metrics
c1, c2, c3, c4 = st.columns(4)
c1.metric("Median final balance",       fmt_dollar(median_final))
c2.metric("10th pctl final balance",    fmt_dollar(p10_final))
c3.metric("Probability of ruin",        fmt_pct(rr_val))
c4.metric("Prob. doubling real wealth", fmt_pct(prob_double))

st.divider()

# ─────────────────────────────────────────────────────────────────────────────
# 2. Fan chart — percentile bands over time
# ─────────────────────────────────────────────────────────────────────────────
fig_fan = go.Figure()


def _add_band(lo: int, hi: int, alpha: float, name: str) -> None:
    fig_fan.add_trace(go.Scatter(
        x          = np.concatenate([ages, ages[::-1]]),
        y          = np.concatenate([pX[hi], pX[lo][::-1]]),
        fill       = "toself",
        fillcolor  = f"rgba(15,33,20,{alpha})",
        line       = dict(width=0),
        name       = name,
        hoverinfo  = "skip",
        showlegend = True,
    ))


_add_band(10, 90, 0.12, "10th – 90th pctl")
_add_band(25, 75, 0.26, "25th – 75th pctl")

fig_fan.add_trace(go.Scatter(
    x=ages, y=pX[50], mode="lines",
    line=dict(color=FOREST, width=2.5),
    name="Median",
))

# Accumulation vs retirement phase shading
fig_fan.add_vrect(
    x0=int(current_age), x1=int(retirement_age),
    fillcolor="rgba(202,198,176,0.45)", layer="below", line_width=0,
    annotation_text="Accumulation", annotation_position="top left",
    annotation_font=dict(color="#888", size=11),
)
fig_fan.add_vrect(
    x0=int(retirement_age), x1=int(plan_to_age),
    fillcolor="rgba(232,229,214,0.55)", layer="below", line_width=0,
    annotation_text="Retirement", annotation_position="top left",
    annotation_font=dict(color="#888", size=11),
)

# Retirement date vertical marker
fig_fan.add_vline(
    x=int(retirement_age),
    line_dash="dash", line_color=FOREST_MID, line_width=1.5,
    annotation_text=f"Retire {int(retirement_age)}",
    annotation_position="top right",
    annotation_font=dict(color=FOREST_MID, size=12),
)

fig_fan.update_layout(
    title       = dict(
        text=f"Portfolio Value Over Time · All values in today's dollars",
        font=dict(color=FOREST, size=16),
    ),
    xaxis       = dict(title="Age", title_font=dict(color=FOREST_MID), tickfont=dict(color=FOREST_LIGHT), gridcolor=CREAM_DARK),
    yaxis       = dict(title="Portfolio Value", title_font=dict(color=FOREST_MID), tickfont=dict(color=FOREST_LIGHT), tickformat="$,.0f", gridcolor=CREAM_DARK),
    paper_bgcolor = CREAM,
    plot_bgcolor  = CREAM_LIGHT,
    font          = dict(color=FOREST, size=12),
    legend        = dict(
        bgcolor=CREAM_LIGHT, bordercolor=FOREST, borderwidth=1,
        font=dict(color=FOREST),
    ),
    hovermode     = "x unified",
    height        = 470,
    margin        = dict(l=60, r=30, t=60, b=50),
)
st.plotly_chart(fig_fan, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# 3. Terminal value histogram
# ─────────────────────────────────────────────────────────────────────────────
fig_hist = go.Figure()
fig_hist.add_trace(go.Histogram(
    x                 = final_vals,
    nbinsx            = 80,
    marker_color      = FOREST_MID,
    marker_line_color = CREAM,
    marker_line_width = 0.6,
    opacity           = 0.82,
    name              = "Final balance",
))

fig_hist.add_vline(
    x=0, line_color=RED, line_width=2,
    annotation_text="Ruin ($0)",
    annotation_position="top right",
    annotation_font=dict(color=RED, size=12),
)

if legacy_floor > 0:
    fig_hist.add_vline(
        x=float(legacy_floor),
        line_color=FOREST_MID, line_dash="dash", line_width=1.5,
        annotation_text=f"Legacy floor {fmt_dollar(legacy_floor)}",
        annotation_position="top left",
        annotation_font=dict(color=FOREST_MID, size=11),
    )

fig_hist.update_layout(
    title       = dict(
        text=f"Distribution of Final Portfolio Values at Age {int(plan_to_age)} · Today's Dollars",
        font=dict(color=FOREST, size=16),
    ),
    xaxis       = dict(title="Final Portfolio Value", title_font=dict(color=FOREST_MID), tickfont=dict(color=FOREST_LIGHT), tickformat="$,.0f", gridcolor=CREAM_DARK),
    yaxis       = dict(title="Number of simulations", title_font=dict(color=FOREST_MID), tickfont=dict(color=FOREST_LIGHT), gridcolor=CREAM_DARK),
    paper_bgcolor = CREAM,
    plot_bgcolor  = CREAM_LIGHT,
    font          = dict(color=FOREST, size=12),
    height        = 390,
    margin        = dict(l=60, r=30, t=60, b=50),
)
st.plotly_chart(fig_hist, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# 4. Key statistics table
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Key Statistics")
stats_df = pd.DataFrame({
    "Metric": [
        "Probability of success",
        "Probability of ruin (portfolio reaches $0)",
        "Median final balance",
        "10th percentile final balance  (worst 10% of outcomes)",
        "90th percentile final balance  (best 10% of outcomes)",
        "Probability of doubling real wealth",
        "Median peak portfolio value",
    ],
    "Result": [
        fmt_pct(sr_val),
        fmt_pct(rr_val),
        fmt_dollar(median_final),
        fmt_dollar(p10_final),
        fmt_dollar(p90_final),
        fmt_pct(prob_double),
        fmt_dollar(median_peak),
    ],
})

def alternate_rows(row):
    # Determine if row index is even or odd
    if row.name % 2 == 0:
        return [f'background-color: {CREAM_DARK}'] * len(row)
    else:
        return [f'background-color: {CREAM_LIGHT}'] * len(row)

stats_styled = stats_df.style.set_table_styles([
        {'selector': 'th.col_heading', 'props': [
            ('background-color', FOREST_LIGHT),
            ('color', CREAM_LIGHT),
        ]}
    ]).set_properties(**{
        'background-color': CREAM_LIGHT,
        'color': FOREST_MID,
        'border': '1px solid',
        'border-color': FOREST_LIGHT,
    }).apply(alternate_rows, axis=1)

st.table(stats_styled, hide_index=True)
# st.dataframe(stats_styled, use_container_width=True, hide_index=True)

# st.markdown(
#     stats_df.style.set_table_styles([
#         {'selector': 'th.col_heading', 'props': [
#             ('background-color', FOREST_LIGHT),
#             ('color', CREAM_LIGHT),
#         ]}
#     ]).set_properties(**{
#         'background-color': CREAM_LIGHT,
#         'color': FOREST_MID,
#         'border-color': FOREST_LIGHT,
#     }).to_html(),
#     unsafe_allow_html=True
# )

# ─────────────────────────────────────────────────────────────────────────────
# 5. Sensitivity analysis
# ─────────────────────────────────────────────────────────────────────────────
st.subheader("Sensitivity Analysis")
st.caption("How the probability of success changes as one variable shifts. All other inputs held constant.")


def _sens(override_key: str, override_val: float | int) -> float:
    """Run one sensitivity scenario (cached via run_simulation) and return success rate."""
    kw = {**sim_kwargs, override_key: override_val}
    p  = run_simulation(**kw)
    return success_rate(p, float(legacy_floor))


tab_age, tab_spend, tab_contrib = st.tabs([
    "Retirement Age",
    "Annual Spending",
    "Annual Contribution",
])

# ── Tab 1: Retirement age ─────────────────────────────────────────────────────
with tab_age:
    ra_base  = int(retirement_age)
    ra_tests = sorted({
        max(int(current_age) + 1, ra_base + d)
        for d in (-5, -3, -1, 0, 2, 5)
        if max(int(current_age) + 1, ra_base + d) < int(plan_to_age)
    })
    rows: list[dict] = []
    for ra in ra_tests:
        rows.append({
            "Retirement Age"      : ra,
            "Yrs accumulating"    : ra - int(current_age),
            "Yrs in retirement"   : int(plan_to_age) - ra,
            "Success Rate"        : fmt_pct(_sens("retirement_age", ra)),
            ""                    : "◀ base" if ra == ra_base else "",
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# ── Tab 2: Annual spending ────────────────────────────────────────────────────
with tab_spend:
    sp_base   = float(annual_spending)
    sp_deltas = (-0.20, -0.10, -0.05, 0.0, 0.05, 0.10, 0.20)
    rows2: list[dict] = []
    for d in sp_deltas:
        v = sp_base * (1 + d)
        rows2.append({
            "Annual Spending" : fmt_dollar(v),
            "vs Base"         : f"{d * 100:+.0f}%",
            "Success Rate"    : fmt_pct(_sens("annual_spending", v)),
            ""                : "◀ base" if d == 0.0 else "",
        })
    st.dataframe(pd.DataFrame(rows2), use_container_width=True, hide_index=True)

# ── Tab 3: Annual contribution ────────────────────────────────────────────────
with tab_contrib:
    co_base   = float(annual_contrib)
    co_deltas = (-0.50, -0.25, -0.10, 0.0, 0.10, 0.25, 0.50)
    rows3: list[dict] = []
    for d in co_deltas:
        v = co_base * (1 + d)
        rows3.append({
            "Annual Contribution" : fmt_dollar(v),
            "vs Base"             : f"{d * 100:+.0f}%",
            "Success Rate"        : fmt_pct(_sens("annual_contribution", v)),
            ""                    : "◀ base" if d == 0.0 else "",
        })
    st.dataframe(pd.DataFrame(rows3), use_container_width=True, hide_index=True)

# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "**Garrison Financial Group** · [gfg.finance](https://gfg.finance) · "
    "Results are probabilistic projections, not guaranteed outcomes. "
    "All dollar values expressed in today's purchasing power (real, inflation-adjusted). "
    "For educational and illustrative purposes only — "
    "consult a licensed financial advisor before making investment decisions."
)

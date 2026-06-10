"""
Macro Dashboard
Garrison Financial Group — gfg.finance

Live US macroeconomic indicators via the FRED API.
Yield curve, labour market, inflation, money supply, and consumer sentiment,
with a three-signal recession composite.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from fredapi import Fred

# ─────────────────────────────────────────────────────────────────────────────
# Page config  ← must be first Streamlit call
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Macro Dashboard | GFG",
    page_icon="🌐",
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
BLUE         = "#2c5f8a"

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
    hr {{border-color:{CREAM_DARK};}}

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
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Shared chart defaults — NO xaxis/yaxis here to avoid duplicate-kwarg errors
# ─────────────────────────────────────────────────────────────────────────────
_CB = dict(
    paper_bgcolor = CREAM,
    plot_bgcolor  = CREAM_LIGHT,
    font          = dict(color=FOREST, size=12),
    margin        = dict(l=60, r=40, t=55, b=50),
    legend        = dict(bgcolor=CREAM_LIGHT, bordercolor=FOREST, borderwidth=1,
                         font=dict(color=FOREST)),
    hovermode     = "x unified",
)
# Reusable axis style dict
_AX = dict(gridcolor=CREAM_DARK, zerolinecolor=CREAM_DARK, zerolinewidth=1, title_font=dict(color=FOREST_MID), tickfont=dict(color=FOREST_LIGHT))

LOOKBACK_MAP = {"2 yr": 2, "5 yr": 5, "10 yr": 10, "Max": None}

# ─────────────────────────────────────────────────────────────────────────────
# FRED API — initialise once; stop with a clear message if key is missing
# ─────────────────────────────────────────────────────────────────────────────
try:
    _API_KEY = st.secrets["FRED_API_KEY"]
    Fred(api_key=_API_KEY)   # validate key is present (doesn't make a request)
except Exception:
    st.title("Macro Dashboard")
    st.error(
        "**FRED API key not configured.**\n\n"
        "Add your key to Streamlit Cloud → Settings → Secrets:\n"
        "```\nFRED_API_KEY = \"your_key_here\"\n```\n"
        "Get a free key at [fred.stlouisfed.org/docs/api/api_key.html]"
        "(https://fred.stlouisfed.org/docs/api/api_key.html)."
    )
    st.stop()


# ─────────────────────────────────────────────────────────────────────────────
# Data fetching — one cached function per series so failures are isolated
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_data(ttl=3_600, show_spinner=False)
def _fetch(series_id: str, api_key: str) -> pd.Series | None:
    """Fetch a FRED series. Returns None on any failure."""
    try:
        s = Fred(api_key=api_key).get_series(series_id)
        if s is None or s.empty:
            return None
        s.index = pd.to_datetime(s.index)
        return s.dropna()
    except Exception:
        return None


def fetch(sid: str) -> pd.Series | None:
    return _fetch(sid, _API_KEY)


# ─────────────────────────────────────────────────────────────────────────────
# Data helpers
# ─────────────────────────────────────────────────────────────────────────────
def _monthly(s: pd.Series | None) -> pd.Series | None:
    if s is None or s.empty:
        return None
    return s.resample("ME").last().dropna()


def _yoy(s: pd.Series | None) -> pd.Series | None:
    """Month-end resample then 12-period % change."""
    m = _monthly(s)
    return None if m is None else m.pct_change(12).mul(100).dropna()


def _mom(s: pd.Series | None) -> pd.Series | None:
    """Month-end resample then 1-period difference."""
    m = _monthly(s)
    return None if m is None else m.diff(1).dropna()


def _cut(s: pd.Series | None, cutoff: pd.Timestamp | None) -> pd.Series | None:
    if s is None or s.empty:
        return None
    if cutoff is None:
        return s
    return s[s.index >= cutoff]


def _fresh(s: pd.Series | None, max_days: int = 90) -> bool:
    """Return True if the series has a recent observation."""
    if s is None or s.empty:
        return False
    return (pd.Timestamp.now() - s.index[-1]).days <= max_days


def _latest(s: pd.Series | None) -> float | None:
    return None if (s is None or s.empty) else float(s.iloc[-1])


def _delta_1y(s: pd.Series | None) -> float | None:
    """Value 12 months ago (monthly series)."""
    if s is None or len(s) < 13:
        return None
    m = _monthly(s)
    if m is None or len(m) < 13:
        return None
    return float(m.iloc[-13])


def _cutoff(years: int | None) -> pd.Timestamp | None:
    return None if years is None else pd.Timestamp.now() - pd.DateOffset(years=years)


# ─────────────────────────────────────────────────────────────────────────────
# Recession shading
# ─────────────────────────────────────────────────────────────────────────────
def add_recession_shading(
    fig: go.Figure,
    usrec: pd.Series | None,
    cutoff: pd.Timestamp | None,
    secondary_y: bool = False,
) -> None:
    """Shade NBER recession periods on a Plotly figure."""
    if usrec is None or usrec.empty:
        return
    rec = _monthly(usrec)
    if rec is None:
        return
    rec = rec.fillna(0)
    if cutoff is not None:
        rec = rec[rec.index >= cutoff]
    if rec.empty:
        return

    prev = 0
    start = None
    for date, val in rec.items():
        v = int(val)
        if v == 1 and prev == 0:
            start = date
        elif v == 0 and prev == 1 and start is not None:
            fig.add_vrect(
                x0=start, x1=date,
                fillcolor="rgba(200,200,200,0.07)",
                layer="below", line_width=0,
            )
            start = None
        prev = v
    # Recession ongoing at end of series
    if prev == 1 and start is not None:
        fig.add_vrect(
            x0=start, x1=rec.index[-1],
            fillcolor="rgba(200,200,200,0.07)",
            layer="below", line_width=0,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Signal badge HTML helpers
# ─────────────────────────────────────────────────────────────────────────────
def _composite_html(n_triggered: int) -> str:
    if n_triggered == 0:
        color, icon, label = GREEN, "🟢", "LOW"
    elif n_triggered == 1:
        color, icon, label = AMBER, "🟡", "ELEVATED"
    else:
        color, icon, label = RED, "🔴", "HIGH"
    return (
        f'<div style="text-align:center;background:{color}22;border:2px solid {color};'
        f'border-radius:12px;padding:1.4rem 1rem;margin-bottom:1.2rem;">'
        f'<div style="font-size:2.8rem;font-weight:700;color:{color};">{icon} {label}</div>'
        f'<div style="font-size:0.95rem;color:{FOREST_MID};margin-top:0.3rem;">'
        f'Recession Risk Composite — {n_triggered} of 3 signals triggered</div></div>'
    )


def _signal_card_html(
    label: str, value_str: str, triggered: bool, threshold: str, note: str
) -> str:
    color  = RED if triggered else GREEN
    icon   = "🔴" if triggered else "🟢"
    status = "TRIGGERED" if triggered else "CLEAR"
    return (
        f'<div style="background:{color}18;border:1px solid {color}55;border-radius:8px;'
        f'padding:1rem 1.1rem;height:100%;">'
        f'<div style="font-size:0.75rem;color:{FOREST_MID};text-transform:uppercase;'
        f'letter-spacing:0.08em;margin-bottom:0.25rem;">{label}</div>'
        f'<div style="font-size:1.5rem;font-weight:700;color:{color};">{icon} {status}</div>'
        f'<div style="font-size:0.85rem;color:{FOREST_MID};margin-top:0.4rem;">'
        f'<b>Current:</b> {value_str}<br><b>Threshold:</b> {threshold}</div>'
        f'<div style="font-size:0.78rem;color:{FOREST_LIGHT};margin-top:0.4rem;">{note}</div></div>'
    )


# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### :color[Garrison Financial Group]{foreground="+FOREST+"}")
    st.caption(":color[Macro Dashboard]{foreground="+FOREST_MID+"}")
    st.divider()

    lookback_label = st.selectbox(
        "Lookback period", list(LOOKBACK_MAP.keys()), index=2
    )
    years  = LOOKBACK_MAP[lookback_label]
    cutoff = _cutoff(years)

    show_rec = st.toggle("Show recession shading", value=True)

    st.divider()
    if st.button("🔄  Refresh data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.caption("Data refreshes automatically every hour.")


# ─────────────────────────────────────────────────────────────────────────────
# Fetch all series (failures return None — logged below as warnings)
# ─────────────────────────────────────────────────────────────────────────────
with st.spinner("Fetching data from FRED…"):
    raw_t10y2y   = fetch("T10Y2Y")
    raw_unrate   = fetch("UNRATE")
    raw_cpi      = fetch("CPIAUCSL")
    raw_core_cpi = fetch("CPILFESL")
    raw_sahm     = fetch("SAHMREALTIME")
    raw_usrec    = fetch("USREC")
    raw_m2       = fetch("M2SL")
    raw_payems   = fetch("PAYEMS")
    raw_sent     = fetch("UMCSENT")

# Warn about any failed fetches
_series_map = {
    "T10Y2Y": raw_t10y2y, "UNRATE": raw_unrate, "CPIAUCSL": raw_cpi,
    "CPILFESL": raw_core_cpi, "SAHMREALTIME": raw_sahm, "USREC": raw_usrec,
    "M2SL": raw_m2, "PAYEMS": raw_payems, "UMCSENT": raw_sent,
}
failed = [k for k, v in _series_map.items() if v is None]
if failed:
    st.warning(f"Could not fetch: {', '.join(failed)}. Some charts may be unavailable.")

stale = [k for k, v in _series_map.items() if v is not None and not _fresh(v)]
if stale:
    st.warning(f"Stale data (>90 days old) for: {', '.join(stale)}.")


# ─────────────────────────────────────────────────────────────────────────────
# Derived monthly series (full history — lookback applied per chart)
# ─────────────────────────────────────────────────────────────────────────────
t10y2y_m   = _monthly(raw_t10y2y)
unrate_m   = _monthly(raw_unrate)
cpi_yoy    = _yoy(raw_cpi)
core_yoy   = _yoy(raw_core_cpi)
sahm_m     = _monthly(raw_sahm)
m2_yoy     = _yoy(raw_m2)
payems_mom = _mom(raw_payems)
sent_m     = _monthly(raw_sent)


# ─────────────────────────────────────────────────────────────────────────────
# Recession signals
# ─────────────────────────────────────────────────────────────────────────────
# Signal 1: Yield curve inversion
yc_val       = _latest(t10y2y_m)
yc_triggered = yc_val is not None and yc_val < 0

# Signal 2: Sahm Rule
sahm_val       = _latest(sahm_m)
sahm_triggered = sahm_val is not None and sahm_val >= 0.5

# Signal 3: Consumer sentiment momentum (>1 std below 12m rolling mean)
sent_triggered = False
sent_threshold_str = "N/A"
if sent_m is not None and len(sent_m) >= 13:
    sent_mean12 = sent_m.rolling(12).mean()
    sent_std12  = sent_m.rolling(12).std()
    sent_lower  = sent_mean12 - sent_std12
    curr_sent   = _latest(sent_m)
    curr_lower  = float(sent_lower.iloc[-1]) if not sent_lower.empty else None
    if curr_sent is not None and curr_lower is not None:
        sent_triggered    = curr_sent < curr_lower
        sent_threshold_str = f"< {curr_lower:.1f} (mean − 1σ)"

n_triggered = sum([yc_triggered, sahm_triggered, sent_triggered])


# ─────────────────────────────────────────────────────────────────────────────
# Page header
# ─────────────────────────────────────────────────────────────────────────────
st.title("Macro Dashboard")
st.caption(
    f"*US macroeconomic indicators via FRED · "
    f"{lookback_label} lookback · "
    f"Data as of {pd.Timestamp.now().strftime('%B %d, %Y')}*"
)

# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab_ov, tab_yc, tab_lm, tab_inf, tab_ms = st.tabs([
    "🔭  Overview",
    "📉  Yield Curve",
    "👷  Labor Market",
    "📊  Inflation",
    "💵  Money & Sentiment",
])


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — Overview
# ══════════════════════════════════════════════════════════════════════════════
with tab_ov:

    # ── Composite signal badge ──
    st.markdown(_composite_html(n_triggered), unsafe_allow_html=True)

    # ── Individual signal cards ──
    sc1, sc2, sc3 = st.columns(3)
    with sc1:
        st.markdown(_signal_card_html(
            "Yield Curve (10Y−2Y)",
            f"{yc_val:+.2f}%" if yc_val is not None else "N/A",
            yc_triggered,
            "< 0% (inversion)",
            "6–24 month leading indicator",
        ), unsafe_allow_html=True)
    with sc2:
        st.markdown(_signal_card_html(
            "Sahm Rule",
            f"{sahm_val:.2f}" if sahm_val is not None else "N/A",
            sahm_triggered,
            "≥ 0.50",
            "Nearly coincident with recession onset",
        ), unsafe_allow_html=True)
    with sc3:
        sv_str = f"{_latest(sent_m):.1f}" if sent_m is not None else "N/A"
        st.markdown(_signal_card_html(
            "Consumer Sentiment Momentum",
            sv_str,
            sent_triggered,
            sent_threshold_str,
            "More than 1σ below 12-month rolling mean",
        ), unsafe_allow_html=True)

    st.caption(
        "Signals are indicators, not forecasts. Yield curve has a 6–24 month lead time; "
        "Sahm Rule is nearly coincident; sentiment is a soft leading indicator. "
        "NBER recession dating is retrospective — recession shading lags by 1–2 months."
    )

    st.divider()

    # ── KPI metric cards ──
    st.subheader("Key Indicators — Current vs. 1 Year Ago")

    def _kpi(label, series, fmt=".2f", suffix="", note=""):
        v = _latest(series)
        v1y = _delta_1y(series)
        if v is None:
            st.metric(label, "N/A")
        else:
            val_str = f"{v:{fmt}}{suffix}"
            delta_str = None
            if v1y is not None:
                d = v - v1y
                delta_str = f"{d:+{fmt}}{suffix} vs 1yr ago"
            st.metric(label, val_str, delta_str, help=note)

    r1c1, r1c2, r1c3, r1c4 = st.columns(4)
    with r1c1:
        _kpi("Yield Curve (10Y−2Y)", t10y2y_m, fmt=".2f", suffix="%",
             note="10-year minus 2-year Treasury yield. Negative = inversion.")
    with r1c2:
        _kpi("Unemployment Rate", unrate_m, fmt=".1f", suffix="%",
             note="U-3 unemployment rate (seasonally adjusted).")
    with r1c3:
        v = _latest(cpi_yoy)
        v1y = _delta_1y(cpi_yoy)
        if v is not None:
            d = (v - v1y) if v1y is not None else None
            r1c3.metric("CPI Inflation (YoY)",
                        f"{v:.1f}%",
                        f"{d:+.1f}pp vs 1yr ago" if d is not None else None,
                        help="CPI All Items, year-over-year % change.")
    with r1c4:
        _kpi("Sahm Rule Indicator", sahm_m, fmt=".2f",
             note="≥0.50 historically coincides with recession onset.")

    r2c1, r2c2, r2c3, r2c4 = st.columns(4)
    with r2c1:
        v = _latest(core_yoy)
        v1y = _delta_1y(core_yoy)
        if v is not None:
            d = (v - v1y) if v1y is not None else None
            r2c1.metric("Core CPI (YoY)",
                        f"{v:.1f}%",
                        f"{d:+.1f}pp vs 1yr ago" if d is not None else None,
                        help="CPI ex food & energy, year-over-year % change.")
    with r2c2:
        v = _latest(m2_yoy)
        v1y = _delta_1y(m2_yoy)
        if v is not None:
            d = (v - v1y) if v1y is not None else None
            r2c2.metric("M2 Growth (YoY)",
                        f"{v:.1f}%",
                        f"{d:+.1f}pp vs 1yr ago" if d is not None else None,
                        help="M2 money supply, year-over-year % change.")
    with r2c3:
        v = _latest(payems_mom)
        if v is not None:
            r2c3.metric("Payrolls (MoM Change)",
                        f"{v:+,.0f}K",
                        help="Nonfarm payrolls, monthly change in thousands.")
    with r2c4:
        _kpi("Consumer Sentiment", sent_m, fmt=".1f",
             note="UMich Consumer Sentiment Index. Long-run avg ≈ 85.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — Yield Curve
# ══════════════════════════════════════════════════════════════════════════════
with tab_yc:
    series = _cut(t10y2y_m, cutoff)
    if series is None or series.empty:
        st.warning("Yield curve data unavailable.")
    else:
        fig = go.Figure()
        if show_rec:
            add_recession_shading(fig, raw_usrec, cutoff)

        # Fill positive (normal) vs negative (inverted) regions
        fig.add_trace(go.Scatter(
            x=series.index, y=series.values,
            mode="lines", name="10Y−2Y Spread",
            line=dict(color=FOREST, width=2),
            fill="tozeroy",
            fillcolor="rgba(15,33,20,0.10)",
        ))

        # Zero line
        fig.add_hline(y=0, line_color=RED, line_dash="dash", line_width=1.5,
                      annotation_text="Inversion threshold",
                      annotation_position="bottom right",
                      annotation_font=dict(color=RED, size=11))

        # Current value callout
        if yc_val is not None:
            color_ann = RED if yc_triggered else GREEN
            fig.add_annotation(
                x=series.index[-1], y=yc_val,
                text=f"  Current: {yc_val:+.2f}%",
                showarrow=False,
                font=dict(color=color_ann, size=12),
                xanchor="left",
            )

        fig.update_layout(
            **_CB,
            title=dict(text="10-Year minus 2-Year Treasury Yield Spread",
                       font=dict(color=FOREST, size=15)),
            xaxis=dict(**_AX, title="Date"),
            yaxis=dict(**_AX, title="Spread (%)"),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "Grey shading = NBER recession periods (retrospective — typically confirmed 6–12 months after onset). "
            "Sustained inversion has preceded every US recession since the 1970s with a 6–24 month lead."
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — Labor Market
# ══════════════════════════════════════════════════════════════════════════════
with tab_lm:
    unrate_d = _cut(unrate_m, cutoff)
    sahm_d   = _cut(sahm_m, cutoff)
    payems_d = _cut(payems_mom, cutoff)

    # ── Chart 1: UNRATE + Sahm Rule (dual-axis) ──
    if unrate_d is not None or sahm_d is not None:
        fig_lm = make_subplots(specs=[[{"secondary_y": True}]])

        if show_rec:
            add_recession_shading(fig_lm, raw_usrec, cutoff)

        if unrate_d is not None:
            fig_lm.add_trace(go.Scatter(
                x=unrate_d.index, y=unrate_d.values,
                mode="lines", name="Unemployment Rate (%)",
                line=dict(color=FOREST, width=2),
            ), secondary_y=False)

        if sahm_d is not None:
            fig_lm.add_trace(go.Scatter(
                x=sahm_d.index, y=sahm_d.values,
                mode="lines", name="Sahm Rule Indicator",
                line=dict(color=BLUE, width=2),
            ), secondary_y=True)

            # 0.5 trigger line on secondary axis
            fig_lm.add_hline(
                y=0.5, line_color=AMBER, line_dash="dash", line_width=1.5,
                annotation_text="Sahm trigger (0.50)",
                annotation_position="top left",
                annotation_font=dict(color=AMBER, size=11),
            )

        fig_lm.update_layout(
            paper_bgcolor=CREAM, plot_bgcolor=CREAM_LIGHT,
            font=dict(color=FOREST, size=12),
            margin=dict(l=60, r=60, t=55, b=50),
            legend=dict(bgcolor=CREAM_LIGHT, bordercolor=FOREST, borderwidth=1,
                        font=dict(color=FOREST)),
            hovermode="x unified",
            title=dict(text="Unemployment Rate & Sahm Rule Indicator",
                       font=dict(color=FOREST, size=15)),
            height=380,
        )
        fig_lm.update_xaxes(**_AX)
        fig_lm.update_yaxes(title_text="Unemployment Rate (%)", **_AX, secondary_y=False)
        fig_lm.update_yaxes(title_text="Sahm Rule", **_AX, secondary_y=True,
                             showgrid=False)
        st.plotly_chart(fig_lm, use_container_width=True)
    else:
        st.warning("Labor market data unavailable.")

    # ── Chart 2: Nonfarm Payrolls MoM ──
    if payems_d is not None and not payems_d.empty:
        bar_colors = [GREEN if v >= 0 else RED for v in payems_d.values]
        fig_pay = go.Figure(go.Bar(
            x=payems_d.index, y=payems_d.values,
            marker_color=bar_colors,
            name="Payrolls MoM Change",
            hovertemplate="%{x|%b %Y}: %{y:+,.0f}K<extra></extra>",
        ))
        if show_rec:
            add_recession_shading(fig_pay, raw_usrec, cutoff)
        fig_pay.add_hline(y=0, line_color=CREAM_DARK, line_width=1)
        fig_pay.update_layout(
            **_CB,
            title=dict(text="Nonfarm Payrolls — Monthly Change (thousands)",
                       font=dict(color=FOREST, size=15)),
            xaxis=dict(**_AX, title="Date"),
            yaxis=dict(**_AX, title="Change (thousands)"),
            height=340,
            showlegend=False,
        )
        st.plotly_chart(fig_pay, use_container_width=True)
        st.caption(
            "Gold bars = job gains. Red bars = job losses. "
            "The Sahm Rule triggers when the 3-month moving average of unemployment "
            "rises ≥0.50pp above its prior 12-month low."
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — Inflation
# ══════════════════════════════════════════════════════════════════════════════
with tab_inf:
    cpi_d  = _cut(cpi_yoy,  cutoff)
    core_d = _cut(core_yoy, cutoff)

    if cpi_d is None and core_d is None:
        st.warning("Inflation data unavailable.")
    else:
        fig_inf = go.Figure()
        if show_rec:
            add_recession_shading(fig_inf, raw_usrec, cutoff)

        if cpi_d is not None:
            fig_inf.add_trace(go.Scatter(
                x=cpi_d.index, y=cpi_d.values,
                mode="lines", name="Headline CPI (YoY)",
                line=dict(color=FOREST, width=2.5),
            ))

        if core_d is not None:
            fig_inf.add_trace(go.Scatter(
                x=core_d.index, y=core_d.values,
                mode="lines", name="Core CPI (YoY, ex food & energy)",
                line=dict(color=BLUE, width=2, dash="dot"),
            ))

        # Fed 2% target
        fig_inf.add_hline(
            y=2.0, line_color=GREEN, line_dash="dash", line_width=1.5,
            annotation_text="Fed target (2%)",
            annotation_position="bottom right",
            annotation_font=dict(color=GREEN, size=11),
        )

        fig_inf.update_layout(
            **_CB,
            title=dict(text="CPI Inflation — Year-over-Year % Change",
                       font=dict(color=FOREST, size=15)),
            xaxis=dict(**_AX, title="Date"),
            yaxis=dict(**_AX, title="YoY % Change"),
            height=420,
        )
        st.plotly_chart(fig_inf, use_container_width=True)
        st.caption(
            "Headline CPI includes food and energy — more volatile. "
            "Core CPI (ex food & energy) is the Fed's closer watch series. "
            "The Fed's formal target is 2% PCE inflation; CPI typically runs ~0.3pp above PCE."
        )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — Money & Sentiment
# ══════════════════════════════════════════════════════════════════════════════
with tab_ms:
    m2_d   = _cut(m2_yoy,  cutoff)
    sent_d = _cut(sent_m,  cutoff)

    # ── M2 YoY chart ──
    if m2_d is not None and not m2_d.empty:
        bar_colors_m2 = [GREEN if v >= 0 else RED for v in m2_d.values]
        fig_m2 = go.Figure(go.Bar(
            x=m2_d.index, y=m2_d.values,
            marker_color=bar_colors_m2,
            name="M2 YoY %",
            hovertemplate="%{x|%b %Y}: %{y:+.1f}%<extra></extra>",
        ))
        if show_rec:
            add_recession_shading(fig_m2, raw_usrec, cutoff)
        fig_m2.add_hline(y=0, line_color=CREAM_DARK, line_width=1)
        fig_m2.update_layout(
            **_CB,
            title=dict(text="M2 Money Supply — Year-over-Year % Change",
                       font=dict(color=FOREST, size=15)),
            xaxis=dict(**_AX, title="Date"),
            yaxis=dict(**_AX, title="YoY % Change"),
            height=360,
            showlegend=False,
        )
        st.plotly_chart(fig_m2, use_container_width=True)
        st.caption(
            "Rapid M2 expansion has historically preceded inflation; contraction is associated "
            "with tighter financial conditions. The 2022 contraction was the sharpest since the 1930s."
        )
    else:
        st.warning("M2 data unavailable.")

    # ── Consumer Sentiment with rolling mean ± 1σ band ──
    if sent_d is not None and not sent_d.empty:
        sm = sent_m  # full history for rolling stats
        roll_mean = sm.rolling(12).mean() if sm is not None else None
        roll_std  = sm.rolling(12).std()  if sm is not None else None

        fig_sent = go.Figure()
        if show_rec:
            add_recession_shading(fig_sent, raw_usrec, cutoff)

        # ±1σ band (using full history, then cut for display)
        if roll_mean is not None and roll_std is not None:
            upper = _cut(roll_mean + roll_std, cutoff)
            lower = _cut(roll_mean - roll_std, cutoff)
            mean_d = _cut(roll_mean, cutoff)

            if upper is not None and lower is not None:
                fig_sent.add_trace(go.Scatter(
                    x=list(upper.index) + list(lower.index[::-1]),
                    y=list(upper.values) + list(lower.values[::-1]),
                    fill="toself",
                    fillcolor="rgba(15,33,20,0.10)",
                    line=dict(width=0),
                    name="±1σ band (12m)",
                    hoverinfo="skip",
                ))

            if mean_d is not None:
                fig_sent.add_trace(go.Scatter(
                    x=mean_d.index, y=mean_d.values,
                    mode="lines", name="12m rolling mean",
                    line=dict(color=AMBER, width=1.5, dash="dash"),
                ))

        fig_sent.add_trace(go.Scatter(
            x=sent_d.index, y=sent_d.values,
            mode="lines", name="Consumer Sentiment",
            line=dict(color=FOREST, width=2),
        ))

        fig_sent.update_layout(
            **_CB,
            title=dict(text="UMich Consumer Sentiment Index",
                       font=dict(color=FOREST, size=15)),
            xaxis=dict(**_AX, title="Date"),
            yaxis=dict(**_AX, title="Index Level"),
            height=360,
        )
        st.plotly_chart(fig_sent, use_container_width=True)
        st.caption(
            "Gold shading = ±1 standard deviation around the 12-month rolling mean. "
            "The recession signal triggers when the current reading falls below the lower band (mean − 1σ). "
            "Long-run average ≈ 85; readings below 60 historically coincide with recessions."
        )
    else:
        st.warning("Consumer sentiment data unavailable.")


# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "**Garrison Financial Group** · [gfg.finance](https://gfg.finance) · "
    "Data sourced from the Federal Reserve Bank of St. Louis (FRED). "
    "NBER recession dating is retrospective and may lag by 6–18 months. "
    "For educational and illustrative purposes only — consult a licensed financial advisor."
)

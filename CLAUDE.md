# Garrison Financial Group — Project Context

## Project Overview

A portfolio of interactive financial planning and data science tools built with Python and Streamlit, targeting financial planners and wealth managers. The goal is to demonstrate applied quantitative finance skills.

**Brand:** Garrison Financial Group
**Domain:** [gfg.finance](https://gfg.finance) — live and configured
**GitHub repo:** [github.com/mgptk/garrison-financial-group](https://github.com/mgptk/garrison-financial-group)
**GitHub Pages:** Served from `/docs` on the `main` branch — live and configured
**Developer:** Experienced data scientist with CFA Level I background; fluent in Python, new to Streamlit and web deployment.

---

## Current Status

| Item | Status |
|------|--------|
| Repo scaffolded | ✅ Done |
| .gitignore, README | ✅ Done |
| Landing page (HTML/CSS/JS) | ✅ Live at gfg.finance |
| CNAME + domain configured | ✅ Done |
| Monte Carlo — design & implementation | ✅ Done |
| Monte Carlo — deployed to Streamlit Cloud | ✅ Live at gfg-monte-carlo.streamlit.app |
| Monte Carlo — embedded in gfg.finance | ✅ Live at gfg.finance/monte-carlo.html |
| Portfolio Optimizer | ⏳ Next (see spec below) |
| Macro Dashboard | ⏳ After Portfolio Optimizer (needs FRED API key) |

---

## Repo Structure

```
garrison-financial-group/
├── CLAUDE.md                        ← This file
├── README.md
├── .gitignore                       ← Python + Streamlit tuned
├── .venv/                           ← Local virtualenv (not committed)
├── docs/                            ← GitHub Pages root → gfg.finance
│   ├── index.html                   ← Landing page with tool cards
│   ├── monte-carlo.html             ← ✅ Embedded app wrapper page
│   ├── CNAME                        ← "gfg.finance"
│   ├── css/style.css                ← Navy + gold design system
│   └── js/main.js                   ← Scroll animations
└── apps/
    ├── monte_carlo/                 ← ✅ Built & deployed
    │   ├── app.py
    │   └── requirements.txt
    ├── portfolio_optimizer/         ← ⏳ Next
    │   ├── app.py
    │   └── requirements.txt
    └── macro_dashboard/             ← ⏳ After that
        ├── app.py
        └── requirements.txt
```

---

## Tech Stack

- **Python 3.11+**
- **Streamlit ≥ 1.35** — app framework
- **NumPy / SciPy** — simulation and optimization
- **Pandas** — data handling
- **Plotly** — all charts (interactive, consistent across apps)
- **yfinance** — price data (Portfolio Optimizer)
- **fredapi** — FRED economic data (Macro Dashboard)

---

## Deployment Architecture

| Layer | Tool | Status |
|-------|------|--------|
| Landing page | GitHub Pages (`/docs`, `main` branch) | ✅ Live at gfg.finance |
| Custom domain | gfg.finance via Cloudflare Registrar | ✅ Live |
| DNS | Cloudflare (4 A records → GitHub IPs, CNAME www) | ✅ Configured |
| App hosting | Streamlit Community Cloud (free tier) | ✅ Monte Carlo live |

**GitHub Pages DNS records:**
- A records on `@`: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- CNAME on `www`: `mgptk.github.io`
- Cloudflare proxy: **DNS only** (grey cloud) — required for GitHub Pages HTTPS

### Deploying a new app (established pattern)

1. Build `apps/<name>/app.py` and `apps/<name>/requirements.txt`
2. Push to `main`
3. Go to [share.streamlit.io](https://share.streamlit.io) → New app → repo `mgptk/garrison-financial-group`, branch `main`, path `apps/<name>/app.py`
4. Set a clean URL slug in Streamlit Cloud (e.g. `gfg-portfolio-optimizer`)
5. Add any secrets in Streamlit Cloud dashboard (Settings → Secrets)
6. Create `docs/<name>.html` — embedded wrapper page (see pattern below)
7. Update the `<a href="#">` in the corresponding tool card in `docs/index.html` to point to `/<name>.html`
8. Push — GitHub Pages updates in ~60 seconds

### Embed pattern (IMPORTANT — use this exactly)

Each app gets a wrapper page at `docs/<name>.html`. The iframe sizing **must use JS-measured height**, not CSS flex/absolute — the browser's default iframe size is 300×150px and will show if CSS fails.

```html
<!-- In <head>: lock page scroll -->
<style>
  html, body { height: 100%; margin: 0; overflow: hidden; }
  #app-frame  { display: block; width: 100%; border: none; }
</style>

<!-- Markup: navbar + app-bar + bare iframe -->
<nav id="hdr-nav" class="navbar">…</nav>
<div id="hdr-bar" class="app-bar">…</div>
<iframe id="app-frame"
  src="https://<streamlit-url>/?embed=true"
  allow="clipboard-write">
</iframe>

<!-- JS: measure actual header heights, set iframe height in px -->
<script>
  function fitFrame() {
    var used = document.getElementById('hdr-nav').offsetHeight
             + document.getElementById('hdr-bar').offsetHeight;
    document.getElementById('app-frame').style.height =
      (window.innerHeight - used) + 'px';
  }
  fitFrame();
  window.addEventListener('resize', fitFrame);
</script>
```

`?embed=true` strips Streamlit's toolbar and footer, allowing clean iframe embedding.

**Live examples:**
- Monte Carlo wrapper: `docs/monte-carlo.html` → [gfg.finance/monte-carlo.html](https://gfg.finance/monte-carlo.html)
- Monte Carlo Streamlit: [gfg-monte-carlo.streamlit.app](https://gfg-monte-carlo.streamlit.app/)

---

## Landing Page (docs/)

Custom hand-coded HTML/CSS — **not** a site builder. Navy + gold color scheme.

**To add a new app to the landing page:**
1. Create `docs/<name>.html` (copy from `docs/monte-carlo.html`, update title/icon/src)
2. In `docs/index.html`, update the relevant tool card's `<a href="#">` to `/<name>.html`
3. No `target="_blank"` — keep navigation within gfg.finance

**Color palette (CSS variables in style.css):**
```css
--navy:       #0d1b2a
--navy-mid:   #1b2e45
--navy-light: #243b55
--gold:       #c9a84c
--gold-light: #e0c068
--text-muted: #8a9bb0
```

**App-bar chrome (shared across all embed pages):**  
`.app-bar`, `.app-bar-inner`, `.app-bar-back`, `.app-bar-title`, `.app-bar-external` are defined in `docs/css/style.css`. Layout and loading overlay go in a page-scoped `<style>` block inside each embed HTML file.

---

## Running Apps Locally

```bash
# From repo root, activate venv
.venv\Scripts\activate         # Windows
source .venv/bin/activate      # macOS/Linux

# Install deps for the app you're working on
pip install -r apps/monte_carlo/requirements.txt

# Run
streamlit run apps/monte_carlo/app.py
```

Streamlit hot-reloads on file save — no restart needed during development.

---

## App 1: Monte Carlo Retirement Simulator ✅ COMPLETE

**Live URL:** https://gfg-monte-carlo.streamlit.app/  
**Embedded at:** https://gfg.finance/monte-carlo.html  
**Source:** `apps/monte_carlo/app.py`

### What was built

A fully vectorised, 5,000-path Monte Carlo retirement simulator with:
- Monthly time steps, log-normal returns, Cholesky-correlated stock/bond draws
- All outputs in real (inflation-adjusted) terms — today's purchasing power
- Sidebar inputs, fan chart, terminal histogram, key stats, sensitivity tabs
- Navy + gold brand styling matching gfg.finance

### Implementation decisions (finalized)

#### Simulation mechanics
- **Time step:** Monthly (`annual ÷ 12` for mean, `÷ √12` for vol)
- **Return distribution:** Log-normal — `log(1+r) ~ N(μ, σ²)` where `μ = log(1+m) − 0.5σ²` ensures `E[1+r] = 1 + monthly_mean`. Prevents negative portfolio values, reflects compounding correctly.
- **Simulations:** 5,000 (vectorised with NumPy — runs in ~160 ms)
- **Correlation:** Cholesky decomposition on 2×2 stock/bond covariance matrix

#### Asset model
- Stock/bond split — user sets allocation via slider
- Stock–bond correlation hardcoded at **−0.15**
- Default assumptions (nominal, annualised):
  - US Equities: 10.0% return, 17.0% vol
  - US Bonds: 4.5% return, 7.0% vol
- All editable in Advanced expander — not surfaced by default

#### Inflation
- All simulation logic in **real terms** — nominal returns converted before simulation
- `real_return = (1 + nominal) / (1 + inflation) − 1`
- Default inflation: **2.5%**, user-editable
- All chart labels read "Today's Dollars"

#### Withdrawal strategy
- **Fixed real withdrawal** — annual spending constant in today's dollars
- Conservative by design (no dynamic/guardrails — v2 feature)
- SS/pension income offsets withdrawals; configurable start age

#### Success definition
- **`success_rate`**: fraction of paths where `final_balance > 0` (strictly greater — portfolios are floored at $0, so `>= 0` would always be 100%)
- With legacy floor: `final_balance >= floor`
- **`ruin_rate`**: fraction of paths where `min(portfolio[:, 1:]) <= 0` at any point after month 0

#### Outputs
1. Headline success % — green ≥ 80%, amber 60–80%, red < 60%
2. Fan chart — 10/25/50/75/90th percentile bands; accumulation / retirement phase shading; dashed retirement-age vline
3. Terminal value histogram — 80 bins; red $0 ruin line; optional legacy floor line
4. Key stats table — 7 metrics including median peak and prob-of-doubling
5. Sensitivity tabs — retirement age / annual spending / annual contribution (each calls cached `run_simulation`)

#### Caching
- `@st.cache_data` on `run_simulation` — all inputs are keyword-only scalars, hash cleanly
- Sensitivity analysis calls the same cached function with overridden kwargs — instant after first load
- Seed stored in `st.session_state`; "🎲 New random seed" button calls `st.rerun()`

---

## App 2: Portfolio Optimizer ⏳ NEXT

**Source:** `apps/portfolio_optimizer/app.py`
**Deploy slug:** `gfg-portfolio-optimizer`
**Embed page:** `docs/portfolio-optimizer.html`

### Purpose
Mean-variance portfolio optimization (Markowitz) with an interactive efficient frontier, Sharpe ratio maximization, CVaR risk analysis, and optional rebalancing suggestions. Demonstrates quantitative finance depth to a practitioner audience.

### Asset universe and data input

- **Free-form ticker entry** (comma-separated, e.g. `AAPL, MSFT, BND, GLD`) via `yfinance`
- **Pre-built starter presets** offered as one-click buttons so the app is immediately usable:
  - *Asset Class ETFs*: `SPY, AGG, GLD, VNQ, EFA, TLT`
  - *US Sectors*: `XLK, XLF, XLE, XLV, XLI, XLY, XLP`
  - *Factor ETFs*: `VTV, VUG, MTUM, QUAL, USMV`
- Pull **adjusted close prices** only; compute log returns from those
- **Lookback period**: 1yr / 3yr / 5yr / 10yr selector, **default 5yr**
- Align all series to a common date range (inner join); warn if any ticker has < 1yr of overlapping history
- Resample daily prices to **monthly returns** before optimization — more stable covariance, less noise

### Return estimation

- **Default: historical mean returns** (annualised from monthly log returns)
- **GMV toggle**: "Minimize volatility only (ignore return estimates)" — skips expected returns entirely, maximises stability. Good alternative when historical means are noisy.
- Note in the UI that historical return estimates are noisy over short lookbacks — surfacing this is part of the value

### Covariance estimation

- **Ledoit-Wolf shrinkage** via `sklearn.covariance.LedoitWolf` — do NOT use raw sample covariance
- Raw sample covariance is rank-deficient or ill-conditioned with many assets and limited history; Ledoit-Wolf produces a well-conditioned matrix that stabilises optimisation results
- This is a deliberate demonstration of practitioner-grade methodology

### Optimisation

- **Solver:** `scipy.optimize.minimize` with `method='SLSQP'`
- **Constraints:** weights sum to 1; weights ≥ 0 (long-only by default)
- **Advanced options** (in expander):
  - Allow short selling (weights ≥ −0.20, or unconstrained)
  - Maximum single-position weight (e.g. 40% cap)
- **Three key optimisations to run:**
  1. Maximise Sharpe ratio (primary)
  2. Minimise volatility (Global Minimum Variance)
  3. Sweep target returns to trace the efficient frontier (~100 points)
- Run max-Sharpe from **multiple random starting points** (≥ 10) and take the best result — the objective is non-convex and sensitive to initialisation

### Efficient frontier construction

- **Random portfolio scatter**: 5,000 random weight vectors, plotted as (annualised vol, annualised return), colour-coded by Sharpe ratio using a gold-to-white colorscale
- **Parametric frontier curve**: traced by solving min-variance at each target return level — overlaid as a clean line on top of the scatter
- **Mark explicitly on the chart:**
  - 🟡 Max Sharpe portfolio
  - ⚪ Min Volatility portfolio
  - ◇ Equal-weight portfolio
  - ★ Current holdings (if user entered weights — see Rebalancing below)

### Risk measures

- **Primary axis:** annualised volatility (standard deviation of returns)
- **CVaR (Expected Shortfall)** at 95% confidence — historical simulation:
  - Sort monthly return series, average the worst 5% of months
  - Annualise: `CVaR_annual ≈ CVaR_monthly × √12`
  - Show for each individual asset and for the max-Sharpe portfolio vs. equal-weight
- **Maximum drawdown** from historical price series — most viscerally understandable risk metric for non-quants; show in the summary table

### Rebalancing (optional)

- Optional section: "Compare to current holdings"
- User inputs current weights for each ticker (number inputs that sum to 100%)
- Show a **delta table**: Current Weight | Optimal Weight | Δ
- No transaction cost modelling in v1

### Sidebar inputs

**Main (always visible):**
- Ticker input (text) + preset buttons
- Lookback period selector
- Risk-free rate (%, default 4.5%)
- GMV toggle

**Advanced expander:**
- Allow short selling (toggle)
- Max position size (slider, default 100%)
- Rebalancing section (optional current weights)

### Outputs / layout

Use `st.tabs` for the main content area:

1. **Efficient Frontier** — scatter + parametric curve + marked portfolios
2. **Optimal Weights** — horizontal bar chart for max-Sharpe portfolio; weights table
3. **Risk Analysis** — CVaR comparison table (each asset + optimised vs. equal-weight); max drawdown; vol comparison
4. **Correlations** — heatmap of asset return correlations (Plotly `go.Heatmap`)
5. **Historical Returns** — cumulative return line chart for all assets over the selected lookback

KPI metric cards above the tabs: Optimised Sharpe | Optimised Vol | Optimised Return | vs. Equal-Weight Sharpe

### Implementation notes

```python
# Key imports
import yfinance as yf
from sklearn.covariance import LedoitWolf
from scipy.optimize import minimize

# Data fetch — cache per ticker list + lookback
@st.cache_data(ttl=3600)
def fetch_prices(tickers: tuple[str, ...], years: int) -> pd.DataFrame: ...

# Covariance
lw = LedoitWolf().fit(monthly_returns)
cov_matrix = lw.covariance_   # annualise: × 12

# Sharpe maximisation — run from N random starts, take best
best = None
for _ in range(15):
    w0 = np.random.dirichlet(np.ones(n_assets))
    res = minimize(neg_sharpe, w0, constraints=..., bounds=...)
    if best is None or res.fun < best.fun:
        best = res
```

- If a ticker fails to fetch (delisted, typo), skip it and show a warning — don't crash
- Validate that the covariance matrix is positive-definite before optimising; fall back to diagonal if not
- All charts use the GFG navy/gold palette (same pattern as Monte Carlo app)
- `requirements.txt`: add `scikit-learn>=1.4.0` and `yfinance>=0.2.40`

---

## App 3: Macro Dashboard ⏳ AFTER PORTFOLIO OPTIMIZER

**Requires:** FRED API key — free at [fred.stlouisfed.org/docs/api/api_key.html](https://fred.stlouisfed.org/docs/api/api_key.html)
**Source:** `apps/macro_dashboard/app.py`
**Deploy slug:** `gfg-macro-dashboard`
**Embed page:** `docs/macro-dashboard.html`

### Purpose
Live US macroeconomic dashboard pulling key indicators from the FRED API. Tracks leading and coincident indicators — yield curve, unemployment, inflation, M2 — with a three-signal recession composite. Designed to be genuinely useful to a financial planner as a quick macro read.

### FRED series to pull

**Core (always fetched):**

| Series ID | Description | Display |
|-----------|-------------|---------|
| `T10Y2Y` | 10yr–2yr Treasury yield spread | Level; inversion < 0 = signal |
| `UNRATE` | Unemployment rate | Level |
| `CPIAUCSL` | CPI All Items | YoY % change |
| `SAHMREALTIME` | Sahm Rule real-time indicator | Level; ≥ 0.5 = signal |
| `USREC` | NBER recession indicator | Used only for chart shading — not displayed standalone |

**Secondary (fetched, shown by default, toggleable):**

| Series ID | Description | Display |
|-----------|-------------|---------|
| `CPILFESL` | Core CPI (ex food & energy) | YoY % change — paired with headline CPI |
| `M2SL` | M2 money supply | YoY % change |
| `PAYEMS` | Nonfarm payrolls | MoM change (thousands) |
| `UMCSENT` | UMich consumer sentiment | Level |

**Out of scope for v1:** GDP (quarterly, too infrequent), housing starts, industrial production.

### Recession signal composite

The headline feature — displayed prominently at the top of the Overview tab as a "signal panel."

Three signals, each shown as a coloured badge (green / amber / red) with current value and threshold:

1. **Yield Curve** — triggered when `T10Y2Y < 0` (current reading)
2. **Sahm Rule** — triggered when `SAHMREALTIME >= 0.5`
3. **Consumer Sentiment Momentum** — triggered when `UMCSENT` is more than 1 standard deviation below its own 12-month rolling mean

**Composite status** (large badge at top):
- 0 of 3 triggered → 🟢 **Low**
- 1 of 3 triggered → 🟡 **Elevated**
- 2–3 of 3 triggered → 🔴 **High**

Include a brief disclosure under the panel: yield curve has a 6–24 month lead time; Sahm Rule is nearly coincident; these signals are indicators, not forecasts.

### Dashboard layout

Use `st.tabs`:

1. **Overview** — signal panel + KPI metric cards for all key series (current value + delta vs. 1 year ago)
2. **Yield Curve** — T10Y2Y time series with recession shading; horizontal zero line; current value callout
3. **Labor Market** — unemployment rate + Sahm Rule indicator on dual axes; recession shading; payrolls MoM bar chart below
4. **Inflation** — headline CPI YoY + Core CPI YoY on same chart; reference line at 2% (Fed target)
5. **Money & Sentiment** — M2 YoY % change; consumer sentiment index

### Data handling

- **Fetch each series in its own `@st.cache_data(ttl=3600)` function** — individual failure doesn't break the rest of the dashboard
- Always fetch **full available history** from FRED; apply the lookback filter at display time (so changing the lookback doesn't trigger a new API call)
- **Resample all series to monthly** (`resample('ME').last()`) before display — daily series like `T10Y2Y` get their month-end observation
- **YoY % change**: `series.pct_change(12) * 100` after resampling to monthly — never display raw CPI or M2 levels
- **Validate each series** before charting: check it's non-empty and that the most recent observation is within the last 90 days; if stale, show a warning rather than a silent bad chart

### Recession shading (applied to all time-series charts)

```python
# Add NBER recession shading to any Plotly figure
def add_recession_shading(fig, usrec: pd.Series, date_range):
    recessions = usrec[usrec == 1]
    # Find contiguous recession periods and add vrect for each
    ...
```

### Lookback selector

Sidebar: 2yr / 5yr / 10yr / Max, **default 10yr** — enough history to show at least one full business cycle including the 2020 recession.

### API key handling

```python
# In app.py
import streamlit as st
from fredapi import Fred

try:
    fred = Fred(api_key=st.secrets["FRED_API_KEY"])
except Exception:
    st.error(
        "FRED API key not configured. "
        "Add `FRED_API_KEY = 'your_key'` to `.streamlit/secrets.toml` locally, "
        "or to Streamlit Cloud → Settings → Secrets."
    )
    st.stop()
```

Graceful failure — show a clear setup message rather than a traceback.

### Implementation notes

- `requirements.txt`: `fredapi>=0.5.2` (already in stub)
- All charts use GFG navy/gold palette + Plotly
- The `USREC` series lags by ~1–2 months (NBER dating is retrospective) — note this in the UI
- `T10Y2Y` is available on FRED as a pre-computed series (no need to compute from `GS10`/`GS2`)
- For the Sahm Rule, `SAHMREALTIME` is the real-time version (revised less frequently) — preferred over computing from scratch

---

## Git Commit History

```
a71fccb fix: make Monte Carlo embed fill full viewport
789429d feat: embed Monte Carlo app directly in gfg.finance
016120f feat: link Monte Carlo app on landing page
63ef4e7 chore: add CLAUDE.md project spec and docs/CNAME for gfg.finance
6f6885e feat(monte-carlo): implement full Monte Carlo Retirement Simulator
ed13b0c Create CNAME
3f46bc7 Initial project scaffold
```

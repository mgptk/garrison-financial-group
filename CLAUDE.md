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

### Purpose
Mean-variance portfolio optimization with interactive efficient frontier. Shows optimal asset allocation and risk/return trade-offs for a custom basket of stocks.

### Design decisions (to be finalized in next session)

#### Data
- **yfinance** to pull historical adjusted close prices for user-specified tickers
- Default lookback: 5 years of daily data, resampled to monthly returns
- Handle missing data / delistings gracefully

#### Optimization
- **Mean-variance (Markowitz)** — minimize portfolio variance for a target return, sweep across return targets to trace the efficient frontier
- **Scipy `minimize`** with constraints: weights sum to 1, weights ≥ 0 (long-only)
- Key portfolios to highlight: minimum variance, maximum Sharpe ratio, user's current allocation
- Optionally: Global Minimum Variance (no expected-return input needed — more robust)

#### Inputs (sidebar)
- Ticker list (text input, comma-separated, e.g. `AAPL, MSFT, BND, GLD`)
- Lookback period (1y / 3y / 5y / 10y)
- Risk-free rate assumption (for Sharpe ratio, default 4.5% — current T-bill yield)
- Optional: target return slider to show a specific point on the frontier

#### Outputs
1. **Efficient frontier chart** — scatter of frontier portfolios (risk vs. return), highlight min-var and max-Sharpe points; plot user's equal-weight allocation for comparison
2. **Max-Sharpe portfolio weights** — bar chart of optimal allocation
3. **Correlation heatmap** — asset correlation matrix
4. **Historical cumulative returns** — line chart comparing each asset
5. **Key stats table** — annualised return, vol, Sharpe for each asset and the optimal portfolio

#### Implementation notes
- Cache price data fetch with `@st.cache_data(ttl=3600)` — refresh once per hour
- Show a warning if fewer than 2 valid tickers are entered
- Plotly for all charts (consistent with Monte Carlo)
- Use `scipy.optimize.minimize` with `SLSQP` method
- For the frontier, generate ~100 points by sweeping the target return from min to max

---

## App 3: Macro Dashboard ⏳ AFTER PORTFOLIO OPTIMIZER

**Requires:** FRED API key (free at fred.stlouisfed.org/docs/api/api_key.html)

### Purpose
Live macroeconomic dashboard pulling key indicators from the FRED API. Shows yield curve, inflation, unemployment, and M2 — with a simple recession probability signal.

### Design decisions (to be finalized)

#### Data (FRED series IDs)
| Series | FRED ID | Notes |
|--------|---------|-------|
| 10Y Treasury yield | `GS10` | |
| 2Y Treasury yield | `GS2` | |
| Yield curve spread (10Y−2Y) | Computed | Inversion = recession signal |
| CPI YoY | `CPIAUCSL` | Compute % change |
| Core PCE YoY | `PCEPILFE` | Fed's preferred inflation measure |
| Unemployment rate | `UNRATE` | |
| M2 money supply | `M2SL` | |
| Fed Funds Rate | `FEDFUNDS` | |
| Real GDP growth | `A191RL1Q225SBEA` | Quarterly |

#### Inputs
- Date range selector (default: last 5 years)
- Recession shading toggle (NBER recessions via `USREC`)

#### Outputs
1. **Yield curve chart** — 10Y−2Y spread over time; shade negative regions red
2. **Inflation chart** — CPI and Core PCE on same axis
3. **Unemployment chart** — rate over time with recession shading
4. **Fed Funds vs. 10Y** — monetary policy context
5. **Recession probability indicator** — simple logistic model on yield curve inversion + unemployment change (or just show the inversion as the signal)

#### FRED API key handling
- Store as Streamlit secret: `FRED_API_KEY`
- In `app.py`: `fred_key = st.secrets["FRED_API_KEY"]`
- Add to Streamlit Cloud: Settings → Secrets → `FRED_API_KEY = "your_key"`
- Cache FRED calls with `@st.cache_data(ttl=3600)`

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

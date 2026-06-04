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
| Monte Carlo — implementation | ✅ Done |
| Monte Carlo — deployed | ✅ Live at gfg-monte-carlo.streamlit.app |
| Monte Carlo — embedded | ✅ Live at gfg.finance/monte-carlo.html |
| Portfolio Optimizer — implementation | ✅ Done |
| Portfolio Optimizer — deployed | ✅ Live at gfg-portfolio-optimizer.streamlit.app |
| Portfolio Optimizer — embedded | ✅ Live at gfg.finance/portfolio-optimizer.html |
| Macro Dashboard — implementation | ✅ Done |
| Macro Dashboard — deployed | ✅ Live at gfg-macro-dashboard.streamlit.app |
| Macro Dashboard — embedded | ✅ Live at gfg.finance/macro-dashboard.html |

**All three tools are live. The project is feature-complete for v1.**

---

## Repo Structure

```
garrison-financial-group/
├── CLAUDE.md                            ← This file
├── README.md
├── .gitignore                           ← Python + Streamlit tuned
├── .venv/                               ← Local virtualenv (not committed)
├── docs/                                ← GitHub Pages root → gfg.finance
│   ├── index.html                       ← Landing page with tool cards
│   ├── monte-carlo.html                 ← ✅ Embed wrapper
│   ├── portfolio-optimizer.html         ← ✅ Embed wrapper
│   ├── macro-dashboard.html             ← ✅ Embed wrapper
│   ├── CNAME                            ← "gfg.finance"
│   ├── css/style.css                    ← Navy + gold design system
│   └── js/main.js                       ← Scroll animations
└── apps/
    ├── monte_carlo/                     ← ✅ Built & deployed
    │   ├── app.py
    │   └── requirements.txt
    ├── portfolio_optimizer/             ← ✅ Built & deployed
    │   ├── app.py
    │   └── requirements.txt
    └── macro_dashboard/                 ← ✅ Built & deployed
        ├── app.py
        └── requirements.txt
```

---

## Tech Stack

- **Python 3.11+**
- **Streamlit ≥ 1.35** — app framework
- **NumPy / SciPy** — simulation and optimisation
- **Pandas ≥ 2.2** — data handling (`"ME"` resample alias required)
- **Plotly ≥ 5.22** — all charts (interactive, consistent across apps)
- **scikit-learn ≥ 1.4** — Ledoit-Wolf covariance (Portfolio Optimizer)
- **yfinance ≥ 1.4** — price data (Portfolio Optimizer)
- **fredapi ≥ 0.5.2** — FRED economic data (Macro Dashboard)

---

## Deployment Architecture

| Layer | Tool | Status |
|-------|------|--------|
| Landing page | GitHub Pages (`/docs`, `main` branch) | ✅ Live at gfg.finance |
| Custom domain | gfg.finance via Cloudflare Registrar | ✅ Live |
| DNS | Cloudflare (4 A records → GitHub IPs, CNAME www) | ✅ Configured |
| Monte Carlo | Streamlit Community Cloud | ✅ gfg-monte-carlo.streamlit.app |
| Portfolio Optimizer | Streamlit Community Cloud | ✅ gfg-portfolio-optimizer.streamlit.app |
| Macro Dashboard | Streamlit Community Cloud | ✅ gfg-macro-dashboard.streamlit.app |

**GitHub Pages DNS records:**
- A records on `@`: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
- CNAME on `www`: `mgptk.github.io`
- Cloudflare proxy: **DNS only** (grey cloud) — required for GitHub Pages HTTPS

### Deploying a new app (established pattern)

1. Build `apps/<name>/app.py` and `apps/<name>/requirements.txt`
2. Push to `main`
3. Go to [share.streamlit.io](https://share.streamlit.io) → New app → repo `mgptk/garrison-financial-group`, branch `main`, path `apps/<name>/app.py`
4. Set a clean URL slug (e.g. `gfg-<name>`)
5. Add any secrets (e.g. `FRED_API_KEY`) in Streamlit Cloud → Settings → Secrets
6. Create `docs/<name>.html` — embedded wrapper page (see pattern below)
7. Update the tool card `<a href="#">` in `docs/index.html` to point to `/<name>.html`
8. Push — GitHub Pages updates in ~60 seconds

### Embed pattern (IMPORTANT — use this exactly)

Each app gets a wrapper page at `docs/<name>.html`. The iframe height **must be set in JS** — the browser's default iframe fallback is 300×150px and will appear if CSS-only sizing fails.

```html
<!-- In <head> -->
<style>
  html, body { height: 100%; margin: 0; overflow: hidden; }
  #app-frame  { display: block; width: 100%; border: none; }
</style>

<!-- Body -->
<nav class="navbar" id="hdr-nav">…</nav>
<div class="app-bar"  id="hdr-bar">…</div>
<iframe id="app-frame"
  src="https://<slug>.streamlit.app/?embed=true"
  allow="clipboard-write">
</iframe>

<!-- JS -->
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

`?embed=true` strips Streamlit's toolbar and footer for clean embedding.

---

## Landing Page (docs/)

Custom hand-coded HTML/CSS — **not** a site builder. Navy + gold colour scheme.

**To add a new app:** copy an existing `docs/<name>.html`, swap title / icon emoji / Streamlit src URL, then update the matching tool card in `docs/index.html` to link to `/<name>.html` (no `target="_blank"`).

**Colour palette (CSS variables in style.css):**
```css
--navy:       #0d1b2a
--navy-mid:   #1b2e45
--navy-light: #243b55
--gold:       #c9a84c
--gold-light: #e0c068
--text-muted: #8a9bb0
```

**App-bar chrome** (`.app-bar`, `.app-bar-inner`, `.app-bar-back`, `.app-bar-title`, `.app-bar-external`) lives in `docs/css/style.css`. The loading overlay and iframe sizing live in each page's own `<style>` block.

---

## Running Apps Locally

```bash
# Activate venv (Windows)
.venv\Scripts\activate

# Install deps for the app you're working on
pip install -r apps/monte_carlo/requirements.txt

# Run (hot-reloads on save)
streamlit run apps/monte_carlo/app.py
```

For the Macro Dashboard locally, create `.streamlit/secrets.toml`:
```toml
FRED_API_KEY = "your_key_here"
```

---

## Known Plotly Gotchas

These bugs were hit during development — record them to avoid repeating.

### 1. `titlefont` → `title_font` in colorbars (Plotly 5.x)
Plotly 5 renamed `titlefont` to `title_font` (snake_case) inside `colorbar=dict(...)`.
The old name silently fails or raises a TypeError. Use:
```python
colorbar=dict(title="Sharpe", tickfont=dict(size=10), title_font=dict(size=11))
```

### 2. Duplicate `yaxis` kwarg when using `**_CHART_BASE`
If `_CHART_BASE` contains a `yaxis` key **and** the `update_layout()` call also passes `yaxis=dict(...)` explicitly, Python raises `TypeError: got multiple values for keyword argument 'yaxis'`.

**Fix:** Keep `_CHART_BASE` free of `xaxis` / `yaxis`. Pass axis styles explicitly per chart:
```python
_CHART_BASE = dict(paper_bgcolor=NAVY, plot_bgcolor=NAVY_MID, ...)  # no xaxis/yaxis

fig.update_layout(
    **_CHART_BASE,
    xaxis=dict(gridcolor=NAVY_LIGHT, title="Date"),
    yaxis=dict(gridcolor=NAVY_LIGHT, title="Value"),
)
```
Or use the dotted shorthand for individual properties (`yaxis_ticksuffix="%"`) which never conflicts.

---

## App 1: Monte Carlo Retirement Simulator ✅ COMPLETE

**Live URL:** https://gfg-monte-carlo.streamlit.app/
**Embedded at:** https://gfg.finance/monte-carlo.html
**Source:** `apps/monte_carlo/app.py`
**Requirements:** `streamlit`, `numpy`, `pandas`, `plotly`, `scipy`

### What was built

A fully vectorised 5,000-path Monte Carlo retirement simulator with log-normal returns, Cholesky-correlated stock/bond draws, and all outputs in real (inflation-adjusted) terms. Fan chart, terminal histogram, key stats table, and 3-tab sensitivity analysis.

### Key implementation decisions

- **Time step:** Monthly (`annual ÷ 12` for mean, `÷ √12` for vol)
- **Log-normal drift:** `μ = log(1+m) − 0.5σ²` ensures `E[1+r] = 1 + monthly_mean`
- **Correlation:** Cholesky decomposition on 2×2 stock/bond covariance (ρ = −0.15)
- **Real terms throughout:** `real_return = (1 + nominal) / (1 + inflation) − 1`
- **Success rate:** `final_balance > 0` (strictly — values are floored at $0, so `>= 0` is always 100%)
- **Ruin rate:** `min(portfolio[:, 1:]) <= 0` at any point after month 0
- **Caching:** `@st.cache_data` on `run_simulation` with keyword-only scalar inputs; sensitivity analysis reuses same cached function with overridden kwargs
- **Seed:** stored in `st.session_state`; "🎲 New random seed" button calls `st.rerun()`
- **Performance:** ~160 ms for 5,000 paths × 660 months (NumPy vectorised)

---

## App 2: Portfolio Optimizer ✅ COMPLETE

**Live URL:** https://gfg-portfolio-optimizer.streamlit.app/
**Embedded at:** https://gfg.finance/portfolio-optimizer.html
**Source:** `apps/portfolio_optimizer/app.py`
**Requirements:** `streamlit`, `numpy`, `pandas`, `plotly`, `scipy`, `yfinance`, `scikit-learn`

### What was built

Markowitz mean-variance optimisation with Ledoit-Wolf shrinkage covariance, interactive efficient frontier, max-Sharpe and GMV portfolios, CVaR risk analysis, correlation heatmap, and in-sample historical return comparison.

### Key implementation decisions

- **Data:** `yf.Ticker(t).history(auto_adjust=True)` per ticker (individual downloads — more reliable than batch); index is `America/New_York` tz-aware → strip with `.tz_convert(None)`
- **Returns:** Daily prices → monthly log returns via `resample("ME").last()` (pandas 2.2+ alias)
- **Covariance:** `sklearn.covariance.LedoitWolf` — well-conditioned even when assets > months; annualised `× 12`
- **Optimisation:** `scipy.optimize.minimize` with `method="SLSQP"`; max-Sharpe run from 20 Dirichlet random starts (objective is non-convex); GMV from single start
- **Frontier:** 80 min-variance solves sweeping GMV return → max individual return
- **Random scatter:** 3,000 Dirichlet weight vectors coloured by Sharpe (Viridis scale)
- **CVaR:** Historical monthly 95% — average loss in worst 5% of months (reported as monthly %, not annualised)
- **`_CHART_BASE`:** Excludes `xaxis`/`yaxis` — axis styles passed explicitly per chart (avoids duplicate-kwarg error)
- **Preset buttons:** One-click presets fill `st.session_state["tickers_text"]` and call `st.rerun()`

### Bugs fixed post-deploy
- `titlefont` → `title_font` in Viridis colorbar (Plotly 5.x rename)
- `yaxis=dict(...)` in `fig_h.update_layout(**_CHART_BASE, yaxis=...)` → changed to `yaxis_ticksuffix="%"`

---

## App 3: Macro Dashboard ✅ COMPLETE

**Live URL:** https://gfg-macro-dashboard.streamlit.app/
**Embedded at:** https://gfg.finance/macro-dashboard.html
**Source:** `apps/macro_dashboard/app.py`
**Requirements:** `streamlit`, `numpy`, `pandas`, `plotly`, `fredapi`
**Secret required:** `FRED_API_KEY` (Streamlit Cloud → Settings → Secrets)

### What was built

Live US macroeconomic dashboard pulling 9 FRED series with a three-signal recession composite, NBER recession shading on all charts, and 5 content tabs.

### FRED series used

| Series ID | Description | Transform |
|-----------|-------------|-----------|
| `T10Y2Y` | 10Y−2Y Treasury spread | Level (monthly last) |
| `UNRATE` | Unemployment rate | Level |
| `CPIAUCSL` | CPI All Items | YoY % change |
| `CPILFESL` | Core CPI (ex food & energy) | YoY % change |
| `SAHMREALTIME` | Sahm Rule real-time | Level |
| `USREC` | NBER recession indicator | Recession shading only |
| `M2SL` | M2 money supply | YoY % change |
| `PAYEMS` | Nonfarm payrolls | MoM change (thousands) |
| `UMCSENT` | UMich consumer sentiment | Level + rolling mean/std |

### Key implementation decisions

- **Isolation:** One `@st.cache_data(ttl=3600)` function per series — a single bad fetch doesn't break the rest; failed series return `None` with a sidebar warning
- **Lookback strategy:** Full history always fetched; `_cut(series, cutoff)` applied at render time — changing the lookback selector is instant with no new API calls
- **Monthly resample:** `resample("ME").last()` — daily series like `T10Y2Y` get month-end observation
- **YoY:** `series.pct_change(12) * 100` on monthly series — never display raw CPI or M2 levels
- **Freshness validation:** `(pd.Timestamp.now() − series.index[-1]).days <= 90` — warn on stale data
- **Recession shading:** `add_recession_shading(fig, usrec, cutoff)` finds 0→1 and 1→0 edges in `USREC`, adds `vrect` for each contiguous period; handles ongoing recession at series end
- **Signal 3 (sentiment):** Triggered when `UMCSENT < rolling_12m_mean − 1×rolling_12m_std`; the rolling stats use full history so the threshold is meaningful
- **`_CHART_BASE`:** Excludes `xaxis`/`yaxis` from the start — no duplicate-kwarg risk
- **Dual-axis chart:** `make_subplots(specs=[[{"secondary_y": True}]])` for UNRATE + Sahm; layout applied with individual `.update_yaxes()` calls instead of `**_CHART_BASE`

### Recession composite logic

```python
# Signal 1: yield curve inversion
yc_triggered = T10Y2Y_current < 0

# Signal 2: Sahm Rule
sahm_triggered = SAHMREALTIME_current >= 0.5

# Signal 3: consumer sentiment momentum
sent_lower = UMCSENT.rolling(12).mean() - UMCSENT.rolling(12).std()
sent_triggered = UMCSENT_current < sent_lower_current

# Composite
n = sum([yc_triggered, sahm_triggered, sent_triggered])
# 0 → 🟢 Low  |  1 → 🟡 Elevated  |  2–3 → 🔴 High
```

---

## Git Commit History

```
0fd89b5 feat: add Macro Dashboard embed page and landing card link
5006ba6 feat(macro-dashboard): implement full Macro Dashboard
a3a64a6 fix: replace yaxis=dict() with yaxis_ticksuffix in Historical Returns tab
2d329d3 fix: rename titlefont -> title_font in colorbar (Plotly 5.x)
246202d feat: add Portfolio Optimizer embed page and landing card link
84091f6 feat(portfolio-optimizer): implement full Portfolio Optimizer
509b17a docs: update CLAUDE.md with full project context for Cowork handoff
a71fccb fix: make Monte Carlo embed fill full viewport
789429d feat: embed Monte Carlo app directly in gfg.finance
016120f feat: link Monte Carlo app on landing page
63ef4e7 chore: add CLAUDE.md project spec and docs/CNAME for gfg.finance
6f6885e feat(monte-carlo): implement full Monte Carlo Retirement Simulator
ed13b0c Create CNAME
3f46bc7 Initial project scaffold
```
